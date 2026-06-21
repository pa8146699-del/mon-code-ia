#!/usr/bin/env python3
"""NetScan — scanner de réseau / ports (interface tactile Kivy).

Outil **100 % autonome** (bibliothèque standard : socket, threading) : il ne
réutilise aucun autre module du dépôt, donc rien n'est copié au build. Il fait
un scan « TCP connect » (comme `nmap -sT`), qui ne nécessite **pas** les
privilèges root — il fonctionne donc dans une appli Android classique.

Deux modes :
    - 🌐 Scanner le réseau : teste les 254 hôtes d'un /24 (ex: 192.168.1.0/24)
      et liste ceux qui ont des ports courants ouverts.
    - 🎯 Scanner un hôte  : teste tous les ports courants d'une IP précise.

Le scan tourne sur un thread de fond ; l'interface est mise à jour via
Clock.schedule_once (jamais depuis le thread directement).

Pour tester l'interface sur ordinateur :
    pip install kivy
    python main.py

⚖️ À n'utiliser que sur des réseaux et des machines qui t'appartiennent ou que
tu es explicitement autorisé à tester. Scanner autrui sans accord est illégal.
"""

import socket
import threading
from concurrent.futures import ThreadPoolExecutor

from kivy.app import App
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput

# Ports courants -> nom du service (pour un rapport lisible).
COMMON_PORTS = {
    21: "ftp", 22: "ssh", 23: "telnet", 25: "smtp", 53: "dns",
    80: "http", 110: "pop3", 139: "netbios", 143: "imap", 443: "https",
    445: "smb", 3306: "mysql", 3389: "rdp", 5900: "vnc", 8080: "http-alt",
}
PORTS = sorted(COMMON_PORTS)
TIMEOUT = 0.5  # secondes max par port


def _esc(text) -> str:
    """Échappe les métacaractères du markup Kivy ([, ], &)."""
    return str(text).replace("&", "&amp;").replace("[", "&bl;").replace("]", "&br;")


def local_subnet() -> str:
    """Devine le préfixe /24 du réseau local (ex: '192.168.1'). '' si introuvable."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(1)
        s.connect(("8.8.8.8", 80))  # n'envoie rien : sert juste à trouver l'IP locale
        ip = s.getsockname()[0]
        s.close()
        return ip.rsplit(".", 1)[0]
    except OSError:
        return ""


def port_open(ip: str, port: int) -> bool:
    """True si une connexion TCP vers ip:port réussit."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(TIMEOUT)
    ouvert = (s.connect_ex((ip, port)) == 0)
    s.close()
    return ouvert


def scan_host_ports(ip: str) -> list:
    """Renvoie la liste des ports courants ouverts d'un hôte."""
    return [p for p in PORTS if port_open(ip, p)]


class NetScanLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", padding=12, spacing=10, **kwargs)
        self._scanning = False

        self.add_widget(
            Label(
                text="[b]📡 NetScan[/b]  —  scanner reseau",
                markup=True,
                font_size="24sp",
                size_hint_y=None,
                height="50dp",
            )
        )
        self.add_widget(
            Label(
                text="Reseau (prefixe /24) ou IP d'un hote :",
                size_hint_y=None,
                height="28dp",
            )
        )

        self.input = TextInput(
            text=local_subnet(),
            multiline=False,
            hint_text="ex: 192.168.1   ou   192.168.1.10",
            size_hint_y=None,
            height="44dp",
        )
        self.add_widget(self.input)

        btns = GridLayout(cols=2, size_hint_y=None, height="56dp", spacing=8)
        b1 = Button(text="🌐 Scanner le reseau", background_color=(0.20, 0.50, 0.80, 1))
        b1.bind(on_release=self.on_scan_network)
        b2 = Button(text="🎯 Scanner un hote", background_color=(0.80, 0.40, 0.10, 1))
        b2.bind(on_release=self.on_scan_host)
        btns.add_widget(b1)
        btns.add_widget(b2)
        self.buttons = [b1, b2]
        self.add_widget(btns)

        scroll = ScrollView()
        self.result = Label(
            text="Entre un reseau (ex: 192.168.1) et lance un scan.",
            markup=True,
            size_hint_y=None,
            halign="left",
            valign="top",
            padding=(8, 8),
        )
        self.result.bind(
            width=lambda *_: setattr(self.result, "text_size", (self.result.width, None)),
            texture_size=lambda *_: setattr(self.result, "height", self.result.texture_size[1]),
        )
        scroll.add_widget(self.result)
        self.add_widget(scroll)

    # --- helpers UI (toujours appelés sur le thread principal) ---
    def _append(self, line: str):
        self.result.text += "\n" + line

    def _enable(self, on: bool):
        for b in self.buttons:
            b.disabled = not on

    def _fmt(self, ip: str, ports: list) -> str:
        svc = ", ".join(f"{p}/{COMMON_PORTS.get(p, '?')}" for p in ports)
        return f"[color=2ecc71]●[/color] [b]{_esc(ip)}[/b]  ->  {_esc(svc)}"

    # --- scan réseau (/24) ---
    def on_scan_network(self, *_):
        if self._scanning:
            return
        base = self.input.text.strip()
        parts = base.split(".")
        if len(parts) == 4:  # IP complète tapée -> on garde le préfixe /24
            base = ".".join(parts[:3])
        if base.count(".") != 2:
            self.result.text = "[color=e74c3c]Prefixe invalide. Exemple : 192.168.1[/color]"
            return
        self._scanning = True
        self._enable(False)
        self.result.text = f"[b]Scan de {_esc(base)}.0/24 ...[/b]\n(patiente, ~30 s)"
        threading.Thread(target=self._run_network, args=(base,), daemon=True).start()

    def _run_network(self, base: str):
        found = []

        def worker(i):
            ip = f"{base}.{i}"
            ports = scan_host_ports(ip)
            if ports:
                found.append(ip)
                Clock.schedule_once(lambda dt, p=ports, a=ip: self._append(self._fmt(a, p)))

        with ThreadPoolExecutor(max_workers=100) as ex:
            ex.map(worker, range(1, 255))
        Clock.schedule_once(lambda dt: self._finish(len(found)))

    def _finish(self, n: int):
        self._scanning = False
        self._enable(True)
        if n == 0:
            self._append("\n[color=e67e22]Aucun hote avec port ouvert trouve.[/color]")
        else:
            self._append(f"\n[b]Termine : {n} hote(s) actif(s).[/b]")

    # --- scan d'un seul hôte ---
    def on_scan_host(self, *_):
        if self._scanning:
            return
        ip = self.input.text.strip()
        if ip.count(".") != 3:
            self.result.text = "[color=e74c3c]Entre une IP complete. Exemple : 192.168.1.10[/color]"
            return
        self._scanning = True
        self._enable(False)
        self.result.text = f"[b]Scan des ports de {_esc(ip)} ...[/b]"
        threading.Thread(target=self._run_host, args=(ip,), daemon=True).start()

    def _run_host(self, ip: str):
        ports = scan_host_ports(ip)

        def done(dt):
            self._scanning = False
            self._enable(True)
            if ports:
                lignes = [f"[b]{_esc(ip)} — ports ouverts :[/b]\n"]
                lignes += [
                    f"[color=2ecc71]●[/color] {p}/{COMMON_PORTS.get(p, '?')}" for p in ports
                ]
                self.result.text = "\n".join(lignes)
            else:
                self.result.text = f"[color=e67e22]{_esc(ip)} : aucun port courant ouvert.[/color]"

        Clock.schedule_once(done)


class NetScanApp(App):
    def build(self):
        self.title = "NetScan"
        return NetScanLayout()


if __name__ == "__main__":
    NetScanApp().run()

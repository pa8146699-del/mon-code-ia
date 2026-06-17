#!/usr/bin/env python3
"""DataGuard Mobile v1.2 — interface tactile Kivy pour Android.

Pour tester l'interface sur ordinateur :
    pip install kivy
    cp ../dataguard/detectors.py ../dataguard/phishing.py .
    python main.py
"""

import os
import re
from datetime import datetime

import detectors
import phishing

from kivy.app import App
from kivy.graphics import Color, Rectangle
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget

try:
    from android.permissions import Permission, request_permissions
    _ANDROID = True
except ImportError:
    _ANDROID = False

MAX_HISTORY = 30
_MARKUP_RE = re.compile(r'\[/?(?:b|i|color[^\]]*)\]')


# --- Logique -----------------------------------------------------------------

def _scan_text(text: str) -> tuple[str, int]:
    findings: list[detectors.Finding] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        findings.extend(detectors.scan_line(line, line_no, "(texte)"))

    if not findings:
        return "[color=2ecc71]Aucune donnee sensible detectee.[/color]", 0

    findings = detectors.sort_findings(findings)
    _colors = {
        detectors.SEVERITY_HIGH: "e74c3c",
        detectors.SEVERITY_MEDIUM: "e67e22",
        detectors.SEVERITY_LOW: "3498db",
    }
    lines = [f"[b]{len(findings)} fuite(s) detectee(s) :[/b]\n"]
    for f in findings:
        c = _colors.get(f.severity, "95a5a6")
        lines.append(
            f"[color={c}][{f.severity}][/color] {f.type}\n"
            f"    ligne {f.line}  ->  {f.excerpt}"
        )
    high = sum(1 for f in findings if f.severity == detectors.SEVERITY_HIGH)
    med = sum(1 for f in findings if f.severity == detectors.SEVERITY_MEDIUM)
    low = sum(1 for f in findings if f.severity == detectors.SEVERITY_LOW)
    score = min(100, high * 40 + med * 20 + low * 5)
    return "\n".join(lines), score


def _analyze_phishing(text: str) -> tuple[str, int]:
    score, signals = phishing.analyze(text)
    level = phishing.risk_level(score)
    level_color = {
        "ÉLEVÉ": "e74c3c",
        "MOYEN": "e67e22",
        "FAIBLE": "3498db",
        "AUCUN": "2ecc71",
    }.get(level, "95a5a6")
    lines = [
        f"[b]Risque : [color={level_color}]{level}[/color] "
        f"(score {score}/100)[/b]\n"
    ]
    if not signals:
        lines.append("[color=2ecc71]Aucun indice d'hameconnage releve.[/color]")
    for s in signals:
        lines.append(f"  [{s.category}] {s.detail}")
    return "\n".join(lines), score


# --- Widget barre de score ---------------------------------------------------

class ScoreBar(Widget):
    """Barre colorée 0-100 : vert → bleu → orange → rouge."""

    def __init__(self, **kwargs):
        super().__init__(size_hint_y=None, height="18dp", **kwargs)
        self._score = 0
        with self.canvas.before:
            self._bg_color = Color(0.13, 0.13, 0.13, 1)
            self._bg_rect = Rectangle(pos=self.pos, size=self.size)
            self._fill_color = Color(0.18, 0.8, 0.44, 1)
            self._fill_rect = Rectangle(pos=self.pos, size=(0, self.height))
        self.bind(pos=self._redraw, size=self._redraw)

    def set_score(self, score: int):
        self._score = max(0, min(100, score))
        if score >= 70:
            self._fill_color.rgba = (0.91, 0.3, 0.24, 1)
        elif score >= 40:
            self._fill_color.rgba = (0.9, 0.49, 0.13, 1)
        elif score > 0:
            self._fill_color.rgba = (0.2, 0.6, 0.86, 1)
        else:
            self._fill_color.rgba = (0.18, 0.8, 0.44, 1)
        self._redraw()

    def _redraw(self, *_):
        self._bg_rect.pos = self.pos
        self._bg_rect.size = self.size
        self._fill_rect.pos = self.pos
        self._fill_rect.size = (self.width * self._score / 100, self.height)


# --- Helpers UI --------------------------------------------------------------

def _make_result_label() -> Label:
    lbl = Label(
        text="Le resultat s'affichera ici.",
        markup=True,
        size_hint_y=None,
        halign="left",
        valign="top",
        padding=(8, 8),
    )
    lbl.bind(
        width=lambda *_: setattr(lbl, "text_size", (lbl.width, None)),
        texture_size=lambda *_: setattr(lbl, "height", lbl.texture_size[1]),
    )
    return lbl


def _open_file_picker(screen):
    """Ouvre un sélecteur de fichier et charge le contenu dans screen.input."""
    start_path = "/sdcard/" if os.path.isdir("/sdcard/") else os.path.expanduser("~")
    content = BoxLayout(orientation="vertical", spacing=6, padding=6)
    chooser = FileChooserListView(path=start_path, size_hint_y=1)
    btn_open = Button(
        text="Ouvrir ce fichier",
        size_hint_y=None,
        height="48dp",
        background_color=(0.2, 0.5, 0.8, 1),
    )
    content.add_widget(chooser)
    content.add_widget(btn_open)
    popup = Popup(title="Choisir un fichier", content=content, size_hint=(0.96, 0.92))

    def do_open(*_):
        if not chooser.selection:
            return
        popup.dismiss()
        path = chooser.selection[0]
        try:
            text = open(path, encoding="utf-8", errors="ignore").read(50_000)
        except OSError as e:
            screen.result.text = f"Erreur lecture : {e}"
            return
        screen.input.text = text
        screen.result.text = f"Fichier charge : {os.path.basename(path)}\nLance l'analyse."

    btn_open.bind(on_release=do_open)
    popup.open()


# --- Écran Scanner -----------------------------------------------------------

class ScannerScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        root = BoxLayout(orientation="vertical", padding=12, spacing=8)

        root.add_widget(Label(
            text="[b]Scanner les secrets[/b]",
            markup=True, font_size="20sp",
            size_hint_y=None, height="42dp",
        ))

        self.input = TextInput(
            hint_text="Colle du code, un fichier de config, un token...",
            size_hint_y=0.33,
        )
        root.add_widget(self.input)

        row = BoxLayout(size_hint_y=None, height="52dp", spacing=8)
        btn_scan = Button(text="Scanner", background_color=(0.2, 0.5, 0.8, 1))
        btn_scan.bind(on_release=self._do_scan)
        btn_clear = Button(text="Vider", size_hint_x=0.3, background_color=(0.3, 0.3, 0.3, 1))
        btn_clear.bind(on_release=self._do_clear)
        btn_file = Button(text="Fichier", size_hint_x=0.4, background_color=(0.2, 0.5, 0.3, 1))
        btn_file.bind(on_release=lambda *_: _open_file_picker(self))
        row.add_widget(btn_scan)
        row.add_widget(btn_clear)
        row.add_widget(btn_file)
        root.add_widget(row)

        self._score_bar = ScoreBar()
        root.add_widget(self._score_bar)
        self._score_lbl = Label(
            text="Score de risque : --",
            size_hint_y=None, height="20dp",
            font_size="12sp", color=(0.6, 0.6, 0.6, 1),
        )
        root.add_widget(self._score_lbl)

        sv = ScrollView()
        self.result = _make_result_label()
        sv.add_widget(self.result)
        root.add_widget(sv)

        self.add_widget(root)

    def _do_scan(self, *_):
        text = self.input.text.strip()
        if not text:
            self.result.text = "Colle d'abord du texte a analyser."
            return
        report, score = _scan_text(text)
        self.result.text = report
        self._score_bar.set_score(score)
        self._score_lbl.text = f"Score de risque : {score}/100"
        App.get_running_app().add_history("Secrets", report, score)

    def _do_clear(self, *_):
        self.input.text = ""
        self.result.text = "Le resultat s'affichera ici."
        self._score_bar.set_score(0)
        self._score_lbl.text = "Score de risque : --"


# --- Écran Phishing ----------------------------------------------------------

class PhishingScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        root = BoxLayout(orientation="vertical", padding=12, spacing=8)

        root.add_widget(Label(
            text="[b]Analyser phishing[/b]",
            markup=True, font_size="20sp",
            size_hint_y=None, height="42dp",
        ))

        self.input = TextInput(
            hint_text="Colle un e-mail, SMS ou message suspect...",
            size_hint_y=0.33,
        )
        root.add_widget(self.input)

        row = BoxLayout(size_hint_y=None, height="52dp", spacing=8)
        btn_analyze = Button(text="Analyser", background_color=(0.8, 0.4, 0.1, 1))
        btn_analyze.bind(on_release=self._do_analyze)
        btn_clear = Button(text="Vider", size_hint_x=0.3, background_color=(0.3, 0.3, 0.3, 1))
        btn_clear.bind(on_release=self._do_clear)
        row.add_widget(btn_analyze)
        row.add_widget(btn_clear)
        root.add_widget(row)

        self._score_bar = ScoreBar()
        root.add_widget(self._score_bar)
        self._score_lbl = Label(
            text="Score de risque : --",
            size_hint_y=None, height="20dp",
            font_size="12sp", color=(0.6, 0.6, 0.6, 1),
        )
        root.add_widget(self._score_lbl)

        sv = ScrollView()
        self.result = _make_result_label()
        sv.add_widget(self.result)
        root.add_widget(sv)

        self.add_widget(root)

    def _do_analyze(self, *_):
        text = self.input.text.strip()
        if not text:
            self.result.text = "Colle d'abord du texte a analyser."
            return
        report, score = _analyze_phishing(text)
        self.result.text = report
        self._score_bar.set_score(score)
        self._score_lbl.text = f"Score de risque : {score}/100"
        App.get_running_app().add_history("Phishing", report, score)

    def _do_clear(self, *_):
        self.input.text = ""
        self.result.text = "Le resultat s'affichera ici."
        self._score_bar.set_score(0)
        self._score_lbl.text = "Score de risque : --"


# --- Écran Historique --------------------------------------------------------

class HistoriqueScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        root = BoxLayout(orientation="vertical", padding=12, spacing=8)

        header = BoxLayout(size_hint_y=None, height="42dp", spacing=8)
        header.add_widget(Label(
            text="[b]Historique[/b]",
            markup=True, font_size="20sp",
        ))
        btn_export = Button(
            text="Exporter .txt",
            size_hint_x=0.42,
            background_color=(0.45, 0.25, 0.6, 1),
        )
        btn_export.bind(on_release=self._do_export)
        btn_clear = Button(
            text="Effacer",
            size_hint_x=0.28,
            background_color=(0.5, 0.15, 0.15, 1),
        )
        btn_clear.bind(on_release=self._do_clear_history)
        header.add_widget(btn_export)
        header.add_widget(btn_clear)
        root.add_widget(header)

        self._entries_box = BoxLayout(
            orientation="vertical", spacing=6, size_hint_y=None
        )
        self._entries_box.bind(minimum_height=self._entries_box.setter("height"))
        sv = ScrollView()
        sv.add_widget(self._entries_box)
        root.add_widget(sv)

        self.add_widget(root)

    def on_enter(self, *_):
        self._refresh()

    def _refresh(self):
        self._entries_box.clear_widgets()
        history = App.get_running_app().history
        if not history:
            self._entries_box.add_widget(
                Label(
                    text="Aucune analyse pour l'instant.\nLance un scan ou une analyse phishing.",
                    size_hint_y=None, height="80dp",
                    halign="center",
                )
            )
            return
        for entry in reversed(history):
            color = (
                "e74c3c" if entry["score"] >= 70 else
                "e67e22" if entry["score"] >= 40 else
                "3498db" if entry["score"] > 0 else
                "2ecc71"
            )
            lbl = Label(
                text=(
                    f"[b]{entry['kind']}[/b]  "
                    f"[color={color}]{entry['score']}/100[/color]  "
                    f"[color=888888]{entry['time']}[/color]\n"
                    f"[color=aaaaaa]{entry['summary']}[/color]"
                ),
                markup=True,
                size_hint_y=None,
                height="58dp",
                halign="left",
                valign="middle",
            )
            lbl.bind(width=lambda w, *_: setattr(w, "text_size", (w.width, None)))
            self._entries_box.add_widget(lbl)

    def _do_clear_history(self, *_):
        App.get_running_app().history.clear()
        self._refresh()

    def _do_export(self, *_):
        history = App.get_running_app().history
        if not history:
            Popup(
                title="Export",
                content=Label(text="Aucune donnee a exporter.", halign="center"),
                size_hint=(0.8, 0.3),
            ).open()
            return

        lines = [
            f"=== DataGuard — Rapport ({datetime.now().strftime('%Y-%m-%d %H:%M')}) ===",
            "",
        ]
        for entry in history:
            plain = _MARKUP_RE.sub("", entry.get("full", entry["summary"]))
            lines += [
                f"[{entry['time']}] {entry['kind']} — score {entry['score']}/100",
                plain.strip(),
                "-" * 50,
                "",
            ]

        export_dir = "/sdcard/DataGuard" if os.path.isdir("/sdcard") else os.path.expanduser("~/DataGuard")
        try:
            os.makedirs(export_dir, exist_ok=True)
            filename = f"rapport_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            path = os.path.join(export_dir, filename)
            with open(path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
            msg = f"Rapport sauvegarde :\n{path}"
        except OSError as e:
            msg = f"Erreur export : {e}"

        Popup(
            title="Export",
            content=Label(text=msg, halign="center"),
            size_hint=(0.92, 0.38),
        ).open()


# --- Application principale --------------------------------------------------

class DataGuardApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.history: list[dict] = []
        self._tab_buttons: list[Button] = []
        self._sm: ScreenManager | None = None

    def build(self):
        self.title = "DataGuard"

        self._sm = ScreenManager()
        self._sm.add_widget(ScannerScreen(name="scanner"))
        self._sm.add_widget(PhishingScreen(name="phishing"))
        self._sm.add_widget(HistoriqueScreen(name="historique"))

        root = BoxLayout(orientation="vertical")
        root.add_widget(self._sm)

        # Barre de navigation en bas
        tab_bar = BoxLayout(size_hint_y=None, height="52dp", spacing=2)
        tabs = [
            ("scanner",    "Scanner",     (0.2, 0.5, 0.8, 1)),
            ("phishing",   "Phishing",    (0.8, 0.4, 0.1, 1)),
            ("historique", "Historique",  (0.45, 0.25, 0.6, 1)),
        ]
        for screen_name, label, color in tabs:
            btn = Button(text=label, background_color=color)
            btn.bind(on_release=lambda x, n=screen_name: self._go_to(n))
            self._tab_buttons.append(btn)
            tab_bar.add_widget(btn)

        root.add_widget(tab_bar)
        return root

    def _go_to(self, name: str):
        if self._sm:
            self._sm.current = name

    def on_start(self):
        if _ANDROID:
            request_permissions([
                Permission.READ_EXTERNAL_STORAGE,
                Permission.WRITE_EXTERNAL_STORAGE,
            ])

    def add_history(self, kind: str, report: str, score: int):
        plain = _MARKUP_RE.sub("", report).strip()
        summary = plain.splitlines()[0][:65] if plain else ""
        self.history.append({
            "kind": kind,
            "score": score,
            "time": datetime.now().strftime("%H:%M:%S"),
            "summary": summary,
            "full": plain,
        })
        if len(self.history) > MAX_HISTORY:
            self.history.pop(0)


if __name__ == "__main__":
    DataGuardApp().run()

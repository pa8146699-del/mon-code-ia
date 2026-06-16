#!/usr/bin/env python3
"""DataGuard Mobile — interface tactile Kivy pour Android.

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
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget

try:
    from android.permissions import Permission, request_permissions
    _ANDROID = True
except ImportError:
    _ANDROID = False


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


# --- Barre de score ----------------------------------------------------------

class ScoreBar(Widget):
    """Barre colorée 0-100 : vert (0) → bleu → orange → rouge (100)."""

    def __init__(self, **kwargs):
        super().__init__(size_hint_y=None, height="20dp", **kwargs)
        self._score = 0
        with self.canvas.before:
            self._bg_color = Color(0.15, 0.15, 0.15, 1)
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


# --- Interface principale ----------------------------------------------------

_MARKUP_RE = re.compile(r'\[/?(?:b|color[^\]]*)\]')


class DataGuardLayout(BoxLayout):
    MAX_HISTORY = 20

    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", padding=12, spacing=8, **kwargs)
        self._history: list[dict] = []

        self.add_widget(Label(
            text="[b]DataGuard[/b]",
            markup=True,
            font_size="26sp",
            size_hint_y=None,
            height="48dp",
        ))
        self.add_widget(Label(
            text="Colle un texte, un e-mail ou du code ci-dessous :",
            size_hint_y=None,
            height="26dp",
        ))

        self.input = TextInput(
            hint_text="Colle ici le contenu a verifier...",
            size_hint_y=0.30,
        )
        self.add_widget(self.input)

        # Boutons principaux
        row1 = BoxLayout(size_hint_y=None, height="52dp", spacing=8)
        btn_scan = Button(text="Scanner les secrets", background_color=(0.2, 0.5, 0.8, 1))
        btn_scan.bind(on_release=self.on_scan)
        btn_phish = Button(text="Analyser phishing", background_color=(0.8, 0.4, 0.1, 1))
        btn_phish.bind(on_release=self.on_phishing)
        row1.add_widget(btn_scan)
        row1.add_widget(btn_phish)
        self.add_widget(row1)

        # Boutons secondaires
        row2 = BoxLayout(size_hint_y=None, height="44dp", spacing=8)
        btn_clear = Button(text="Vider", background_color=(0.35, 0.35, 0.35, 1))
        btn_clear.bind(on_release=self._on_clear)
        btn_file = Button(text="Choisir fichier", background_color=(0.25, 0.55, 0.3, 1))
        btn_file.bind(on_release=self.on_pick_file)
        self._btn_hist = Button(text="Historique (0)", background_color=(0.45, 0.25, 0.6, 1))
        self._btn_hist.bind(on_release=self.on_history)
        row2.add_widget(btn_clear)
        row2.add_widget(btn_file)
        row2.add_widget(self._btn_hist)
        self.add_widget(row2)

        # Barre de score
        self._score_bar = ScoreBar()
        self.add_widget(self._score_bar)
        self._score_label = Label(
            text="Score de risque : --",
            size_hint_y=None,
            height="20dp",
            font_size="12sp",
            color=(0.65, 0.65, 0.65, 1),
        )
        self.add_widget(self._score_label)

        # Zone de résultat
        scroll = ScrollView()
        self.result = Label(
            text="Le resultat s'affichera ici.",
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

    # --- Actions -------------------------------------------------------------

    def _show_result(self, report: str, score: int, kind: str):
        self.result.text = report
        self._score_bar.set_score(score)
        self._score_label.text = f"Score de risque : {score}/100"
        self._add_history(kind, report, score)

    def on_scan(self, *_):
        text = self.input.text.strip()
        if not text:
            self.result.text = "Colle d'abord du texte a analyser."
            return
        report, score = _scan_text(text)
        self._show_result(report, score, "Secrets")

    def on_phishing(self, *_):
        text = self.input.text.strip()
        if not text:
            self.result.text = "Colle d'abord du texte a analyser."
            return
        report, score = _analyze_phishing(text)
        self._show_result(report, score, "Phishing")

    def _on_clear(self, *_):
        self.input.text = ""
        self.result.text = "Le resultat s'affichera ici."
        self._score_bar.set_score(0)
        self._score_label.text = "Score de risque : --"

    def on_pick_file(self, *_):
        start_path = "/sdcard/" if os.path.isdir("/sdcard/") else os.path.expanduser("~")
        content = BoxLayout(orientation="vertical", spacing=6, padding=6)
        chooser = FileChooserListView(path=start_path, size_hint_y=1)
        btn_open = Button(text="Ouvrir ce fichier", size_hint_y=None, height="48dp",
                          background_color=(0.2, 0.5, 0.8, 1))
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
                self.result.text = f"Erreur lecture : {e}"
                return
            self.input.text = text
            self.result.text = f"Fichier charge : {os.path.basename(path)}\nAppuie sur Scanner ou Analyser."

        btn_open.bind(on_release=do_open)
        popup.open()

    def on_history(self, *_):
        if not self._history:
            Popup(
                title="Historique",
                content=Label(text="Aucune analyse pour l'instant."),
                size_hint=(0.8, 0.4),
            ).open()
            return

        box = BoxLayout(orientation="vertical", spacing=4, padding=6, size_hint_y=None)
        box.bind(minimum_height=box.setter("height"))

        for entry in reversed(self._history):
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
                height="60dp",
                halign="left",
                valign="middle",
            )
            lbl.bind(width=lambda w, *_: setattr(w, "text_size", (w.width, None)))
            box.add_widget(lbl)

        sv = ScrollView()
        sv.add_widget(box)
        Popup(
            title=f"Historique ({len(self._history)} analyses)",
            content=sv,
            size_hint=(0.96, 0.88),
        ).open()

    # --- Historique interne --------------------------------------------------

    def _add_history(self, kind: str, report: str, score: int):
        plain = _MARKUP_RE.sub("", report).strip()
        summary = plain.splitlines()[0][:60] if plain else ""
        self._history.append({
            "kind": kind,
            "score": score,
            "time": datetime.now().strftime("%H:%M:%S"),
            "summary": summary,
        })
        if len(self._history) > self.MAX_HISTORY:
            self._history.pop(0)
        self._btn_hist.text = f"Historique ({len(self._history)})"


class DataGuardApp(App):
    def build(self):
        self.title = "DataGuard"
        return DataGuardLayout()

    def on_start(self):
        if _ANDROID:
            request_permissions([Permission.READ_EXTERNAL_STORAGE])


if __name__ == "__main__":
    DataGuardApp().run()

#!/usr/bin/env python3
"""DataGuard Mobile — interface tactile Kivy pour Android.

Réutilise la logique de détection (detectors.py) et d'analyse anti-phishing
(phishing.py) du projet. Ces deux modules sont copiés à côté de ce fichier
au moment du build (voir .github/workflows/build-apk.yml).

Pour tester l'interface sur ordinateur :
    pip install kivy
    cp ../dataguard/detectors.py ../dataguard/phishing.py .
    python main.py
"""

import detectors
import phishing

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput


def scan_text(text: str) -> str:
    """Scanne un texte collé et renvoie un rapport lisible."""
    findings: list[detectors.Finding] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        findings.extend(detectors.scan_line(line, line_no, "(texte)"))

    if not findings:
        return "[color=2ecc71]Aucune donnee sensible detectee.[/color]"

    findings = detectors.sort_findings(findings)
    colors = {
        detectors.SEVERITY_HIGH: "e74c3c",
        detectors.SEVERITY_MEDIUM: "e67e22",
        detectors.SEVERITY_LOW: "3498db",
    }
    lines = [f"[b]{len(findings)} fuite(s) detectee(s) :[/b]\n"]
    for f in findings:
        c = colors.get(f.severity, "95a5a6")
        lines.append(
            f"[color={c}][{f.severity}][/color] {f.type}\n"
            f"    ligne {f.line}  ->  {f.excerpt}"
        )
    return "\n".join(lines)


def analyze_phishing(text: str) -> str:
    """Analyse un texte et renvoie un rapport de risque d'hameconnage."""
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
        lines.append(f"• [{s.category}] {s.detail}")
    return "\n".join(lines)


class DataGuardLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", padding=12, spacing=10, **kwargs)

        self.add_widget(
            Label(
                text="[b]🛡️ DataGuard[/b]",
                markup=True,
                font_size="26sp",
                size_hint_y=None,
                height="50dp",
            )
        )
        self.add_widget(
            Label(
                text="Colle un texte, un e-mail ou du code ci-dessous :",
                size_hint_y=None,
                height="30dp",
            )
        )

        self.input = TextInput(
            hint_text="Colle ici le contenu à vérifier...",
            size_hint_y=0.4,
        )
        self.add_widget(self.input)

        buttons = BoxLayout(size_hint_y=None, height="56dp", spacing=10)
        scan_btn = Button(text="🔍 Scanner les secrets", background_color=(0.2, 0.5, 0.8, 1))
        scan_btn.bind(on_release=self.on_scan)
        phish_btn = Button(text="🎣 Analyser phishing", background_color=(0.8, 0.4, 0.1, 1))
        phish_btn.bind(on_release=self.on_phishing)
        buttons.add_widget(scan_btn)
        buttons.add_widget(phish_btn)
        self.add_widget(buttons)

        scroll = ScrollView()
        self.result = Label(
            text="Le résultat s'affichera ici.",
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

    def on_scan(self, *_):
        self.result.text = scan_text(self.input.text)

    def on_phishing(self, *_):
        self.result.text = analyze_phishing(self.input.text)


class DataGuardApp(App):
    def build(self):
        self.title = "DataGuard"
        return DataGuardLayout()


if __name__ == "__main__":
    DataGuardApp().run()

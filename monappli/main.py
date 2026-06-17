#!/usr/bin/env python3
"""MonAppli — ton appli de sécurité perso, interface tactile Kivy.

Réutilise la logique de détection (detectors.py) et d'analyse anti-phishing
(phishing.py) du dossier dataguard/. Ces deux modules sont copiés à côté de
ce fichier au moment du build (voir .github/workflows/build-monappli.yml).

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

# Couleurs partagées par tous les rapports (codes hexadécimaux Kivy markup).
SEVERITY_COLORS = {
    detectors.SEVERITY_HIGH: "e74c3c",
    detectors.SEVERITY_MEDIUM: "e67e22",
    detectors.SEVERITY_LOW: "3498db",
}
RISK_COLORS = {
    "ÉLEVÉ": "e74c3c",
    "MOYEN": "e67e22",
    "FAIBLE": "3498db",
    "AUCUN": "2ecc71",
}


def scan_text(text: str) -> str:
    """Scanne un texte collé et renvoie un rapport lisible (Kivy markup)."""
    findings: list[detectors.Finding] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        findings.extend(detectors.scan_line(line, line_no, "(texte)"))

    if not findings:
        return "[color=2ecc71]Aucune donnee sensible detectee.[/color]"

    findings = detectors.sort_findings(findings)
    lines = [f"[b]{len(findings)} fuite(s) detectee(s) :[/b]\n"]
    for f in findings:
        c = SEVERITY_COLORS.get(f.severity, "95a5a6")
        lines.append(
            f"[color={c}][{f.severity}][/color] {f.type}\n"
            f"    ligne {f.line}  ->  {f.excerpt}"
        )
    return "\n".join(lines)


def analyze_phishing(text: str) -> str:
    """Analyse un texte et renvoie un rapport de risque d'hameconnage."""
    score, signals = phishing.analyze(text)
    level = phishing.risk_level(score)
    c = RISK_COLORS.get(level, "95a5a6")

    lines = [f"[b]Risque : [color={c}]{level}[/color] (score {score}/100)[/b]\n"]
    if not signals:
        lines.append("[color=2ecc71]Aucun indice d'hameconnage releve.[/color]")
    for s in signals:
        lines.append(f"• [{s.category}] {s.detail}")
    return "\n".join(lines)


def analyze_all(text: str) -> str:
    """Lance les deux analyses (secrets + phishing) et combine les rapports."""
    return (
        "[b]== 🔍 Secrets ==[/b]\n"
        + scan_text(text)
        + "\n\n[b]== 🎣 Phishing ==[/b]\n"
        + analyze_phishing(text)
    )


class MonAppliLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", padding=12, spacing=10, **kwargs)

        self.add_widget(
            Label(
                text="[b]🔐 MonAppli[/b]",
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

        # Première rangée : les deux analyses séparées.
        row1 = BoxLayout(size_hint_y=None, height="56dp", spacing=10)
        scan_btn = Button(text="🔍 Scanner les secrets", background_color=(0.2, 0.5, 0.8, 1))
        scan_btn.bind(on_release=self.on_scan)
        phish_btn = Button(text="🎣 Analyser phishing", background_color=(0.8, 0.4, 0.1, 1))
        phish_btn.bind(on_release=self.on_phishing)
        row1.add_widget(scan_btn)
        row1.add_widget(phish_btn)
        self.add_widget(row1)

        # Deuxième rangée : le bouton tout-en-un, plus visible.
        all_btn = Button(
            text="✅ Tout analyser",
            size_hint_y=None,
            height="56dp",
            background_color=(0.15, 0.6, 0.35, 1),
        )
        all_btn.bind(on_release=self.on_all)
        self.add_widget(all_btn)

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

    def on_all(self, *_):
        self.result.text = analyze_all(self.input.text)


class MonAppliApp(App):
    def build(self):
        self.title = "MonAppli"
        return MonAppliLayout()


if __name__ == "__main__":
    MonAppliApp().run()

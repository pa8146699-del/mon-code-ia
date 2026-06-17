#!/usr/bin/env python3
"""MonAppli — ta boîte à outils cybersécurité perso (interface tactile Kivy).

Réutilise toute la logique du dossier dataguard/ :
    - detectors.py  → détection de secrets
    - phishing.py   → analyse anti-phishing
    - toolkit.py    → mots de passe (force + génération) et empreintes (hash)

Ces modules sont copiés à côté de ce fichier au moment du build
(voir .github/workflows/build-monappli.yml).

Pour tester l'interface sur ordinateur :
    pip install kivy
    cp ../dataguard/detectors.py ../dataguard/phishing.py ../dataguard/toolkit.py .
    python main.py
"""

import detectors
import phishing
import toolkit

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
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
PASSWORD_COLORS = {
    "TRÈS FAIBLE": "e74c3c",
    "FAIBLE": "e67e22",
    "MOYEN": "f1c40f",
    "FORT": "2ecc71",
    "TRÈS FORT": "27ae60",
}


def _esc(text: str) -> str:
    """Échappe les caractères spéciaux du markup Kivy ([, ], &)."""
    return text.replace("&", "&amp;").replace("[", "&bl;").replace("]", "&br;")


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
            f"    ligne {f.line}  ->  {_esc(f.excerpt)}"
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
        lines.append(f"• [{s.category}] {_esc(s.detail)}")
    return "\n".join(lines)


def analyze_all(text: str) -> str:
    """Lance les deux analyses (secrets + phishing) et combine les rapports."""
    return (
        "[b]== 🔍 Secrets ==[/b]\n"
        + scan_text(text)
        + "\n\n[b]== 🎣 Phishing ==[/b]\n"
        + analyze_phishing(text)
    )


def check_password(text: str) -> str:
    """Analyse le texte collé comme un mot de passe à tester."""
    pw = text.strip()
    if not pw:
        return "[color=e67e22]Colle d'abord un mot de passe dans la zone de texte.[/color]"

    r = toolkit.password_strength(pw)
    c = PASSWORD_COLORS.get(r.level, "95a5a6")
    lines = [
        f"[b]Force : [color={c}]{r.level}[/color] (score {r.score}/100)[/b]",
        f"Entropie estimee : ~{r.entropy_bits} bits\n",
    ]
    for issue in r.issues:
        lines.append(f"[color=e74c3c]⚠ {_esc(issue)}[/color]")
    for tip in r.tips:
        lines.append(f"[color=3498db]💡 {_esc(tip)}[/color]")
    if not r.issues and not r.tips:
        lines.append("[color=2ecc71]Excellent mot de passe ![/color]")
    return "\n".join(lines)


def make_password() -> str:
    """Génère un mot de passe sûr de 16 caractères et l'affiche."""
    pw = toolkit.generate_password(16, use_symbols=True)
    return (
        "[b]Mot de passe genere (16 caracteres) :[/b]\n\n"
        f"[color=2ecc71]{_esc(pw)}[/color]\n\n"
        "Range-le dans un gestionnaire de mots de passe."
    )


def hash_report(text: str) -> str:
    """Calcule et affiche les empreintes (hash) du texte collé."""
    if not text:
        return "[color=e67e22]Colle d'abord un texte a hacher.[/color]"
    h = toolkit.hash_text(text)
    lines = ["[b]Empreintes du texte :[/b]\n"]
    for algo, digest in h.items():
        lines.append(f"[b]{algo}[/b]\n[color=3498db]{digest}[/color]")
    return "\n".join(lines)


class MonAppliLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", padding=12, spacing=10, **kwargs)

        self.add_widget(
            Label(
                text="[b]🔐 MonAppli[/b]  —  boite a outils cyber",
                markup=True,
                font_size="24sp",
                size_hint_y=None,
                height="50dp",
            )
        )
        self.add_widget(
            Label(
                text="Colle un texte, un e-mail, du code ou un mot de passe :",
                size_hint_y=None,
                height="28dp",
            )
        )

        self.input = TextInput(
            hint_text="Colle ici le contenu à vérifier...",
            size_hint_y=0.32,
        )
        self.add_widget(self.input)

        # Grille des 6 outils (2 colonnes).
        tools = GridLayout(cols=2, size_hint_y=None, height="180dp", spacing=8)
        for label, handler, color in (
            ("🔍 Secrets", self.on_scan, (0.20, 0.50, 0.80, 1)),
            ("🎣 Phishing", self.on_phishing, (0.80, 0.40, 0.10, 1)),
            ("✅ Tout analyser", self.on_all, (0.15, 0.60, 0.35, 1)),
            ("🔑 Force mot de passe", self.on_password, (0.55, 0.35, 0.75, 1)),
            ("🎲 Générer mot de passe", self.on_generate, (0.30, 0.45, 0.55, 1)),
            ("#️⃣ Empreintes (hash)", self.on_hash, (0.40, 0.40, 0.45, 1)),
        ):
            btn = Button(text=label, background_color=color)
            btn.bind(on_release=handler)
            tools.add_widget(btn)
        self.add_widget(tools)

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

    def on_password(self, *_):
        self.result.text = check_password(self.input.text)

    def on_generate(self, *_):
        self.result.text = make_password()

    def on_hash(self, *_):
        self.result.text = hash_report(self.input.text)


class MonAppliApp(App):
    def build(self):
        self.title = "MonAppli"
        return MonAppliLayout()


if __name__ == "__main__":
    MonAppliApp().run()

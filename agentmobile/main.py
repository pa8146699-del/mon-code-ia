#!/usr/bin/env python3
"""AgentMobile — AgentOS sur ton téléphone (interface tactile Kivy).

Un chat où Claude AGIT sur une base SQLite locale (clients, projets, tâches,
finances, notes) — ta source unique de vérité, stockée sur l'appareil.

Réutilise la logique du dossier agentos/ :
    db.py, tools.py, notion_sync.py, llm.py
Ces modules sont copiés à côté de ce fichier au moment du build
(voir .github/workflows/build-agentmobile.yml). L'appel à l'API Claude passe
par urllib (llm.py) : aucune dépendance lourde, l'APK ne requiert que kivy.

Tout est gratuit hormis l'usage de l'API Claude (au token, pas d'abonnement) :
saisis ta clé ANTHROPIC dans le champ prévu.

Pour tester l'interface sur ordinateur :
    pip install kivy
    cp ../agentos/db.py ../agentos/tools.py ../agentos/notion_sync.py ../agentos/llm.py .
    python main.py
"""

import os
import threading

import db
import llm

from kivy.app import App
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput


def _esc(text: str) -> str:
    """Échappe les caractères spéciaux du markup Kivy ([, ], &)."""
    return text.replace("&", "&amp;").replace("[", "&bl;").replace("]", "&br;")


class AgentLayout(BoxLayout):
    def __init__(self, conn, **kwargs):
        super().__init__(orientation="vertical", padding=10, spacing=8, **kwargs)
        self.conn = conn
        self.history: list[dict] = []
        self.busy = False

        self.add_widget(Label(
            text="[b]🤖 AgentOS[/b]", markup=True,
            size_hint_y=None, height=44, font_size="22sp",
        ))

        # Le moteur (Groq gratuit par défaut, ou Claude) est choisi dans llm.py.
        if llm.PROVIDER == "groq":
            hint, env_var = "Clé API Groq (gratuite — console.groq.com)…", "GROQ_API_KEY"
        else:
            hint, env_var = "Clé API Claude (ANTHROPIC_API_KEY)…", "ANTHROPIC_API_KEY"
        self.key_input = TextInput(
            hint_text=hint, password=True, multiline=False,
            size_hint_y=None, height=44,
        )
        # Pré-remplie si la variable d'environnement existe (test PC).
        self.key_input.text = os.environ.get(env_var, "")
        self.add_widget(self.key_input)

        scroll = ScrollView()
        self.conversation = Label(
            text="[i]Dis-moi quoi enregistrer ou demande l'état de ta base.[/i]",
            markup=True, size_hint_y=None, halign="left", valign="top",
            padding=(6, 6),
        )
        self.conversation.bind(
            width=lambda *_: setattr(self.conversation, "text_size", (self.conversation.width, None)),
            texture_size=lambda *_: setattr(self.conversation, "height", self.conversation.texture_size[1]),
        )
        scroll.add_widget(self.conversation)
        self.add_widget(scroll)

        row = BoxLayout(orientation="horizontal", size_hint_y=None, height=52, spacing=6)
        self.message_input = TextInput(hint_text="Ton message…", multiline=False)
        self.message_input.bind(on_text_validate=lambda *_: self.send())
        send_btn = Button(text="Envoyer", size_hint_x=None, width=110,
                          background_color=(0.2, 0.5, 0.9, 1))
        send_btn.bind(on_press=lambda *_: self.send())
        row.add_widget(self.message_input)
        row.add_widget(send_btn)
        self.add_widget(row)

    def _append(self, line: str) -> None:
        self.conversation.text += "\n" + line

    def send(self) -> None:
        if self.busy:
            return
        message = self.message_input.text.strip()
        if not message:
            return
        key = self.key_input.text.strip()
        if not key:
            self._append("[color=e74c3c]⚠ Saisis d'abord ta clé API Claude.[/color]")
            return

        self.message_input.text = ""
        self._append(f"[b]Toi :[/b] {_esc(message)}")
        self.busy = True

        threading.Thread(target=self._run, args=(message, key), daemon=True).start()

    def _run(self, message: str, key: str) -> None:
        def on_tool(name, args):
            Clock.schedule_once(
                lambda *_: self._append(f"[color=888888][i]· {_esc(name)}[/i][/color]")
            )

        try:
            reply = llm.run_turn(self.conn, self.history, message, api_key=key, on_tool=on_tool)
        except Exception as e:  # remonte proprement à l'écran
            reply = f"Erreur : {e}"

        Clock.schedule_once(lambda *_: self._finish(reply))

    def _finish(self, reply: str) -> None:
        self._append(f"[b][color=2ecc71]AgentOS :[/color][/b] {_esc(reply)}")
        self.busy = False


class AgentMobileApp(App):
    def build(self):
        self.title = "AgentOS"
        # Base stockée dans le dossier privé de l'app (inscriptible sur Android).
        conn = db.connect(os.path.join(self.user_data_dir, "agentos.db"))
        return AgentLayout(conn)


if __name__ == "__main__":
    AgentMobileApp().run()

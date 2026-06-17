#!/usr/bin/env python3
"""AgentOS — assistant style Jarvis qui AGIT sur ta base de données.

À la différence de jarvis/ (qui ne fait que discuter), cet agent utilise le
« tool use » de Claude : il lit et écrit réellement dans la base SQLite
(clients, projets, tâches, finances, notes) — ta source unique de vérité.

    python agentos/agent.py            # mode texte (terminal)
    python agentos/agent.py --voice    # mode vocal (micro + synthèse)

Nécessite ANTHROPIC_API_KEY. La synchro Notion (optionnelle) s'active via les
variables NOTION_* (voir notion_sync.py).
"""

import os
import sys

import anthropic

import db
from tools import TOOLS, dispatch

VOICE_MODE = "--voice" in sys.argv

if VOICE_MODE:
    import pyttsx3
    import speech_recognition as sr

    _recognizer = sr.Recognizer()
    _engine = pyttsx3.init()

_client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
_conn = db.connect()
_history: list[dict] = []

SYSTEM = (
    "Tu es AgentOS, un assistant personnel qui gère un système centralisé "
    "(clients, projets, tâches, finances, notes) servant de source unique de "
    "vérité. Tu ne te contentes pas de discuter : tu utilises les outils mis à "
    "ta disposition pour LIRE et ÉCRIRE concrètement dans la base. Quand "
    "l'utilisateur te donne une information (une dépense, un prospect, une "
    "tâche…), enregistre-la avec le bon outil, puis confirme brièvement. "
    "Quand il pose une question, interroge la base avant de répondre. "
    "Réponds en français, de façon concise."
)


def listen() -> str:
    """Écoute le micro et retourne le texte reconnu."""
    with sr.Microphone() as source:
        print("En écoute...")
        _recognizer.adjust_for_ambient_noise(source, duration=0.5)
        audio = _recognizer.listen(source)
    try:
        text = _recognizer.recognize_google(audio, language="fr-FR")
        print(f"Vous : {text}")
        return text
    except sr.UnknownValueError:
        return ""
    except sr.RequestError as e:
        print(f"Erreur reconnaissance vocale : {e}")
        return ""


def read_input() -> str:
    """Lit une commande depuis le terminal."""
    try:
        return input("Vous : ").strip()
    except (EOFError, KeyboardInterrupt):
        return "quitter"


def speak(text: str) -> None:
    """Synthétise le texte en parole."""
    _engine.say(text)
    _engine.runAndWait()


def respond(user_message: str) -> str:
    """Boucle d'agent : Claude raisonne, appelle des outils, puis conclut."""
    _history.append({"role": "user", "content": user_message})

    while True:
        response = _client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=SYSTEM,
            tools=TOOLS,
            messages=_history,
        )
        _history.append({"role": "assistant", "content": response.content})

        if response.stop_reason != "tool_use":
            # Réponse finale : concatène les blocs texte.
            return "".join(b.text for b in response.content if b.type == "text")

        # Exécute chaque outil demandé et renvoie les résultats à Claude.
        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            print(f"  [outil] {block.name}({block.input})")
            output = dispatch(_conn, block.name, block.input)
            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": output,
                }
            )
        _history.append({"role": "user", "content": tool_results})


def main() -> None:
    print("AgentOS démarré. Tapez 'quitter' ou dites 'stop' pour arrêter.\n")

    get_input = listen if VOICE_MODE else read_input

    while True:
        user_input = get_input()

        if not user_input:
            continue

        if user_input.lower() in {"quitter", "stop", "exit", "quit"}:
            farewell = "Au revoir !"
            print(f"AgentOS : {farewell}")
            if VOICE_MODE:
                speak(farewell)
            break

        reply = respond(user_input)
        print(f"AgentOS : {reply}\n")

        if VOICE_MODE:
            speak(reply)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""AgentOS — assistant style Jarvis qui AGIT sur ta base de données.

À la différence de jarvis/ (qui ne fait que discuter), cet agent utilise le
« tool use » de Claude : il lit et écrit réellement dans la base SQLite
(clients, projets, tâches, finances, notes) — ta source unique de vérité.

    python agentos/agent.py            # mode texte (terminal)
    python agentos/agent.py --voice    # mode vocal (micro + synthèse)

Nécessite ANTHROPIC_API_KEY. Zéro dépendance externe en mode texte (l'appel
API passe par urllib via llm.py). La synchro Notion (optionnelle) s'active via
les variables NOTION_* (voir notion_sync.py).
"""

import sys

import db
import llm

VOICE_MODE = "--voice" in sys.argv

if VOICE_MODE:
    import pyttsx3
    import speech_recognition as sr

    _recognizer = sr.Recognizer()
    _engine = pyttsx3.init()

_conn = db.connect()
_history: list[dict] = []


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


def _log_tool(name: str, args: dict) -> None:
    print(f"  [outil] {name}({args})")


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

        reply = llm.run_turn(_conn, _history, user_input, on_tool=_log_tool)
        print(f"AgentOS : {reply}\n")

        if VOICE_MODE:
            speak(reply)


if __name__ == "__main__":
    main()

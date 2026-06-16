#!/usr/bin/env python3
"""Jarvis — assistant vocal/textuel propulsé par Claude."""

import os
import sys

import anthropic

VOICE_MODE = "--voice" in sys.argv

if VOICE_MODE:
    import pyttsx3
    import speech_recognition as sr

    _recognizer = sr.Recognizer()
    _engine = pyttsx3.init()

_client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
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


def respond(user_message: str) -> str:
    """Envoie le message à Claude et retourne la réponse."""
    _history.append({"role": "user", "content": user_message})

    response = _client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=(
            "Tu es Jarvis, un assistant personnel intelligent, concis et utile. "
            "Réponds en français sauf si l'utilisateur écrit dans une autre langue."
        ),
        messages=_history,
    )

    reply = response.content[0].text
    _history.append({"role": "assistant", "content": reply})
    return reply


def main() -> None:
    print("Jarvis démarré. Tapez 'quitter' ou dites 'stop' pour arrêter.\n")

    get_input = listen if VOICE_MODE else read_input

    while True:
        user_input = get_input()

        if not user_input:
            continue

        if user_input.lower() in {"quitter", "stop", "exit", "quit"}:
            farewell = "Au revoir !"
            print(f"Jarvis : {farewell}")
            if VOICE_MODE:
                speak(farewell)
            break

        reply = respond(user_input)
        print(f"Jarvis : {reply}\n")

        if VOICE_MODE:
            speak(reply)


if __name__ == "__main__":
    main()

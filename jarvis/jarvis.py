#!/usr/bin/env python3
"""Jarvis — assistant vocal/textuel local propulsé par Ollama (gratuit)."""

import sys
import ollama

VOICE_MODE = "--voice" in sys.argv
MODEL = "llama3.2"

if VOICE_MODE:
    import pyttsx3
    import speech_recognition as sr

    _recognizer = sr.Recognizer()
    _engine = pyttsx3.init()

_history: list[dict] = []

_SYSTEM = (
    "Tu es Jarvis, un assistant personnel intelligent, concis et utile. "
    "Réponds en français sauf si l'utilisateur écrit dans une autre langue."
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
    """Envoie le message au modèle local et retourne la réponse."""
    _history.append({"role": "user", "content": user_message})

    response = ollama.chat(
        model=MODEL,
        messages=[{"role": "system", "content": _SYSTEM}] + _history,
    )

    reply = response.message.content
    _history.append({"role": "assistant", "content": reply})
    return reply


def main() -> None:
    print(f"Jarvis démarré (modèle : {MODEL}). Tapez 'quitter' pour arrêter.\n")

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

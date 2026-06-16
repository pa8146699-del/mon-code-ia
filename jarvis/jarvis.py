#!/usr/bin/env python3
"""Jarvis — assistant textuel CLI (Groq, gratuit)."""

import os
import sys
from groq import Groq

_client = Groq(api_key=os.environ["GROQ_API_KEY"])
MODEL   = "llama-3.3-70b-versatile"
_SYSTEM = (
    "Tu es Jarvis, un assistant personnel intelligent, concis et utile. "
    "Réponds en français sauf si l'utilisateur écrit dans une autre langue."
)
_history: list[dict] = []


def read_input() -> str:
    try:
        return input("Vous : ").strip()
    except (EOFError, KeyboardInterrupt):
        return "quitter"


def respond(user_message: str) -> str:
    _history.append({"role": "user", "content": user_message})

    response = _client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "system", "content": _SYSTEM}] + _history,
        max_tokens=1024,
    )

    reply = response.choices[0].message.content
    _history.append({"role": "assistant", "content": reply})
    return reply


def main() -> None:
    print(f"Jarvis démarré (modèle : {MODEL}). Tapez 'quitter' pour arrêter.\n")

    while True:
        user_input = read_input()
        if not user_input:
            continue
        if user_input.lower() in {"quitter", "stop", "exit", "quit"}:
            print("Jarvis : Au revoir !")
            break
        print(f"Jarvis : {respond(user_input)}\n")


if __name__ == "__main__":
    main()

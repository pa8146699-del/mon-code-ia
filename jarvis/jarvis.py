#!/usr/bin/env python3
"""Jarvis — assistant textuel CLI (Ollama local, gratuit)."""

import ollama

MODEL   = "tinyllama"   # ~600 Mo — changer selon RAM dispo (voir CLAUDE.md)
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

    response = ollama.chat(
        model=MODEL,
        messages=[{"role": "system", "content": _SYSTEM}] + _history,
    )

    reply = response.message.content
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

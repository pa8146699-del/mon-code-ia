#!/usr/bin/env python3
"""Jarvis — interface web avec choix du backend : Ollama local ou Groq cloud."""

import json
import os
from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_from_directory
import ollama

app = Flask(__name__)

OLLAMA_MODEL = "phi3:mini"
GROQ_MODEL   = "llama-3.3-70b-versatile"
HISTORY_FILE = Path(__file__).parent / "data" / "history.json"

_SYSTEM = (
    "Tu es Jarvis, un assistant personnel intelligent, concis et utile. "
    "Réponds en français sauf si l'utilisateur écrit dans une autre langue."
)
_backend = "ollama"  # "ollama" | "groq"

# Client Groq optionnel (actif uniquement si GROQ_API_KEY est défini)
_groq = None
if os.environ.get("GROQ_API_KEY"):
    from groq import Groq
    _groq = Groq(api_key=os.environ["GROQ_API_KEY"])


def _load_history() -> list[dict]:
    try:
        return json.loads(HISTORY_FILE.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _save_history(history: list[dict]) -> None:
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    HISTORY_FILE.write_text(json.dumps(history, ensure_ascii=False, indent=2))


_history: list[dict] = _load_history()


@app.route("/")
def index():
    return render_template("index.html",
                           groq_available=_groq is not None,
                           history=_history)


@app.route("/backend", methods=["POST"])
def set_backend():
    global _backend
    data = request.get_json() or {}
    requested = data.get("backend", "ollama")
    if requested == "groq" and _groq is None:
        return jsonify({"error": "GROQ_API_KEY non définie"}), 400
    _backend = requested
    return jsonify({"backend": _backend})


@app.route("/chat", methods=["POST"])
def chat():
    user_message = (request.get_json() or {}).get("message", "").strip()
    if not user_message:
        return jsonify({"error": "Message vide"}), 400

    _history.append({"role": "user", "content": user_message})

    if _backend == "groq" and _groq:
        response = _groq.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "system", "content": _SYSTEM}] + _history,
            max_tokens=1024,
        )
        reply = response.choices[0].message.content
    else:
        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[{"role": "system", "content": _SYSTEM}] + _history,
        )
        reply = response.message.content

    _history.append({"role": "assistant", "content": reply})
    _save_history(_history)
    return jsonify({"reply": reply, "backend": _backend})


@app.route("/reset", methods=["POST"])
def reset():
    _history.clear()
    _save_history(_history)
    return jsonify({"ok": True})


@app.route("/sw.js")
def service_worker():
    resp = send_from_directory("static", "sw.js")
    resp.headers["Service-Worker-Allowed"] = "/"
    return resp


if __name__ == "__main__":
    mode = "Ollama local"
    if _groq:
        mode += " + Groq cloud disponible"
    msgs = len([m for m in _history if m["role"] == "user"])
    print(f"Jarvis démarré ({mode}) → http://localhost:5000")
    if msgs:
        print(f"{msgs} message(s) chargé(s) depuis l'historique.\n")
    app.run(host="0.0.0.0", port=5000, debug=False)

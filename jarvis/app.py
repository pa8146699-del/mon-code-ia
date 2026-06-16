#!/usr/bin/env python3
"""Jarvis — interface web (Flask + Groq, gratuit)."""

import os
from flask import Flask, jsonify, render_template, request
from groq import Groq

app = Flask(__name__)

MODEL  = "llama-3.3-70b-versatile"
_client = Groq(api_key=os.environ["GROQ_API_KEY"])
_SYSTEM = (
    "Tu es Jarvis, un assistant personnel intelligent, concis et utile. "
    "Réponds en français sauf si l'utilisateur écrit dans une autre langue."
)
_history: list[dict] = []


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    user_message = (request.get_json() or {}).get("message", "").strip()
    if not user_message:
        return jsonify({"error": "Message vide"}), 400

    _history.append({"role": "user", "content": user_message})

    response = _client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "system", "content": _SYSTEM}] + _history,
        max_tokens=1024,
    )

    reply = response.choices[0].message.content
    _history.append({"role": "assistant", "content": reply})
    return jsonify({"reply": reply})


@app.route("/reset", methods=["POST"])
def reset():
    _history.clear()
    return jsonify({"ok": True})


if __name__ == "__main__":
    print("Jarvis démarré → http://localhost:5000\n")
    app.run(host="0.0.0.0", port=5000, debug=False)

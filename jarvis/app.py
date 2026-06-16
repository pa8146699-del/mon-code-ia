#!/usr/bin/env python3
"""Jarvis — interface web pour accès depuis téléphone ou navigateur."""

from flask import Flask, jsonify, render_template, request
import ollama

app = Flask(__name__)

MODEL = "llama3.2"
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

    response = ollama.chat(
        model=MODEL,
        messages=[{"role": "system", "content": _SYSTEM}] + _history,
    )

    reply = response.message.content
    _history.append({"role": "assistant", "content": reply})
    return jsonify({"reply": reply})


@app.route("/reset", methods=["POST"])
def reset():
    _history.clear()
    return jsonify({"ok": True})


if __name__ == "__main__":
    print("Jarvis web démarré → http://localhost:5000")
    print("Sur votre téléphone (même Wi-Fi) → http://<IP-de-votre-PC>:5000\n")
    app.run(host="0.0.0.0", port=5000, debug=False)

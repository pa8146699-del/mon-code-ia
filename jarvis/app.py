#!/usr/bin/env python3
"""Jarvis — assistant web complet (Ollama + Groq, historique, paramètres, épingles)."""

import json
import os
from datetime import datetime
from pathlib import Path

from flask import Flask, Response, jsonify, render_template, request, send_from_directory
import ollama

app = Flask(__name__)

DATA = Path(__file__).parent / "data"
HISTORY_FILE  = DATA / "history.json"
SETTINGS_FILE = DATA / "settings.json"
PINS_FILE     = DATA / "pins.json"

DEFAULT_SETTINGS = {
    "ollama_model":  "phi3:mini",
    "groq_model":    "llama-3.3-70b-versatile",
    "system_prompt": (
        "Tu es Jarvis, un assistant personnel intelligent, concis et utile. "
        "Réponds en français sauf si l'utilisateur écrit dans une autre langue."
    ),
    "voice_enabled": True,
    "theme": "dark",
}

# ── Persistence helpers ───────────────────────────────────────────────────────

def _read(path: Path, default):
    try:
        return json.loads(path.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return default() if callable(default) else default

def _write(path: Path, data) -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2))

# ── State ─────────────────────────────────────────────────────────────────────

_history:  list[dict] = _read(HISTORY_FILE, list)
_pins:     list[dict] = _read(PINS_FILE, list)
_settings: dict       = {**DEFAULT_SETTINGS, **_read(SETTINGS_FILE, dict)}
_backend = "ollama"

_groq = None
if os.environ.get("GROQ_API_KEY"):
    from groq import Groq
    _groq = Groq(api_key=os.environ["GROQ_API_KEY"])

def _ai_msgs(history):
    return [{"role": m["role"], "content": m["content"]} for m in history]

def _now():
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html",
                           groq_available=_groq is not None,
                           history=_history,
                           settings=_settings)

@app.route("/backend", methods=["POST"])
def set_backend():
    global _backend
    b = (request.get_json() or {}).get("backend", "ollama")
    if b == "groq" and not _groq:
        return jsonify({"error": "GROQ_API_KEY non définie"}), 400
    _backend = b
    return jsonify({"backend": _backend})

@app.route("/chat", methods=["POST"])
def chat():
    msg = (request.get_json() or {}).get("message", "").strip()
    if not msg:
        return jsonify({"error": "Message vide"}), 400

    _history.append({"role": "user", "content": msg, "ts": _now()})
    sys = _settings["system_prompt"]

    if _backend == "groq" and _groq:
        r = _groq.chat.completions.create(
            model=_settings["groq_model"],
            messages=[{"role": "system", "content": sys}] + _ai_msgs(_history),
            max_tokens=1024,
        )
        reply = r.choices[0].message.content
    else:
        r = ollama.chat(
            model=_settings["ollama_model"],
            messages=[{"role": "system", "content": sys}] + _ai_msgs(_history),
        )
        reply = r.message.content

    _history.append({"role": "assistant", "content": reply, "ts": _now()})
    _write(HISTORY_FILE, _history)
    return jsonify({"reply": reply, "backend": _backend})

@app.route("/reset", methods=["POST"])
def reset():
    _history.clear()
    _write(HISTORY_FILE, _history)
    return jsonify({"ok": True})

# ── History ───────────────────────────────────────────────────────────────────

@app.route("/history")
def get_history():
    return jsonify(_history)

@app.route("/history/export")
def export_history():
    lines = []
    for m in _history:
        role = "Vous" if m["role"] == "user" else "Jarvis"
        ts = m.get("ts", "")
        lines.append(f"[{ts}] {role}:\n{m['content']}\n")
    return Response("\n".join(lines), mimetype="text/plain",
                    headers={"Content-Disposition": "attachment; filename=jarvis.txt"})

# ── Pins ──────────────────────────────────────────────────────────────────────

@app.route("/pins", methods=["GET"])
def get_pins():
    return jsonify(_pins)

@app.route("/pins", methods=["POST"])
def add_pin():
    msg = request.get_json() or {}
    if not any(p.get("content") == msg.get("content") for p in _pins):
        _pins.append({**msg, "pinned_at": _now()})
        _write(PINS_FILE, _pins)
    return jsonify(_pins)

@app.route("/pins/<int:idx>", methods=["DELETE"])
def remove_pin(idx):
    if 0 <= idx < len(_pins):
        _pins.pop(idx)
        _write(PINS_FILE, _pins)
    return jsonify(_pins)

# ── Settings ──────────────────────────────────────────────────────────────────

@app.route("/settings", methods=["GET"])
def get_settings():
    return jsonify(_settings)

@app.route("/settings", methods=["POST"])
def update_settings():
    data = request.get_json() or {}
    _settings.update({k: v for k, v in data.items() if k in DEFAULT_SETTINGS})
    _write(SETTINGS_FILE, _settings)
    return jsonify(_settings)

# ── PWA ───────────────────────────────────────────────────────────────────────

@app.route("/sw.js")
def service_worker():
    resp = send_from_directory("static", "sw.js")
    resp.headers["Service-Worker-Allowed"] = "/"
    return resp

if __name__ == "__main__":
    mode = "Ollama local" + (" + Groq disponible" if _groq else "")
    msgs = len([m for m in _history if m["role"] == "user"])
    print(f"Jarvis démarré ({mode}) → http://localhost:5000")
    if msgs:
        print(f"{msgs} message(s) en mémoire.\n")
    app.run(host="0.0.0.0", port=5000, debug=False)

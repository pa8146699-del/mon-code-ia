#!/usr/bin/env python3
"""Jarvis — top niveau : streaming, sessions, mémoire, markdown."""

import json
import os
from datetime import datetime
from pathlib import Path

from flask import Flask, Response, jsonify, render_template, request, send_from_directory, stream_with_context
import ollama

app = Flask(__name__)

DATA          = Path(__file__).parent / "data"
SESSIONS_FILE = DATA / "sessions.json"
MEMORY_FILE   = DATA / "memory.json"
SETTINGS_FILE = DATA / "settings.json"
PINS_FILE     = DATA / "pins.json"

DEFAULT_SETTINGS = {
    "ollama_model":  "phi3:mini",
    "groq_model":    "llama-3.3-70b-versatile",
    "system_prompt": (
        "Tu es Jarvis, un assistant personnel intelligent, concis et utile. "
        "Tu réponds en Markdown quand c'est pertinent (listes, code, titres). "
        "Réponds en français sauf si l'utilisateur écrit dans une autre langue."
    ),
    "voice_enabled": True,
    "theme": "dark",
}

# ── Helpers ───────────────────────────────────────────────────────────────────

def _read(path, default):
    try:
        return json.loads(path.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return default() if callable(default) else default

def _write(path, data):
    DATA.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2))

def _now():
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

def _new_id():
    return datetime.now().strftime("%Y%m%d%H%M%S%f")

def _ai_msgs(history):
    return [{"role": m["role"], "content": m["content"]} for m in history]

def _system_prompt():
    base = _settings["system_prompt"]
    if _memory:
        facts = "\n".join(f"- {f}" for f in _memory)
        base += f"\n\n[Ce que tu sais sur l'utilisateur :]\n{facts}"
    return base

def _sse(data: dict) -> str:
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

# ── State ─────────────────────────────────────────────────────────────────────

_sessions: dict = _read(SESSIONS_FILE, dict)
_memory:   list = _read(MEMORY_FILE, list)
_settings: dict = {**DEFAULT_SETTINGS, **_read(SETTINGS_FILE, dict)}
_pins:     list = _read(PINS_FILE, list)
_backend = "ollama"

# Session courante = la plus récente, ou nouvelle
if _sessions:
    _current = max(_sessions, key=lambda k: _sessions[k].get("created_at", ""))
else:
    _current = _new_id()
    _sessions[_current] = {"id": _current, "title": "Nouvelle conversation",
                           "created_at": _now(), "messages": []}
    _write(SESSIONS_FILE, _sessions)

_groq = None
if os.environ.get("GROQ_API_KEY"):
    from groq import Groq
    _groq = Groq(api_key=os.environ["GROQ_API_KEY"])

# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    sess = _sessions.get(_current, {})
    return render_template("index.html",
                           groq_available=_groq is not None,
                           settings=_settings,
                           current_session=sess,
                           history=sess.get("messages", []))

# ── Chat (streaming SSE) ──────────────────────────────────────────────────────

@app.route("/chat", methods=["POST"])
def chat():
    global _current
    msg = (request.get_json() or {}).get("message", "").strip()
    if not msg:
        return jsonify({"error": "Message vide"}), 400

    sess = _sessions.setdefault(_current, {
        "id": _current, "title": "Nouvelle conversation",
        "created_at": _now(), "messages": []
    })
    history = sess["messages"]
    history.append({"role": "user", "content": msg, "ts": _now()})

    # Auto-titre sur le premier message
    if len(history) == 1:
        sess["title"] = (msg[:45] + "…") if len(msg) > 45 else msg

    sys = _system_prompt()

    def generate():
        full = ""
        try:
            if _backend == "groq" and _groq:
                stream = _groq.chat.completions.create(
                    model=_settings["groq_model"],
                    messages=[{"role": "system", "content": sys}] + _ai_msgs(history),
                    max_tokens=2048,
                    stream=True,
                )
                for chunk in stream:
                    tok = (chunk.choices[0].delta.content or "")
                    if tok:
                        full += tok
                        yield _sse({"token": tok})
            else:
                stream = ollama.chat(
                    model=_settings["ollama_model"],
                    messages=[{"role": "system", "content": sys}] + _ai_msgs(history),
                    stream=True,
                )
                for chunk in stream:
                    tok = chunk.message.content or ""
                    if tok:
                        full += tok
                        yield _sse({"token": tok})
        except Exception as e:
            yield _sse({"error": str(e)})
            history.pop()
            return

        history.append({"role": "assistant", "content": full, "ts": _now()})
        _write(SESSIONS_FILE, _sessions)
        yield _sse({"done": True, "backend": _backend, "title": sess["title"]})

    return Response(stream_with_context(generate()),
                    content_type="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

@app.route("/reset", methods=["POST"])
def reset():
    if _current in _sessions:
        _sessions[_current]["messages"] = []
        _sessions[_current]["title"] = "Nouvelle conversation"
        _write(SESSIONS_FILE, _sessions)
    return jsonify({"ok": True})

# ── Sessions ──────────────────────────────────────────────────────────────────

@app.route("/sessions")
def list_sessions():
    lst = sorted(_sessions.values(), key=lambda s: s.get("created_at", ""), reverse=True)
    return jsonify([{**s, "messages": None,
                     "count": len(s.get("messages", []))} for s in lst])

@app.route("/sessions", methods=["POST"])
def new_session():
    global _current
    _current = _new_id()
    _sessions[_current] = {"id": _current, "title": "Nouvelle conversation",
                            "created_at": _now(), "messages": []}
    _write(SESSIONS_FILE, _sessions)
    return jsonify({"id": _current})

@app.route("/sessions/<sid>", methods=["GET"])
def get_session(sid):
    s = _sessions.get(sid)
    if not s:
        return jsonify({"error": "Session inconnue"}), 404
    return jsonify(s)

@app.route("/sessions/<sid>/activate", methods=["POST"])
def activate_session(sid):
    global _current
    if sid not in _sessions:
        return jsonify({"error": "Session inconnue"}), 404
    _current = sid
    return jsonify(_sessions[sid])

@app.route("/sessions/<sid>", methods=["DELETE"])
def delete_session(sid):
    global _current
    _sessions.pop(sid, None)
    if _current == sid:
        if _sessions:
            _current = max(_sessions, key=lambda k: _sessions[k].get("created_at", ""))
        else:
            _current = _new_id()
            _sessions[_current] = {"id": _current, "title": "Nouvelle conversation",
                                   "created_at": _now(), "messages": []}
    _write(SESSIONS_FILE, _sessions)
    return jsonify({"ok": True, "current": _current})

@app.route("/sessions/<sid>/rename", methods=["POST"])
def rename_session(sid):
    name = (request.get_json() or {}).get("title", "").strip()
    if sid in _sessions and name:
        _sessions[sid]["title"] = name
        _write(SESSIONS_FILE, _sessions)
    return jsonify({"ok": True})

@app.route("/history/export")
def export_history():
    sess = _sessions.get(_current, {})
    lines = []
    for m in sess.get("messages", []):
        role = "Vous" if m["role"] == "user" else "Jarvis"
        lines.append(f"[{m.get('ts','')}] {role}:\n{m['content']}\n")
    return Response("\n".join(lines), mimetype="text/plain",
                    headers={"Content-Disposition": "attachment; filename=jarvis.txt"})

# ── Memory ────────────────────────────────────────────────────────────────────

@app.route("/memory")
def get_memory():
    return jsonify(_memory)

@app.route("/memory", methods=["POST"])
def add_memory():
    fact = (request.get_json() or {}).get("fact", "").strip()
    if fact and fact not in _memory:
        _memory.append(fact)
        _write(MEMORY_FILE, _memory)
    return jsonify(_memory)

@app.route("/memory/<int:idx>", methods=["DELETE"])
def del_memory(idx):
    if 0 <= idx < len(_memory):
        _memory.pop(idx)
        _write(MEMORY_FILE, _memory)
    return jsonify(_memory)

# ── Pins ──────────────────────────────────────────────────────────────────────

@app.route("/pins")
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
def del_pin(idx):
    if 0 <= idx < len(_pins):
        _pins.pop(idx)
        _write(PINS_FILE, _pins)
    return jsonify(_pins)

# ── Settings ──────────────────────────────────────────────────────────────────

@app.route("/settings", methods=["GET"])
def get_settings():
    return jsonify(_settings)

@app.route("/settings", methods=["POST"])
def upd_settings():
    data = request.get_json() or {}
    _settings.update({k: v for k, v in data.items() if k in DEFAULT_SETTINGS})
    _write(SETTINGS_FILE, _settings)
    return jsonify(_settings)

# ── Backend ───────────────────────────────────────────────────────────────────

@app.route("/backend", methods=["POST"])
def set_backend():
    global _backend
    b = (request.get_json() or {}).get("backend", "ollama")
    if b == "groq" and not _groq:
        return jsonify({"error": "GROQ_API_KEY non définie"}), 400
    _backend = b
    return jsonify({"backend": _backend})

@app.route("/sw.js")
def service_worker():
    resp = send_from_directory("static", "sw.js")
    resp.headers["Service-Worker-Allowed"] = "/"
    return resp

if __name__ == "__main__":
    mode = "Ollama" + (" + Groq" if _groq else "")
    print(f"Jarvis démarré ({mode}) → http://localhost:5000\n")
    app.run(host="0.0.0.0", port=5000, debug=False)

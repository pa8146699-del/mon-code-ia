#!/usr/bin/env python3
"""Client API + boucle d'agent — stdlib pure (urllib, zéro SDK).

Trois moteurs au choix, via la variable d'environnement AGENTOS_PROVIDER :

    groq       (DÉFAUT) — GRATUIT, sans carte bancaire. Clé gratuite sur
               https://console.groq.com. Modèles Llama, API compatible OpenAI.
    gemini     GRATUIT. Clé gratuite sur https://aistudio.google.com.
               Modèles Google Gemini, function calling.
    anthropic  Claude (Fable 5). Payant au token. Clé sur console.anthropic.com.

Aucune dépendance externe : tout passe par urllib, donc l'APK se build avec
`python3,kivy` seulement. Code partagé entre agent.py (terminal/voix) et
agentmobile/ (Kivy).

Clé : fournie via l'argument api_key, sinon lue dans l'environnement
(GEMINI_API_KEY / GROQ_API_KEY / ANTHROPIC_API_KEY selon le moteur).
"""

import json
import os
import urllib.error
import urllib.request

try:
    import requests as _requests
    _HAS_REQUESTS = True
except ImportError:
    _HAS_REQUESTS = False

from tools import TOOLS, dispatch

PROVIDER = os.environ.get("AGENTOS_PROVIDER", "groq").lower()

# --- Configuration par moteur ----------------------------------------------

_GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
_GEMINI_API = "https://generativelanguage.googleapis.com/v1beta/models"

_GROQ_API = "https://api.groq.com/openai/v1/chat/completions"
_GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")

_ANTHROPIC_API = "https://api.anthropic.com/v1/messages"
_ANTHROPIC_MODEL = "claude-fable-5"
_ANTHROPIC_VERSION = "2023-06-01"

_KEY_VAR = {
    "gemini": "GEMINI_API_KEY",
    "groq": "GROQ_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
}

SYSTEM = (
    "Tu es AgentOS, un assistant personnel qui gère un système centralisé "
    "(clients, projets, tâches, finances, notes) servant de source unique de "
    "vérité. Tu ne te contentes pas de discuter : tu utilises les outils mis à "
    "ta disposition pour LIRE et ÉCRIRE concrètement dans la base. Quand "
    "l'utilisateur te donne une information (une dépense, un prospect, une "
    "tâche…), enregistre-la avec le bon outil, puis confirme brièvement. "
    "Quand il pose une question, interroge la base avant de répondre. "
    "Réponds en français, de façon concise."
)


def _env_key() -> str | None:
    return os.environ.get(_KEY_VAR.get(PROVIDER, ""))


def _post(url: str, payload: dict, headers: dict) -> dict:
    headers = {"User-Agent": "AgentOS/1.0", **headers}
    if _HAS_REQUESTS:
        r = _requests.post(url, json=payload, headers=headers, timeout=60)
        r.raise_for_status()
        return r.json()
    request = urllib.request.Request(
        url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST"
    )
    with urllib.request.urlopen(request, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


# --- Moteur Gemini (Google) ------------------------------------------------

def _gemini_tools() -> list[dict]:
    """Convertit TOOLS vers les function_declarations de Gemini."""
    decls = []
    for t in TOOLS:
        decl = {"name": t["name"], "description": t["description"]}
        params = t.get("input_schema", {})
        if params.get("properties"):  # Gemini refuse un objet de params vide
            decl["parameters"] = params
        decls.append(decl)
    return [{"function_declarations": decls}]


def _run_gemini(conn, history, key, on_tool) -> str:
    url = f"{_GEMINI_API}/{_GEMINI_MODEL}:generateContent"
    headers = {"Content-Type": "application/json", "x-goog-api-key": key}
    while True:
        payload = {
            "systemInstruction": {"parts": [{"text": SYSTEM}]},
            "contents": history,
            "tools": _gemini_tools(),
        }
        data = _post(url, payload, headers)
        candidates = data.get("candidates")
        if not candidates:
            return f"Réponse vide du modèle : {json.dumps(data, ensure_ascii=False)[:300]}"

        parts = candidates[0].get("content", {}).get("parts", [])
        history.append({"role": "model", "parts": parts})

        calls = [p["functionCall"] for p in parts if "functionCall" in p]
        if not calls:
            return "".join(p.get("text", "") for p in parts if "text" in p)

        responses = []
        for fc in calls:
            name = fc["name"]
            args = fc.get("args") or {}
            if on_tool:
                on_tool(name, args)
            output = dispatch(conn, name, args)
            try:
                parsed = json.loads(output)
            except json.JSONDecodeError:
                parsed = output
            if not isinstance(parsed, dict):
                parsed = {"result": parsed}
            responses.append({"functionResponse": {"name": name, "response": parsed}})
        history.append({"role": "user", "parts": responses})


# --- Moteur Groq / compatible OpenAI ---------------------------------------

def _openai_tools() -> list[dict]:
    """Convertit TOOLS (format Anthropic) vers le format function-calling OpenAI."""
    return [
        {
            "type": "function",
            "function": {
                "name": t["name"],
                "description": t["description"],
                "parameters": t["input_schema"],
            },
        }
        for t in TOOLS
    ]


def _run_openai(conn, history, key, on_tool) -> str:
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    while True:
        payload = {
            "model": _GROQ_MODEL,
            "max_tokens": 1024,
            "messages": [{"role": "system", "content": SYSTEM}, *history],
            "tools": _openai_tools(),
        }
        data = _post(_GROQ_API, payload, headers)
        message = data["choices"][0]["message"]
        history.append(message)

        calls = message.get("tool_calls")
        if not calls:
            return message.get("content") or ""

        for call in calls:
            name = call["function"]["name"]
            try:
                args = json.loads(call["function"].get("arguments") or "{}")
            except json.JSONDecodeError:
                args = {}
            if on_tool:
                on_tool(name, args)
            output = dispatch(conn, name, args)
            history.append({"role": "tool", "tool_call_id": call["id"], "content": output})


# --- Moteur Anthropic / Claude ---------------------------------------------

def _run_anthropic(conn, history, key, on_tool) -> str:
    headers = {
        "x-api-key": key,
        "anthropic-version": _ANTHROPIC_VERSION,
        "content-type": "application/json",
    }
    while True:
        payload = {
            "model": _ANTHROPIC_MODEL,
            "max_tokens": 1024,
            "system": SYSTEM,
            "tools": TOOLS,
            "messages": history,
        }
        data = _post(_ANTHROPIC_API, payload, headers)
        content = data.get("content", [])
        history.append({"role": "assistant", "content": content})

        if data.get("stop_reason") != "tool_use":
            return "".join(b.get("text", "") for b in content if b.get("type") == "text")

        tool_results = []
        for block in content:
            if block.get("type") != "tool_use":
                continue
            if on_tool:
                on_tool(block["name"], block["input"])
            output = dispatch(conn, block["name"], block["input"])
            tool_results.append(
                {"type": "tool_result", "tool_use_id": block["id"], "content": output}
            )
        history.append({"role": "user", "content": tool_results})


_RUNNERS = {"gemini": _run_gemini, "groq": _run_openai, "anthropic": _run_anthropic}


# --- Point d'entrée ---------------------------------------------------------

def run_turn(conn, history: list[dict], user_message: str,
             api_key: str | None = None, on_tool=None) -> str:
    """Ajoute le message, déroule la boucle de tool use, retourne le texte final.

    `history` est muté en place. Son format dépend du moteur (AGENTOS_PROVIDER) ;
    garde un même historique pour un même moteur sur toute la session.
    `on_tool(name, args)` est appelé avant chaque exécution d'outil (optionnel).
    """
    key = api_key or _env_key()
    if not key:
        raise RuntimeError(
            f"Clé API manquante ({_KEY_VAR.get(PROVIDER, '?')} ou argument api_key)."
        )

    if PROVIDER == "gemini":
        history.append({"role": "user", "parts": [{"text": user_message}]})
    else:
        history.append({"role": "user", "content": user_message})

    runner = _RUNNERS.get(PROVIDER, _run_gemini)
    try:
        return runner(conn, history, key, on_tool)
    except urllib.error.HTTPError as e:
        return f"Erreur API ({e.code}) : {e.read().decode('utf-8', 'replace')}"
    except (urllib.error.URLError, OSError) as e:
        return f"Erreur réseau : {e}"

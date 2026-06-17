#!/usr/bin/env python3
"""Client API + boucle d'agent — stdlib pure (urllib, zéro SDK).

Deux moteurs au choix, via la variable d'environnement AGENTOS_PROVIDER :

    groq       (DÉFAUT) — GRATUIT. Clé gratuite sur https://console.groq.com
               (sans carte bancaire). Modèle Llama, API compatible OpenAI.
    anthropic  — Claude (Fable 5). Payant au token. Clé sur console.anthropic.com.

Aucune dépendance externe : tout passe par urllib, donc l'APK se build avec
`python3,kivy` seulement. Code partagé entre agent.py (terminal/voix) et
agentmobile/ (Kivy).

Clé : fournie via l'argument api_key, sinon lue dans l'environnement
(GROQ_API_KEY pour groq, ANTHROPIC_API_KEY pour anthropic).
"""

import json
import os
import urllib.error
import urllib.request

from tools import TOOLS, dispatch

PROVIDER = os.environ.get("AGENTOS_PROVIDER", "groq").lower()

# --- Configuration par moteur ----------------------------------------------

_GROQ_API = "https://api.groq.com/openai/v1/chat/completions"
_GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")

_ANTHROPIC_API = "https://api.anthropic.com/v1/messages"
_ANTHROPIC_MODEL = "claude-fable-5"
_ANTHROPIC_VERSION = "2023-06-01"

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
    return os.environ.get("GROQ_API_KEY" if PROVIDER == "groq" else "ANTHROPIC_API_KEY")


def _post(url: str, payload: dict, headers: dict) -> dict:
    request = urllib.request.Request(
        url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST"
    )
    with urllib.request.urlopen(request, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


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
        var = "GROQ_API_KEY" if PROVIDER == "groq" else "ANTHROPIC_API_KEY"
        raise RuntimeError(f"Clé API manquante ({var} ou argument api_key).")

    # En format OpenAI le message user est une chaîne ; en Anthropic aussi.
    history.append({"role": "user", "content": user_message})

    runner = _run_openai if PROVIDER == "groq" else _run_anthropic
    try:
        return runner(conn, history, key, on_tool)
    except urllib.error.HTTPError as e:
        return f"Erreur API ({e.code}) : {e.read().decode('utf-8', 'replace')}"
    except (urllib.error.URLError, OSError) as e:
        return f"Erreur réseau : {e}"

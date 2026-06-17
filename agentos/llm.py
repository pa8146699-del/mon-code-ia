#!/usr/bin/env python3
"""Client API Claude + boucle d'agent — stdlib pure (urllib, zéro SDK).

Utiliser le SDK `anthropic` est pratique sur PC mais lourd à empaqueter pour
Android (httpx, pydantic…). Ici on parle directement à l'API Messages via
urllib : aucune dépendance externe, donc l'APK se build avec `python3,kivy`
seulement, et le code est partagé entre `agent.py` (terminal/voix) et
`agentmobile/` (Kivy).

La seule chose qui se « paie » est l'usage de l'API au token (pas d'abonnement) :
fournis une clé via ANTHROPIC_API_KEY ou l'argument api_key.
"""

import json
import os
import urllib.error
import urllib.request

from tools import TOOLS, dispatch

_API = "https://api.anthropic.com/v1/messages"
_MODEL = "claude-sonnet-4-6"
_VERSION = "2023-06-01"

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


def _call(messages: list[dict], api_key: str) -> dict:
    """Un appel à l'API Messages. Retourne le JSON décodé."""
    payload = {
        "model": _MODEL,
        "max_tokens": 1024,
        "system": SYSTEM,
        "tools": TOOLS,
        "messages": messages,
    }
    request = urllib.request.Request(
        _API,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "x-api-key": api_key,
            "anthropic-version": _VERSION,
            "content-type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def run_turn(conn, history: list[dict], user_message: str,
             api_key: str | None = None, on_tool=None) -> str:
    """Ajoute le message, déroule la boucle de tool use, retourne le texte final.

    `history` est muté en place (compatible JSON, réutilisable au tour suivant).
    `on_tool(name, args)` est appelé avant chaque exécution d'outil (optionnel).
    """
    key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise RuntimeError("Clé API manquante (ANTHROPIC_API_KEY ou argument api_key).")

    history.append({"role": "user", "content": user_message})

    while True:
        try:
            response = _call(history, key)
        except urllib.error.HTTPError as e:
            return f"Erreur API ({e.code}) : {e.read().decode('utf-8', 'replace')}"
        except (urllib.error.URLError, OSError) as e:
            return f"Erreur réseau : {e}"

        content = response.get("content", [])
        history.append({"role": "assistant", "content": content})

        if response.get("stop_reason") != "tool_use":
            return "".join(b.get("text", "") for b in content if b.get("type") == "text")

        tool_results = []
        for block in content:
            if block.get("type") != "tool_use":
                continue
            if on_tool:
                on_tool(block["name"], block["input"])
            output = dispatch(conn, block["name"], block["input"])
            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block["id"],
                    "content": output,
                }
            )
        history.append({"role": "user", "content": tool_results})

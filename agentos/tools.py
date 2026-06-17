#!/usr/bin/env python3
"""Outils (tool use) qu'AgentOS expose à Claude.

TOOLS = la liste de définitions JSON envoyée à l'API Claude.
dispatch(conn, name, args) = exécute l'outil demandé contre la base SQLite,
synchronise vers Notion en best-effort, et retourne un résultat JSON.

Ajouter un outil = une entrée dans TOOLS + une branche dans dispatch().
"""

import json

import db
import notion_sync

TOOLS = [
    {
        "name": "add_client",
        "description": "Ajoute un client/prospect au CRM.",
        "input_schema": {
            "type": "object",
            "properties": {
                "nom": {"type": "string"},
                "email": {"type": "string"},
                "telephone": {"type": "string"},
                "statut": {"type": "string", "description": "prospect, actif, perdu…"},
                "notes": {"type": "string"},
            },
            "required": ["nom"],
        },
    },
    {
        "name": "list_clients",
        "description": "Liste les clients, éventuellement filtrés par statut.",
        "input_schema": {
            "type": "object",
            "properties": {"statut": {"type": "string"}},
        },
    },
    {
        "name": "update_client",
        "description": "Met à jour un client existant (par son id).",
        "input_schema": {
            "type": "object",
            "properties": {
                "client_id": {"type": "integer"},
                "nom": {"type": "string"},
                "email": {"type": "string"},
                "telephone": {"type": "string"},
                "statut": {"type": "string"},
                "notes": {"type": "string"},
            },
            "required": ["client_id"],
        },
    },
    {
        "name": "add_projet",
        "description": "Crée un projet, éventuellement rattaché à un client (client_id).",
        "input_schema": {
            "type": "object",
            "properties": {
                "titre": {"type": "string"},
                "client_id": {"type": "integer"},
                "statut": {"type": "string"},
                "echeance": {"type": "string", "description": "date AAAA-MM-JJ"},
                "description": {"type": "string"},
            },
            "required": ["titre"],
        },
    },
    {
        "name": "list_projets",
        "description": "Liste les projets, éventuellement filtrés par statut.",
        "input_schema": {
            "type": "object",
            "properties": {"statut": {"type": "string"}},
        },
    },
    {
        "name": "update_projet",
        "description": "Met à jour un projet existant (par son id).",
        "input_schema": {
            "type": "object",
            "properties": {
                "projet_id": {"type": "integer"},
                "titre": {"type": "string"},
                "client_id": {"type": "integer"},
                "statut": {"type": "string"},
                "echeance": {"type": "string"},
                "description": {"type": "string"},
            },
            "required": ["projet_id"],
        },
    },
    {
        "name": "add_tache",
        "description": "Crée une tâche, éventuellement rattachée à un projet (projet_id).",
        "input_schema": {
            "type": "object",
            "properties": {
                "titre": {"type": "string"},
                "projet_id": {"type": "integer"},
                "statut": {"type": "string", "description": "à faire, en cours, terminé"},
                "echeance": {"type": "string"},
            },
            "required": ["titre"],
        },
    },
    {
        "name": "list_taches",
        "description": "Liste les tâches, éventuellement filtrées par statut.",
        "input_schema": {
            "type": "object",
            "properties": {"statut": {"type": "string"}},
        },
    },
    {
        "name": "update_tache",
        "description": "Met à jour une tâche existante (par son id), p. ex. pour la marquer terminée.",
        "input_schema": {
            "type": "object",
            "properties": {
                "tache_id": {"type": "integer"},
                "titre": {"type": "string"},
                "projet_id": {"type": "integer"},
                "statut": {"type": "string"},
                "echeance": {"type": "string"},
            },
            "required": ["tache_id"],
        },
    },
    {
        "name": "add_finance",
        "description": "Enregistre une dépense ou un revenu. Sert à catégoriser une facture.",
        "input_schema": {
            "type": "object",
            "properties": {
                "type": {"type": "string", "enum": ["depense", "revenu"]},
                "montant": {"type": "number"},
                "categorie": {"type": "string"},
                "description": {"type": "string"},
                "date": {"type": "string", "description": "date AAAA-MM-JJ"},
            },
            "required": ["type", "montant"],
        },
    },
    {
        "name": "list_finances",
        "description": "Liste les transactions, filtrables par type et/ou catégorie.",
        "input_schema": {
            "type": "object",
            "properties": {
                "type": {"type": "string", "enum": ["depense", "revenu"]},
                "categorie": {"type": "string"},
            },
        },
    },
    {
        "name": "finance_summary",
        "description": "Renvoie revenus, dépenses, solde, et dépenses par catégorie.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "add_note",
        "description": "Sauvegarde une note dans la base de connaissances.",
        "input_schema": {
            "type": "object",
            "properties": {
                "titre": {"type": "string"},
                "contenu": {"type": "string"},
                "tags": {"type": "string", "description": "mots-clés séparés par des virgules"},
            },
            "required": ["titre", "contenu"],
        },
    },
    {
        "name": "search_notes",
        "description": "Recherche des notes par titre, contenu ou tags.",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
    },
]

# Les outils d'écriture dont le résultat est poussé vers Notion (best-effort).
_SYNC_TABLE = {
    "add_client": "clients",
    "add_projet": "projets",
    "add_tache": "taches",
    "add_finance": "finances",
    "add_note": "notes",
}

# Nom de l'outil -> fonction db. Les fonctions update_* reçoivent l'id en 1er.
_HANDLERS = {
    "add_client": db.add_client,
    "list_clients": db.list_clients,
    "update_client": lambda conn, **a: db.update_client(conn, a.pop("client_id"), **a),
    "add_projet": db.add_projet,
    "list_projets": db.list_projets,
    "update_projet": lambda conn, **a: db.update_projet(conn, a.pop("projet_id"), **a),
    "add_tache": db.add_tache,
    "list_taches": db.list_taches,
    "update_tache": lambda conn, **a: db.update_tache(conn, a.pop("tache_id"), **a),
    "add_finance": db.add_finance,
    "list_finances": db.list_finances,
    "finance_summary": db.finance_summary,
    "add_note": db.add_note,
    "search_notes": db.search_notes,
}


def dispatch(conn, name: str, args: dict) -> str:
    """Exécute l'outil `name` et retourne son résultat sérialisé en JSON."""
    handler = _HANDLERS.get(name)
    if handler is None:
        return json.dumps({"erreur": f"outil inconnu : {name}"}, ensure_ascii=False)

    try:
        result = handler(conn, **args)
    except Exception as e:  # remonte l'erreur à Claude au lieu de planter
        return json.dumps({"erreur": str(e)}, ensure_ascii=False)

    # Synchro Notion best-effort : ne bloque jamais l'agent si elle échoue.
    table = _SYNC_TABLE.get(name)
    if table and isinstance(result, dict) and result.get("id"):
        notion_sync.sync_row(table, result)

    return json.dumps(result, ensure_ascii=False, default=str)

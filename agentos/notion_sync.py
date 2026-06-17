#!/usr/bin/env python3
"""Synchro best-effort vers Notion — la couche « hybride » d'AgentOS.

La base SQLite reste la source unique de vérité ; Notion sert de miroir
consultable depuis le portable. Cette synchro ne plante JAMAIS l'agent :
toute erreur (réseau, config absente, propriété manquante) est avalée et
journalisée discrètement.

Configuration (variables d'environnement, toutes optionnelles) :
    NOTION_TOKEN          jeton d'intégration interne Notion (secret_…)
    NOTION_DB_CLIENTS     id de la base Notion « Clients »
    NOTION_DB_PROJETS     id de la base Notion « Projets »
    NOTION_DB_TACHES      id de la base Notion « Tâches »
    NOTION_DB_FINANCES    id de la base Notion « Finances »
    NOTION_DB_NOTES       id de la base Notion « Notes »
    NOTION_TITLE_PROP     nom de la propriété titre (défaut : « Name »)

Si NOTION_TOKEN ou l'id de base correspondant est absent, sync_row() est un
no-op qui renvoie False. Zéro dépendance externe (urllib stdlib).
"""

import json
import os
import urllib.error
import urllib.request

_API = "https://api.notion.com/v1/pages"
_VERSION = "2022-06-28"

# table SQLite -> variable d'env contenant l'id de la base Notion
_DB_ENV = {
    "clients": "NOTION_DB_CLIENTS",
    "projets": "NOTION_DB_PROJETS",
    "taches": "NOTION_DB_TACHES",
    "finances": "NOTION_DB_FINANCES",
    "notes": "NOTION_DB_NOTES",
}

# table -> champ utilisé comme titre de la page Notion
_TITLE_FIELD = {
    "clients": "nom",
    "projets": "titre",
    "taches": "titre",
    "finances": "description",
    "notes": "titre",
}


def _title_for(table: str, row: dict) -> str:
    field = _TITLE_FIELD.get(table, "id")
    return str(row.get(field) or f"{table} #{row.get('id')}")


def sync_row(table: str, row: dict) -> bool:
    """Crée une page Notion miroir de `row`. Best-effort : renvoie True/False."""
    token = os.environ.get("NOTION_TOKEN")
    database_id = os.environ.get(_DB_ENV.get(table, ""))
    if not token or not database_id:
        return False  # non configuré -> on ignore silencieusement

    title_prop = os.environ.get("NOTION_TITLE_PROP", "Name")
    payload = {
        "parent": {"database_id": database_id},
        "properties": {
            title_prop: {
                "title": [{"text": {"content": _title_for(table, row)[:200]}}]
            }
        },
        # Le détail complet (JSON) va dans le corps de la page : aucune
        # contrainte de schéma côté Notion, donc pas d'erreur « propriété ».
        "children": [
            {
                "object": "block",
                "type": "code",
                "code": {
                    "language": "json",
                    "rich_text": [
                        {"text": {"content": json.dumps(row, ensure_ascii=False, default=str)}}
                    ],
                },
            }
        ],
    }

    request = urllib.request.Request(
        _API,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Notion-Version": _VERSION,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as resp:
            return resp.status in (200, 201)
    except (urllib.error.URLError, OSError) as e:
        print(f"[notion_sync] synchro {table} ignorée : {e}")
        return False

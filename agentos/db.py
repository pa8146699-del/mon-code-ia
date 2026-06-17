#!/usr/bin/env python3
"""Base de données SQLite d'AgentOS — la source unique de vérité.

Zéro dépendance externe (sqlite3 stdlib). Le chemin du fichier est lu depuis
la variable d'environnement AGENTOS_DB, sinon agentos/agentos.db par défaut.

Cinq domaines : clients, projets, taches, finances, notes.
Toutes les fonctions d'écriture retournent la ligne créée/modifiée sous forme
de dict (sérialisable JSON) — pratique pour la synchro Notion et le tool use.
"""

import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_DB = Path(__file__).resolve().parent / "agentos.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS clients (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    nom        TEXT NOT NULL,
    email      TEXT,
    telephone  TEXT,
    statut     TEXT DEFAULT 'prospect',
    notes      TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS projets (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    titre       TEXT NOT NULL,
    client_id   INTEGER REFERENCES clients(id),
    statut      TEXT DEFAULT 'en cours',
    echeance    TEXT,
    description TEXT,
    created_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS taches (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    titre      TEXT NOT NULL,
    projet_id  INTEGER REFERENCES projets(id),
    statut     TEXT DEFAULT 'à faire',
    echeance   TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS finances (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    type        TEXT NOT NULL CHECK (type IN ('depense', 'revenu')),
    montant     REAL NOT NULL,
    categorie   TEXT,
    description TEXT,
    date        TEXT NOT NULL,
    created_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS notes (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    titre      TEXT NOT NULL,
    contenu    TEXT NOT NULL,
    tags       TEXT,
    created_at TEXT NOT NULL
);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def connect(db_path: str | os.PathLike | None = None) -> sqlite3.Connection:
    """Ouvre la base (la crée si besoin) et garantit le schéma."""
    path = db_path or os.environ.get("AGENTOS_DB") or DEFAULT_DB
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)
    conn.commit()
    return conn


def _row(conn: sqlite3.Connection, table: str, row_id: int) -> dict:
    cur = conn.execute(f"SELECT * FROM {table} WHERE id = ?", (row_id,))
    found = cur.fetchone()
    return dict(found) if found else {}


# --- Clients ---------------------------------------------------------------

def add_client(conn, nom, email=None, telephone=None, statut="prospect", notes=None) -> dict:
    cur = conn.execute(
        "INSERT INTO clients (nom, email, telephone, statut, notes, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (nom, email, telephone, statut, notes, _now()),
    )
    conn.commit()
    return _row(conn, "clients", cur.lastrowid)


def list_clients(conn, statut=None) -> list[dict]:
    if statut:
        cur = conn.execute("SELECT * FROM clients WHERE statut = ? ORDER BY id", (statut,))
    else:
        cur = conn.execute("SELECT * FROM clients ORDER BY id")
    return [dict(r) for r in cur.fetchall()]


def update_client(conn, client_id, **fields) -> dict:
    allowed = {"nom", "email", "telephone", "statut", "notes"}
    sets = {k: v for k, v in fields.items() if k in allowed and v is not None}
    if sets:
        clause = ", ".join(f"{k} = ?" for k in sets)
        conn.execute(f"UPDATE clients SET {clause} WHERE id = ?", (*sets.values(), client_id))
        conn.commit()
    return _row(conn, "clients", client_id)


# --- Projets ---------------------------------------------------------------

def add_projet(conn, titre, client_id=None, statut="en cours", echeance=None, description=None) -> dict:
    cur = conn.execute(
        "INSERT INTO projets (titre, client_id, statut, echeance, description, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (titre, client_id, statut, echeance, description, _now()),
    )
    conn.commit()
    return _row(conn, "projets", cur.lastrowid)


def list_projets(conn, statut=None) -> list[dict]:
    if statut:
        cur = conn.execute("SELECT * FROM projets WHERE statut = ? ORDER BY id", (statut,))
    else:
        cur = conn.execute("SELECT * FROM projets ORDER BY id")
    return [dict(r) for r in cur.fetchall()]


def update_projet(conn, projet_id, **fields) -> dict:
    allowed = {"titre", "client_id", "statut", "echeance", "description"}
    sets = {k: v for k, v in fields.items() if k in allowed and v is not None}
    if sets:
        clause = ", ".join(f"{k} = ?" for k in sets)
        conn.execute(f"UPDATE projets SET {clause} WHERE id = ?", (*sets.values(), projet_id))
        conn.commit()
    return _row(conn, "projets", projet_id)


# --- Tâches ----------------------------------------------------------------

def add_tache(conn, titre, projet_id=None, statut="à faire", echeance=None) -> dict:
    cur = conn.execute(
        "INSERT INTO taches (titre, projet_id, statut, echeance, created_at) "
        "VALUES (?, ?, ?, ?, ?)",
        (titre, projet_id, statut, echeance, _now()),
    )
    conn.commit()
    return _row(conn, "taches", cur.lastrowid)


def list_taches(conn, statut=None) -> list[dict]:
    if statut:
        cur = conn.execute("SELECT * FROM taches WHERE statut = ? ORDER BY id", (statut,))
    else:
        cur = conn.execute("SELECT * FROM taches ORDER BY id")
    return [dict(r) for r in cur.fetchall()]


def update_tache(conn, tache_id, **fields) -> dict:
    allowed = {"titre", "projet_id", "statut", "echeance"}
    sets = {k: v for k, v in fields.items() if k in allowed and v is not None}
    if sets:
        clause = ", ".join(f"{k} = ?" for k in sets)
        conn.execute(f"UPDATE taches SET {clause} WHERE id = ?", (*sets.values(), tache_id))
        conn.commit()
    return _row(conn, "taches", tache_id)


# --- Finances --------------------------------------------------------------

def add_finance(conn, type, montant, categorie=None, description=None, date=None) -> dict:
    cur = conn.execute(
        "INSERT INTO finances (type, montant, categorie, description, date, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (type, float(montant), categorie, description, date or _now()[:10], _now()),
    )
    conn.commit()
    return _row(conn, "finances", cur.lastrowid)


def list_finances(conn, type=None, categorie=None) -> list[dict]:
    clauses, params = [], []
    if type:
        clauses.append("type = ?")
        params.append(type)
    if categorie:
        clauses.append("categorie = ?")
        params.append(categorie)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    cur = conn.execute(f"SELECT * FROM finances {where} ORDER BY date", params)
    return [dict(r) for r in cur.fetchall()]


def finance_summary(conn) -> dict:
    """Totaux revenus / dépenses / solde et dépenses par catégorie."""
    revenus = conn.execute(
        "SELECT COALESCE(SUM(montant), 0) FROM finances WHERE type = 'revenu'"
    ).fetchone()[0]
    depenses = conn.execute(
        "SELECT COALESCE(SUM(montant), 0) FROM finances WHERE type = 'depense'"
    ).fetchone()[0]
    par_categorie = {
        r["categorie"] or "(sans catégorie)": r["total"]
        for r in conn.execute(
            "SELECT categorie, SUM(montant) AS total FROM finances "
            "WHERE type = 'depense' GROUP BY categorie"
        ).fetchall()
    }
    return {
        "revenus": round(revenus, 2),
        "depenses": round(depenses, 2),
        "solde": round(revenus - depenses, 2),
        "depenses_par_categorie": par_categorie,
    }


# --- Notes -----------------------------------------------------------------

def add_note(conn, titre, contenu, tags=None) -> dict:
    cur = conn.execute(
        "INSERT INTO notes (titre, contenu, tags, created_at) VALUES (?, ?, ?, ?)",
        (titre, contenu, tags, _now()),
    )
    conn.commit()
    return _row(conn, "notes", cur.lastrowid)


def list_notes(conn) -> list[dict]:
    cur = conn.execute("SELECT * FROM notes ORDER BY id DESC")
    return [dict(r) for r in cur.fetchall()]


def search_notes(conn, query) -> list[dict]:
    like = f"%{query}%"
    cur = conn.execute(
        "SELECT * FROM notes WHERE titre LIKE ? OR contenu LIKE ? OR tags LIKE ? "
        "ORDER BY id DESC",
        (like, like, like),
    )
    return [dict(r) for r in cur.fetchall()]

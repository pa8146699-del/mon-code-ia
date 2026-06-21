#!/usr/bin/env python3
"""HackNotes CLI — carnet de notes de pirate, version terminal.

Jumeau en ligne de commande de l'app Kivy `hacknotes/main.py`, pensé pour tourner
**directement dans Termux/Kali** : 100% bibliothèque standard (zéro `pip`, zéro
`kivy`), même esprit que `dataguard/`. Même schéma SQLite que l'app graphique.

Base de données : `$HACKNOTES_DB` si défini, sinon `~/.hacknotes.db`
(persiste entre les sessions, indépendamment du dossier courant).

Usage :
    python notes_cli.py add "Titre" Categorie "Contenu..."
    python notes_cli.py list
    python notes_cli.py search <mot>
    python notes_cli.py view <id>
    python notes_cli.py edit <id> "Titre" Categorie "Contenu..."
    python notes_cli.py del <id>

Sans argument : affiche l'aide.
"""

import argparse
import os
import sqlite3
import sys
from datetime import datetime

SCHEMA = """
CREATE TABLE IF NOT EXISTS notes (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    title     TEXT NOT NULL,
    category  TEXT NOT NULL DEFAULT '',
    content   TEXT NOT NULL DEFAULT '',
    created   TEXT NOT NULL,
    updated   TEXT NOT NULL
);
"""

# Couleurs ANSI par catégorie (terminal). Reflètent CATEGORY_COLORS de main.py.
ANSI = {
    "Lab": "\033[92m",        # vert
    "Cible": "\033[91m",      # rouge/orange
    "Technique": "\033[94m",  # bleu
    "Recon": "\033[95m",      # magenta
    "Faille": "\033[91m",     # rouge
}
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"


def db_path():
    return os.environ.get("HACKNOTES_DB", os.path.expanduser("~/.hacknotes.db"))


def connect(path=None):
    conn = sqlite3.connect(path or db_path())
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    conn.commit()
    return conn


def _now():
    return datetime.now().isoformat(timespec="seconds")


def add_note(conn, title, category, content):
    cur = conn.execute(
        "INSERT INTO notes (title, category, content, created, updated) "
        "VALUES (?, ?, ?, ?, ?)",
        (title, category, content, _now(), _now()),
    )
    conn.commit()
    return cur.lastrowid


def update_note(conn, note_id, title, category, content):
    conn.execute(
        "UPDATE notes SET title=?, category=?, content=?, updated=? WHERE id=?",
        (title, category, content, _now(), note_id),
    )
    conn.commit()
    return conn.total_changes


def delete_note(conn, note_id):
    conn.execute("DELETE FROM notes WHERE id=?", (note_id,))
    conn.commit()
    return conn.total_changes


def get_note(conn, note_id):
    return conn.execute("SELECT * FROM notes WHERE id=?", (note_id,)).fetchone()


def list_notes(conn, query=""):
    query = (query or "").strip()
    if query:
        like = f"%{query}%"
        return conn.execute(
            "SELECT * FROM notes WHERE title LIKE ? OR category LIKE ? "
            "OR content LIKE ? ORDER BY updated DESC",
            (like, like, like),
        ).fetchall()
    return conn.execute("SELECT * FROM notes ORDER BY updated DESC").fetchall()


def _color(category):
    return ANSI.get((category or "").strip(), "\033[90m")


def _print_row(row):
    cat = row["category"] or "—"
    date = row["updated"].replace("T", " ")
    dot = f"{_color(cat)}●{RESET}"
    print(f"  {BOLD}[{row['id']}] {row['title']}{RESET}")
    print(f"      {dot} {cat}   {DIM}{date}{RESET}")


# --------------------------------------------------------------------------- #
#                              Commandes CLI                                   #
# --------------------------------------------------------------------------- #
def cmd_add(args):
    conn = connect()
    nid = add_note(conn, args.title, args.category, args.content)
    print(f"✅ Note #{nid} ajoutée.")


def cmd_list(args):
    conn = connect()
    rows = list_notes(conn)
    if not rows:
        print("Aucune note. Ajoute-en une : notes_cli.py add \"Titre\" Cat \"...\"")
        return
    print(f"\n🏴‍☠️  {len(rows)} note(s) :\n")
    for row in rows:
        _print_row(row)
    print()


def cmd_search(args):
    conn = connect()
    rows = list_notes(conn, args.query)
    if not rows:
        print(f"Aucun résultat pour « {args.query} ».")
        return
    print(f"\n🔍 {len(rows)} résultat(s) pour « {args.query} » :\n")
    for row in rows:
        _print_row(row)
    print()


def cmd_view(args):
    conn = connect()
    row = get_note(conn, args.id)
    if row is None:
        print(f"❌ Note #{args.id} introuvable.")
        return
    cat = row["category"] or "—"
    print()
    print(f"{BOLD}{row['title']}{RESET}")
    print(f"{_color(cat)}● {cat}{RESET}   {DIM}créée {row['created']} · maj {row['updated']}{RESET}")
    print("-" * 50)
    print(row["content"] or "(vide)")
    print()


def cmd_edit(args):
    conn = connect()
    if get_note(conn, args.id) is None:
        print(f"❌ Note #{args.id} introuvable.")
        return
    update_note(conn, args.id, args.title, args.category, args.content)
    print(f"✅ Note #{args.id} mise à jour.")


def cmd_del(args):
    conn = connect()
    if delete_note(conn, args.id):
        print(f"🗑  Note #{args.id} supprimée.")
    else:
        print(f"❌ Note #{args.id} introuvable.")


def build_parser():
    p = argparse.ArgumentParser(
        prog="notes_cli.py",
        description="HackNotes CLI — carnet de notes de pirate (terminal, stdlib).",
    )
    sub = p.add_subparsers(dest="cmd")

    a = sub.add_parser("add", help="ajouter une note")
    a.add_argument("title")
    a.add_argument("category")
    a.add_argument("content")
    a.set_defaults(func=cmd_add)

    li = sub.add_parser("list", help="lister toutes les notes")
    li.set_defaults(func=cmd_list)

    s = sub.add_parser("search", help="rechercher dans les notes")
    s.add_argument("query")
    s.set_defaults(func=cmd_search)

    v = sub.add_parser("view", help="afficher une note en entier")
    v.add_argument("id", type=int)
    v.set_defaults(func=cmd_view)

    e = sub.add_parser("edit", help="modifier une note")
    e.add_argument("id", type=int)
    e.add_argument("title")
    e.add_argument("category")
    e.add_argument("content")
    e.set_defaults(func=cmd_edit)

    d = sub.add_parser("del", help="supprimer une note")
    d.add_argument("id", type=int)
    d.set_defaults(func=cmd_del)

    return p


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "func", None):
        parser.print_help()
        return
    args.func(args)


if __name__ == "__main__":
    main()

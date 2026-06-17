#!/usr/bin/env python3
"""Tests pour AgentOS. Lancer avec : python -m pytest agentos/

Fonctionne aussi sans pytest : python agentos/test_agentos.py

Ces tests n'appellent jamais l'API Claude : ils valident la base SQLite et le
dispatch des outils directement. La synchro Notion est un no-op sans config.
"""

import json
from pathlib import Path

import db
import tools


def _fresh_db(tmp_path: Path):
    return db.connect(tmp_path / "test.db")


# --- Base de données -------------------------------------------------------

def test_add_et_list_client(tmp_path: Path):
    conn = _fresh_db(tmp_path)
    row = db.add_client(conn, "Dupont SARL", email="contact@dupont.fr")
    assert row["id"] == 1
    assert row["nom"] == "Dupont SARL"
    assert row["statut"] == "prospect"
    assert len(db.list_clients(conn)) == 1


def test_update_client(tmp_path: Path):
    conn = _fresh_db(tmp_path)
    db.add_client(conn, "ACME")
    updated = db.update_client(conn, 1, statut="actif")
    assert updated["statut"] == "actif"


def test_filtre_client_par_statut(tmp_path: Path):
    conn = _fresh_db(tmp_path)
    db.add_client(conn, "A", statut="actif")
    db.add_client(conn, "B", statut="prospect")
    assert len(db.list_clients(conn, statut="actif")) == 1


def test_projet_et_tache(tmp_path: Path):
    conn = _fresh_db(tmp_path)
    projet = db.add_projet(conn, "Site web", description="refonte")
    tache = db.add_tache(conn, "Maquette", projet_id=projet["id"])
    assert tache["projet_id"] == projet["id"]
    assert db.list_taches(conn)[0]["statut"] == "à faire"


def test_finance_summary(tmp_path: Path):
    conn = _fresh_db(tmp_path)
    db.add_finance(conn, "revenu", 1000, categorie="vente")
    db.add_finance(conn, "depense", 300, categorie="logiciel")
    db.add_finance(conn, "depense", 200, categorie="logiciel")
    resume = db.finance_summary(conn)
    assert resume["revenus"] == 1000
    assert resume["depenses"] == 500
    assert resume["solde"] == 500
    assert resume["depenses_par_categorie"]["logiciel"] == 500


def test_search_notes(tmp_path: Path):
    conn = _fresh_db(tmp_path)
    db.add_note(conn, "Réunion", "Discuter du budget marketing", tags="pro")
    db.add_note(conn, "Idée", "Application mobile", tags="perso")
    trouve = db.search_notes(conn, "budget")
    assert len(trouve) == 1
    assert trouve[0]["titre"] == "Réunion"


# --- Dispatch des outils (sans Claude) -------------------------------------

def test_dispatch_add_finance(tmp_path: Path):
    conn = _fresh_db(tmp_path)
    out = tools.dispatch(conn, "add_finance", {"type": "depense", "montant": 42.5, "categorie": "repas"})
    data = json.loads(out)
    assert data["montant"] == 42.5
    assert data["categorie"] == "repas"


def test_dispatch_finance_summary(tmp_path: Path):
    conn = _fresh_db(tmp_path)
    tools.dispatch(conn, "add_finance", {"type": "revenu", "montant": 500})
    out = tools.dispatch(conn, "finance_summary", {})
    assert json.loads(out)["revenus"] == 500


def test_dispatch_update_tache(tmp_path: Path):
    conn = _fresh_db(tmp_path)
    tools.dispatch(conn, "add_tache", {"titre": "Appeler client"})
    out = tools.dispatch(conn, "update_tache", {"tache_id": 1, "statut": "terminé"})
    assert json.loads(out)["statut"] == "terminé"


def test_dispatch_outil_inconnu(tmp_path: Path):
    conn = _fresh_db(tmp_path)
    out = tools.dispatch(conn, "outil_bidon", {})
    assert "erreur" in json.loads(out)


def test_dispatch_erreur_remontee(tmp_path: Path):
    conn = _fresh_db(tmp_path)
    # type invalide -> contrainte CHECK SQLite -> erreur renvoyée, pas de crash.
    out = tools.dispatch(conn, "add_finance", {"type": "xxx", "montant": 1})
    assert "erreur" in json.loads(out)


if __name__ == "__main__":
    import tempfile

    passed = 0
    failed = 0
    for name, fn in sorted(globals().items()):
        if not name.startswith("test_") or not callable(fn):
            continue
        try:
            if "tmp_path" in fn.__code__.co_varnames:
                with tempfile.TemporaryDirectory() as d:
                    fn(Path(d))
            else:
                fn()
            passed += 1
            print(f"✓ {name}")
        except AssertionError as e:
            failed += 1
            print(f"✗ {name} : {e}")

    print(f"\n{passed} réussi(s), {failed} échec(s)")
    raise SystemExit(1 if failed else 0)

#!/usr/bin/env python3
"""Tests pour MonIA. Lancer avec : python -m pytest monia/

Fonctionne aussi sans pytest : python monia/test_monia.py

Ces tests sont 100 % stdlib et n'appellent aucun service externe : ils valident
directement le réseau de neurones maison (`reseau.py`).
"""

from pathlib import Path

from reseau import ACTIVATIONS, Reseau


# --- Construction et passe avant -------------------------------------------

def test_formes_des_poids():
    ia = Reseau([2, 4, 1], seed=0)
    assert [len(W) for W in ia.poids] == [4, 1]          # neurones par couche
    assert [len(W[0]) for W in ia.poids] == [2, 4]        # entrées par couche
    assert [len(b) for b in ia.biais] == [4, 1]


def test_predire_renvoie_la_bonne_taille():
    ia = Reseau([3, 5, 2], seed=0)
    sortie = ia.predire([0.1, 0.2, 0.3])
    assert len(sortie) == 2


def test_seed_reproductible():
    a = Reseau([2, 3, 1], seed=42)
    b = Reseau([2, 3, 1], seed=42)
    assert a.poids == b.poids and a.biais == b.biais


def test_activation_inconnue_leve():
    erreur = False
    try:
        Reseau([1, 1], activation="bidon")
    except ValueError:
        erreur = True
    assert erreur


def test_derivees_activations():
    # Sigmoïde : f(0)=0.5, f'(0)=0.25 ; tanh : f(0)=0, f'(0)=1 ; identité : f'=1.
    f_sig, df_sig = ACTIVATIONS["sigmoide"]
    assert abs(f_sig(0) - 0.5) < 1e-9
    assert abs(df_sig(0) - 0.25) < 1e-9
    _, df_id = ACTIVATIONS["identite"]
    assert df_id(123) == 1.0


# --- Apprentissage ----------------------------------------------------------

def test_apprend_fonction_lineaire():
    # Doit retrouver y = 2x : poids -> 2, biais -> 0.
    donnees = [([x], [2 * x]) for x in range(-5, 6)]
    ia = Reseau([1, 1], sortie="identite", seed=0)
    ia.entrainer(donnees, epochs=1000, taux=0.01)
    assert abs(ia.poids[0][0][0] - 2.0) < 1e-3
    assert abs(ia.predire([10])[0] - 20.0) < 1e-2


def test_erreur_diminue():
    donnees = [([x], [2 * x]) for x in range(-5, 6)]
    ia = Reseau([1, 1], sortie="identite", seed=0)
    historique = ia.entrainer(donnees, epochs=200, taux=0.01)
    assert historique[-1] < historique[0]


def test_apprend_xor_non_lineaire():
    # Le XOR est hors de portée d'un neurone unique : prouve l'intérêt des couches.
    donnees = [([0, 0], [0]), ([0, 1], [1]), ([1, 0], [1]), ([1, 1], [0])]
    ia = Reseau([2, 4, 1], activation="tanh", sortie="sigmoide", seed=1)
    ia.entrainer(donnees, epochs=3000, taux=0.5)
    for entree, attendu in donnees:
        assert round(ia.predire(entree)[0]) == attendu[0]


# --- Mémoire persistante ----------------------------------------------------

def test_sauvegarder_et_charger(tmp_path: Path):
    donnees = [([x], [2 * x]) for x in range(-5, 6)]
    ia = Reseau([1, 1], sortie="identite", seed=0)
    ia.entrainer(donnees, epochs=500, taux=0.01)
    chemin = tmp_path / "memoire.json"
    ia.sauvegarder(chemin)

    rechargee = Reseau.charger(chemin)
    assert rechargee.predire([7]) == ia.predire([7])


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

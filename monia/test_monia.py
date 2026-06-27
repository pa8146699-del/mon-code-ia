#!/usr/bin/env python3
"""Tests pour MonIA. Lancer avec : python -m pytest monia/

Fonctionne aussi sans pytest : python monia/test_monia.py

Ces tests sont 100 % stdlib et n'appellent aucun service externe : ils valident
directement le réseau de neurones maison (`reseau.py`).
"""

import os
from pathlib import Path

from discussion import Discussion, mots
from ecrivain import Ecrivain, jetons
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


# --- Chatbot (leçon 5) ------------------------------------------------------

def test_mots_decoupe_et_minuscule():
    assert mots("Bonjour, ça VA ?") == ["bonjour", "ça", "va"]


def test_chatbot_repond_a_ce_qu_il_a_appris():
    paires = [
        ("bonjour", "Salut !"),
        ("salut", "Salut !"),
        ("au revoir", "À bientôt."),
        ("quel est ton nom", "Je m'appelle MonIA."),
    ]
    chat = Discussion(paires, seed=0)
    chat.entrainer(epochs=3000, taux=0.3)
    assert chat.repondre("bonjour") == "Salut !"
    assert chat.repondre("quel est ton nom") == "Je m'appelle MonIA."


def test_chatbot_avoue_ne_pas_savoir():
    chat = Discussion([("bonjour", "Salut !")], seed=0)
    chat.entrainer(epochs=1000, taux=0.3)
    # Une question dont aucun mot n'est connu du vocabulaire.
    assert "ne sais pas" in chat.repondre("xyzzy plugh").lower()


def test_chatbot_lister_et_oublier():
    paires = [("bonjour", "Salut !"), ("au revoir", "À bientôt."), ("merci", "De rien.")]
    chat = Discussion(paires, seed=0)
    chat.entrainer(epochs=500, taux=0.3)
    assert len(chat.lister()) == 3

    assert chat.oublier("merci") == 1            # un couple supprimé
    assert len(chat.lister()) == 2
    assert chat.oublier("inexistant") == 0       # rien à oublier
    chat.oublier("au revoir")
    assert chat.oublier("bonjour") == -1         # refuse de tout vider
    assert len(chat.lister()) == 1


def test_chatbot_apprend_en_direct():
    # Enseignement à la volée : une nouvelle paire, et elle sait répondre.
    chat = Discussion([("bonjour", "Salut !")], seed=0)
    chat.entrainer(epochs=1000, taux=0.3)
    assert "ne sais pas" in chat.repondre("la capitale de la france").lower()
    chat.apprendre("quelle est la capitale de la France", "Paris")
    assert chat.repondre("la capitale de la france ?") == "Paris"


def test_chatbot_sauvegarder_et_charger(tmp_path: Path):
    paires = [("bonjour", "Salut !"), ("au revoir", "À bientôt.")]
    chat = Discussion(paires, seed=0)
    chat.entrainer(epochs=2000, taux=0.3)
    chemin = tmp_path / "chat.json"
    chat.sauvegarder(chemin)

    rechargee = Discussion.charger(chemin)
    assert rechargee.repondre("bonjour") == chat.repondre("bonjour")


# --- Générateur de texte (leçon 6) ------------------------------------------

def test_jetons_separe_mots_et_ponctuation():
    assert jetons("Bonjour, le monde !") == ["bonjour", ",", "le", "monde", "!"]


def test_ecrivain_apprend_le_vocabulaire():
    ec = Ecrivain(ordre=2)
    ec.apprendre_texte("le chat dort. le chien court. le chat court.")
    # mots distincts : le, chat, dort, ., chien, court  -> 6
    assert ec.vocabulaire() == 6


def test_ecrivain_genere_du_texte_appris():
    ec = Ecrivain(ordre=1)
    ec.apprendre_texte("le chat mange la souris.")
    texte = ec.generer(amorce="le", nb_mots=5, seed=0)
    assert len(texte) > 0
    # Chaque mot produit fait partie du vocabulaire du texte appris.
    for mot in jetons(texte):
        assert mot in ec._mots


def test_ecrivain_sauvegarder_et_charger(tmp_path: Path):
    ec = Ecrivain(ordre=2)
    ec.apprendre_texte("maître corbeau sur un arbre perché tenait un fromage.")
    chemin = tmp_path / "ecrivain.json"
    ec.sauvegarder(chemin)
    recharge = Ecrivain.charger(chemin)
    assert recharge.vocabulaire() == ec.vocabulaire()
    assert recharge.generer(seed=1) == ec.generer(seed=1)


# --- Assistant de code Python (leçon 7) -------------------------------------

def test_codeur_base_de_connaissances():
    import codeur

    assert len(codeur.CONNAISSANCES_CODE) >= 10
    for question, code in codeur.CONNAISSANCES_CODE:
        assert isinstance(question, str) and question
        assert isinstance(code, str) and code


def test_codeur_repond_avec_du_code():
    # L'assistant de code n'est qu'un Discussion avec des réponses = du Python.
    import codeur

    assistant = Discussion(codeur.CONNAISSANCES_CODE[:6], cachees=16, seed=0)
    assistant.entrainer(epochs=2000, taux=0.3)
    assert "print" in assistant.repondre("comment afficher du texte")


# --- Dépanneur de commandes (leçon 8) ---------------------------------------

def test_commandes_base_valide():
    import commandes

    assert len(commandes.COMMANDES) >= 15
    for question, commande in commandes.COMMANDES:
        assert isinstance(question, str) and question
        assert isinstance(commande, str) and commande


def test_commandes_donne_la_bonne_commande():
    import commandes

    aide = Discussion(commandes.COMMANDES, cachees=16, seed=0)
    aide.entrainer(epochs=2000, taux=0.3)
    assert aide.repondre("comment voir mes fichiers").startswith("ls")


# --- Assistant GitHub (leçon 9) ---------------------------------------------

def test_github_base_valide():
    import github

    assert len(github.CONNAISSANCES_GITHUB) >= 15
    for question, reponse in github.CONNAISSANCES_GITHUB:
        assert isinstance(question, str) and question
        assert isinstance(reponse, str) and reponse


def test_github_explique_le_clonage():
    import github

    gh = Discussion(github.CONNAISSANCES_GITHUB, cachees=16, seed=0)
    gh.entrainer(epochs=2000, taux=0.3)
    assert "git clone" in gh.repondre("comment cloner mon projet")


# --- Menu principal (leçon 0) -----------------------------------------------

def test_cyber_base_valide():
    import cyber

    assert len(cyber.CONNAISSANCES_CYBER) >= 15
    for question, explication in cyber.CONNAISSANCES_CYBER:
        assert isinstance(question, str) and question
        assert isinstance(explication, str) and explication


def test_cyber_explique_le_phishing():
    import cyber

    assistant = Discussion(cyber.CONNAISSANCES_CYBER, cachees=20, seed=0)
    assistant.entrainer(epochs=2000, taux=0.3)
    assert "phishing" in assistant.repondre("c'est quoi le phishing").lower()


def test_failles_base_valide():
    import failles

    assert len(failles.CONNAISSANCES_FAILLES) >= 15
    for question, explication in failles.CONNAISSANCES_FAILLES:
        assert isinstance(question, str) and question
        assert isinstance(explication, str) and explication


def test_failles_explique_l_injection_sql():
    import failles

    assistant = Discussion(failles.CONNAISSANCES_FAILLES, cachees=20, seed=0)
    assistant.entrainer(epochs=2000, taux=0.3)
    assert "sql" in assistant.repondre("c'est quoi l'injection sql").lower()


def test_analyseur_trouve_des_failles():
    import analyseur

    code = (
        'password = "secret123"\n'
        'os.system("rm " + x)\n'
        "h = hashlib.md5(p).hexdigest()\n"
    )
    noms = {t["nom"] for t in analyseur.analyser_texte(code)}
    assert "Secret en clair" in noms
    assert "Commande shell (os.system/popen)" in noms
    assert "Hachage faible (md5/sha1)" in noms


def test_analyseur_masque_les_secrets():
    import analyseur

    trouvailles = analyseur.analyser_texte('api_key = "sk-tres-secret-12345"')
    secret = [t for t in trouvailles if t["nom"] == "Secret en clair"][0]
    assert "sk-tres-secret-12345" not in secret["extrait"]
    assert "***" in secret["extrait"]


def test_analyseur_code_propre_sans_alerte():
    import analyseur

    code = "x = 2 + 2\nprint('Bonjour')\n"
    assert analyseur.analyser_texte(code) == []


def test_analyseur_dossier(tmp_path: Path):
    import analyseur

    (tmp_path / "sale.py").write_text('password = "secret123"\n', encoding="utf-8")
    (tmp_path / "propre.py").write_text("x = 1 + 1\n", encoding="utf-8")
    resultats = analyseur.analyser_dossier(str(tmp_path))
    fichiers = {os.path.basename(c) for c in resultats}
    assert "sale.py" in fichiers
    assert "propre.py" not in fichiers


def test_menu_pointe_vers_des_fichiers_existants():
    import monia

    dossier = os.path.dirname(monia.__file__)
    for _, fichier in monia.LECONS.values():
        assert os.path.exists(os.path.join(dossier, fichier)), fichier


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

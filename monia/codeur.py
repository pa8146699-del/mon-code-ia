#!/usr/bin/env python3
"""Leçon 7 — Apprendre à coder : un assistant qui donne des commandes Python.

C'est le chatbot de `discussion.py` (réseau de neurones + sac de mots) mais avec
une base de connaissances spéciale : à chaque question en français correspond un
**bout de code Python**. Tu demandes « comment afficher du texte ? », il répond
`print("ton texte")`.

Comme le chatbot, il comprend les reformulations et avoue quand il ne sait pas.
Tu peux lui apprendre tes propres recettes en direct (voir plus bas), et il
retient tout dans `codeur.json`.

⚠️ Honnêteté : il ne « comprend » pas la programmation, il restitue les recettes
qu'on lui a apprises. Mais ça fait un super aide-mémoire Python de poche, qui
grandit avec toi.

Lancer :  python3 codeur.py
"""

import os

from discussion import Discussion

FICHIER = os.path.join(os.path.dirname(__file__), "codeur.json")

# On apprend en direct avec ">>>" (et pas "=") parce que le code contient
# souvent un "=", par exemple  x = 5.
SEPARATEUR = ">>>"

AIDE = (
    "Pose ta question en français, je réponds en Python.\n"
    "  exemples :  comment afficher du texte ?   |   comment faire une boucle ?\n"
    "Pour m'apprendre une recette :  apprends: ta question " + SEPARATEUR + " ton code\n"
    "  exemple :  apprends: comment dire bonjour " + SEPARATEUR + " print('Bonjour')\n"
    "Autres :  aide   |   quitter"
)

# Recettes Python de départ (question en français -> code Python).
CONNAISSANCES_CODE = [
    ("comment afficher du texte", 'print("Bonjour")'),
    ("comment écrire un message à l'écran", 'print("Bonjour")'),
    ("comment créer une variable", "x = 5"),
    ("comment ranger une valeur dans une variable", "x = 5"),
    ("comment demander quelque chose à l'utilisateur", 'nom = input("Ton nom : ")'),
    ("comment lire ce que tape l'utilisateur", 'nom = input("Ton nom : ")'),
    ("comment faire une boucle qui répète", "for i in range(10):\n    print(i)"),
    ("comment répéter dix fois", "for i in range(10):\n    print(i)"),
    ("comment faire une boucle tant que", "while x < 10:\n    x = x + 1"),
    ("comment tester une condition si", 'if age >= 18:\n    print("majeur")'),
    ("comment faire un sinon", 'if age >= 18:\n    print("majeur")\nelse:\n    print("mineur")'),
    ("comment créer une fonction", 'def saluer():\n    print("Salut")'),
    ("comment créer une liste", 'fruits = ["pomme", "banane"]'),
    ("comment ajouter un élément à une liste", 'fruits.append("kiwi")'),
    ("comment connaître la taille d'une liste", "len(fruits)"),
    ("comment tirer un nombre au hasard", "import random\nrandom.randint(1, 100)"),
    ("comment additionner deux nombres", "resultat = 2 + 3"),
    ("comment transformer du texte en nombre", 'nombre = int("5")'),
    ("comment importer un module", "import math"),
    ("comment calculer une racine carrée", "import math\nmath.sqrt(16)"),
    ("comment écrire un commentaire", "# ceci est un commentaire"),
    ("comment arrondir un nombre", "round(3.14159, 2)"),
    ("comment mettre du texte en majuscules", '"salut".upper()'),
    ("comment ouvrir un fichier", 'contenu = open("fichier.txt").read()'),
]


def _afficher_code(code):
    """Affiche un bout de code, lisiblement, encadré."""
    print("MonIA (Python) :")
    for ligne in code.split("\n"):
        print("    " + ligne)


if __name__ == "__main__":
    if os.path.exists(FICHIER):
        codeur = Discussion.charger(FICHIER)
        print("J'ai rechargé toutes les recettes que tu m'as apprises. 🧠")
    else:
        print("J'apprends mes recettes Python de départ...")
        codeur = Discussion(CONNAISSANCES_CODE, cachees=16, seed=0)
        codeur.entrainer(epochs=4000, taux=0.3)
        codeur.sauvegarder(FICHIER)

    print("Prêt ! " + AIDE + "\n")

    while True:
        try:
            phrase = input("Toi : ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nMonIA : Au revoir !")
            break

        if phrase.lower() in {"quitter", "stop", "exit", "quit"}:
            print("MonIA : Au revoir !")
            break
        if not phrase:
            continue
        if phrase.lower() in {"aide", "help", "?"}:
            print("MonIA :\n" + AIDE)
            continue

        if phrase.lower().startswith("apprends"):
            corps = phrase.split(":", 1)[1] if ":" in phrase else ""
            if SEPARATEUR not in corps:
                print(f"MonIA : Écris :  apprends: ta question {SEPARATEUR} ton code")
                continue
            question, code = corps.split(SEPARATEUR, 1)
            question, code = question.strip(), code.strip()
            if not question or not code:
                print("MonIA : Il me faut une question ET du code.")
                continue
            codeur.apprendre(question, code)
            codeur.sauvegarder(FICHIER)
            print(f"MonIA : Recette apprise ! « {question} »")
            continue

        reponse = codeur.repondre(phrase)
        if "ne sais pas" in reponse.lower():
            print("MonIA : " + reponse)
        else:
            _afficher_code(reponse)

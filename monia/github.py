#!/usr/bin/env python3
"""Leçon 9 — Connaître GitHub : cloner, envoyer, branches, tokens, pull requests.

GitHub, c'est le site où vit ton projet `mon-code-ia` : une copie en ligne de ton
code, son historique, et un endroit pour le partager et le sauvegarder. Cet
assistant répond à tes questions sur GitHub — soit par une **commande**, soit par
une **explication courte**.

Même moteur que le chatbot (`discussion.py`) : réseau de neurones + sac de mots.
Il comprend les reformulations, avoue quand il ne sait pas, apprend tes astuces
en direct et retient tout dans `github.json`.

Lancer :  python3 github.py
"""

import os
import re

from discussion import Discussion

FICHIER = os.path.join(os.path.dirname(__file__), "github.json")
SEPARATEUR = ">>>"

# Ton dépôt, pour que les exemples soient les tiens.
DEPOT = "https://github.com/pa8146699-del/mon-code-ia"

AIDE = (
    "Pose ta question sur GitHub, je réponds par une commande ou une explication.\n"
    "  exemples :  comment cloner mon projet ?  |  c'est quoi une pull request ?\n"
    "M'apprendre une astuce :  apprends: ta question " + SEPARATEUR + " ta réponse\n"
    "Autres :  aide   |   quitter"
)

# Les réponses « commande » commencent par une vraie commande ; les réponses
# « explication » sont du texte. On les affiche différemment.
CONNAISSANCES_GITHUB = [
    ("c'est quoi github", "GitHub est un site qui héberge ton code en ligne : une copie de ton projet, son historique, et un moyen de le partager et de le sauvegarder."),
    ("comment cloner mon projet", f"git clone {DEPOT}.git\n(télécharge tout le projet sur ton téléphone)"),
    ("comment télécharger le projet depuis github", f"git clone {DEPOT}.git\n(copie le projet en local)"),
    ("comment récupérer les nouveautés", "git pull\n(récupère les derniers changements depuis GitHub)"),
    ("comment envoyer mon code sur github", 'git add . && git commit -m "mon message" && git push\n(enregistre puis envoie ton code)'),
    ("comment sauvegarder mon travail en ligne", 'git add . && git commit -m "mon message" && git push\n(envoie ton travail sur GitHub)'),
    ("comment voir mon projet en ligne", f"Ouvre cette adresse dans ton navigateur :\n{DEPOT}"),
    ("comment voir mes branches", "git branch\n(liste les branches du projet)"),
    ("comment changer de branche", "git checkout nom_de_la_branche\n(bascule sur une autre branche)"),
    ("comment créer une nouvelle branche", "git checkout -b nom_de_la_branche\n(crée une branche et passe dessus)"),
    ("comment voir l'historique des changements", "git log --oneline\n(affiche la liste des commits)"),
    ("comment annuler mes changements non envoyés", "git checkout -- nom_du_fichier\n(remet le fichier comme avant, attention)"),
    ("comment me connecter à github", "GitHub n'accepte plus le mot de passe : crée un jeton (token) sur github.com, dans Settings > Developer settings > Personal access tokens, et utilise-le comme mot de passe au moment du git push."),
    ("c'est quoi un token", "Un token (jeton) est un mot de passe spécial pour GitHub. Tu le crées dans tes réglages GitHub et tu t'en sers à la place de ton mot de passe pour pousser ton code."),
    ("c'est quoi un commit", "Un commit est une photo de ton code à un instant donné, avec un message qui décrit ce que tu as changé."),
    ("c'est quoi un push", "Pousser (push), c'est envoyer tes commits depuis ton téléphone vers GitHub."),
    ("c'est quoi un pull", "Tirer (pull), c'est récupérer sur ton téléphone les changements qui sont sur GitHub."),
    ("c'est quoi une pull request", "Une pull request propose de fusionner les changements d'une branche dans une autre ; on la crée et on la relit sur le site github.com."),
    ("c'est quoi un dépôt", "Un dépôt (repository) est le dossier de ton projet sur GitHub, avec tout son code et son historique."),
    ("comment créer un dépôt", "Sur github.com, clique sur le bouton 'New' (ou le +) en haut à droite, donne un nom, puis valide."),
    ("comment voir l'état de mes fichiers", "git status\n(montre ce qui a changé et ce qui sera envoyé)"),
    ("comment ignorer des fichiers", "Ajoute leur nom dans un fichier nommé .gitignore\n(git ne les enverra plus sur GitHub)"),
]

# Mots qui indiquent que la réponse est une commande à taper.
_DEBUTS_COMMANDE = ("git ", "cd ", "ls", "pip ", "nano ", "python3 ")


def _afficher(reponse):
    lignes = reponse.split("\n")
    premiere = lignes[0]
    if premiere.startswith(_DEBUTS_COMMANDE):
        print("MonIA — la commande :")
        print("    $ " + premiere)
        for reste in lignes[1:]:
            print("    " + reste)
    else:
        print("MonIA : " + reponse)


if __name__ == "__main__":
    if os.path.exists(FICHIER):
        gh = Discussion.charger(FICHIER)
        print("J'ai rechargé tout ce que je sais sur GitHub. 🧠")
    else:
        print("Je révise GitHub...")
        gh = Discussion(CONNAISSANCES_GITHUB, cachees=16, seed=0)
        gh.entrainer(epochs=4000, taux=0.3)
        gh.sauvegarder(FICHIER)

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
                print(f"MonIA : Écris :  apprends: ta question {SEPARATEUR} ta réponse")
                continue
            question, reponse = corps.split(SEPARATEUR, 1)
            question, reponse = question.strip(), reponse.strip()
            if not question or not reponse:
                print("MonIA : Il me faut une question ET une réponse.")
                continue
            gh.apprendre(question, reponse)
            gh.sauvegarder(FICHIER)
            print(f"MonIA : Appris ! « {question} »")
            continue

        reponse = gh.repondre(phrase)
        if "ne sais pas" in reponse.lower():
            print("MonIA : " + reponse)
        else:
            _afficher(reponse)

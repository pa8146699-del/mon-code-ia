#!/usr/bin/env python3
"""Leçon 8 — Le dépanneur : les bonnes commandes quand tu bloques.

Quand tu es perdu dans le terminal (Termux / Linux / git / Python), demande-lui
en français « comment je fais pour... » et il te donne **la commande exacte**,
avec une petite explication.

C'est le chatbot de `discussion.py` (réseau de neurones + sac de mots) avec une
base de connaissances remplie des commandes que tu utilises vraiment. Il
comprend les reformulations, avoue quand il ne sait pas, apprend tes propres
astuces en direct et retient tout dans `commandes.json`.

Lancer :  python3 commandes.py
"""

import os

from discussion import Discussion, boucle

FICHIER = os.path.join(os.path.dirname(__file__), "commandes.json")
SEPARATEUR = ">>>"

AIDE = (
    "Dis-moi ce que tu veux faire, je te donne la commande.\n"
    "  exemples :  comment voir mes fichiers ?  |  comment récupérer le code ?\n"
    "M'apprendre une astuce :  apprends: ce que je veux faire " + SEPARATEUR + " la commande\n"
    "Autres :  aide   |   quitter"
)

# Chaque réponse = la commande, puis (à la ligne) une courte explication.
COMMANDES = [
    # --- Se repérer et se déplacer dans les dossiers ---
    ("comment voir mes fichiers", "ls\n(affiche les fichiers du dossier courant)"),
    ("comment savoir où je suis", "pwd\n(affiche le chemin du dossier courant)"),
    ("comment changer de dossier", "cd nom_du_dossier\n(entre dans un dossier)"),
    ("comment revenir en arrière", "cd ..\n(remonte d'un dossier)"),
    ("comment aller au dossier principal", "cd ~\n(retourne à ton dossier d'accueil)"),
    ("comment créer un dossier", "mkdir nom_du_dossier\n(crée un nouveau dossier)"),
    # --- Fichiers ---
    ("comment créer ou modifier un fichier", "nano fichier.py\n(ouvre l'éditeur nano)"),
    ("comment sauvegarder dans nano", "Ctrl+O puis Entrée\n(O comme 'Output')"),
    ("comment quitter nano", "Ctrl+X\n(ferme l'éditeur nano)"),
    ("comment voir le contenu d'un fichier", "cat fichier.py\n(affiche tout le fichier)"),
    ("comment supprimer un fichier", "rm fichier\n(efface un fichier, attention c'est définitif)"),
    ("comment copier un fichier", "cp source destination\n(copie un fichier)"),
    ("comment renommer ou déplacer un fichier", "mv ancien nouveau\n(déplace ou renomme)"),
    # --- git (récupérer / envoyer le code) ---
    ("comment récupérer la dernière version du code", "git pull\n(télécharge les nouveautés du projet)"),
    ("comment mettre à jour mon ia", "cd ~/mon-code-ia && git pull\n(récupère mes dernières améliorations)"),
    ("comment voir l'état de mes changements", "git status\n(montre ce qui a changé)"),
    ("comment envoyer mes changements", 'git add . && git commit -m "mon message" && git push\n(enregistre et envoie ton code)'),
    ("comment télécharger le projet", "git clone <adresse>\n(copie le projet sur ton téléphone)"),
    # --- Python ---
    ("comment lancer un programme python", "python3 fichier.py\n(exécute un script Python)"),
    ("comment installer un paquet python", "pip install nom_du_paquet\n(installe une bibliothèque)"),
    ("comment arrêter un programme", "Ctrl+C\n(interrompt le programme en cours)"),
    ("comment quitter python", "exit()\n(ou Ctrl+D pour sortir de l'interpréteur)"),
    # --- Termux / Debian ---
    ("comment installer un programme", "apt install nom\n(installe un logiciel sous Debian/Termux)"),
    ("comment mettre à jour le système", "apt update && apt upgrade\n(met tout à jour)"),
    # --- Lancer ton IA ---
    ("comment discuter avec mon ia", "cd ~/mon-code-ia/monia && python3 discussion.py\n(ouvre le chatbot)"),
    ("comment lancer l'écrivain", "cd ~/mon-code-ia/monia && python3 ecrivain.py\n(le générateur de texte)"),
    ("comment lancer les tests", "cd ~/mon-code-ia/monia && python3 test_monia.py\n(vérifie que tout marche)"),
    # --- Reformulations (mêmes réponses, pour mieux te comprendre) ---
    ("comment récupérer le code", "git pull\n(télécharge les nouveautés du projet)"),
    ("comment télécharger les nouveautés", "git pull\n(télécharge les nouveautés du projet)"),
    ("comment voir les fichiers du dossier", "ls\n(affiche les fichiers du dossier courant)"),
    ("comment sortir de nano", "Ctrl+X\n(ferme l'éditeur nano)"),
    ("comment lancer mon ia", "cd ~/mon-code-ia/monia && python3 discussion.py\n(ouvre le chatbot)"),
    ("comment exécuter un script", "python3 fichier.py\n(exécute un script Python)"),
]


def _afficher(reponse):
    """Affiche la commande (1re ligne) et son explication (le reste)."""
    if "ne sais pas" in reponse.lower():
        print("MonIA : " + reponse)
        return
    lignes = reponse.split("\n")
    print("MonIA — la commande :")
    print("    $ " + lignes[0])
    for explication in lignes[1:]:
        print("    " + explication)


if __name__ == "__main__":
    import sys

    voix = "voix" in sys.argv

    if os.path.exists(FICHIER):
        helper = Discussion.charger(FICHIER)
        print("J'ai rechargé toutes les commandes que je connais. 🧠")
    else:
        print("Je révise les commandes utiles...")
        helper = Discussion(COMMANDES, cachees=16, seed=0)
        helper.entrainer(epochs=4000, taux=0.3)
        helper.sauvegarder(FICHIER)

    boucle(helper, FICHIER, separateur=SEPARATEUR, afficher=_afficher, aide=AIDE, voix=voix)

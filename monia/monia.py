#!/usr/bin/env python3
"""MonIA — le menu principal : lance n'importe quelle leçon depuis un seul écran.

Plus besoin de retenir tous les noms de fichiers : tape un numéro, et l'outil
correspondant se lance. Quand tu le quittes, tu reviens au menu.

Lancer :  python3 monia.py
"""

import os
import subprocess
import sys

DOSSIER = os.path.dirname(os.path.abspath(__file__))

# numéro -> (description, fichier à lancer)
LECONS = {
    # Les assistants (pose des questions, il répond)
    "1": ("Discuter avec ton IA", "discussion.py"),
    "2": ("Écrire un texte (style d'un livre)", "ecrivain.py"),
    "3": ("Coder en Python", "codeur.py"),
    "4": ("Dépanner le terminal", "commandes.py"),
    "5": ("Tout savoir sur GitHub", "github.py"),
    "6": ("Cybersécurité", "cyber.py"),
    "7": ("Failles (vulnérabilités)", "failles.py"),
    # Les leçons (comprendre comment l'IA fonctionne)
    "8": ("Leçon : le neurone", "cerveau.py"),
    "9": ("Leçon : apprendre y = 2x", "apprentissage.py"),
    "10": ("Leçon : s'entraîner (epochs)", "entrainement.py"),
    "11": ("Leçon : la mémoire", "memoire.py"),
    "12": ("Leçon : le réseau (XOR)", "reseau.py"),
    # Vérifier que tout marche
    "t": ("Lancer les tests", "test_monia.py"),
}


def afficher_menu():
    print("\n=== MonIA — ton IA 100% maison ===")
    print("  Les assistants (pose des questions) :")
    print("    1) Discuter            2) Écrire un texte")
    print("    3) Coder en Python     4) Dépanner le terminal")
    print("    5) GitHub              6) Cybersécurité")
    print("    7) Failles (vulnérabilités)")
    print("  Les leçons (comprendre comment ça marche) :")
    print("    8) Le neurone          9) Apprendre y = 2x")
    print("   10) S'entraîner        11) La mémoire")
    print("   12) Le réseau (XOR)")
    print("    t) Lancer les tests    0) Quitter")


def lancer(fichier):
    """Lance un script de MonIA et attend qu'il se termine."""
    subprocess.run([sys.executable, os.path.join(DOSSIER, fichier)])


if __name__ == "__main__":
    while True:
        afficher_menu()
        try:
            choix = input("\nTon choix : ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nÀ bientôt !")
            break

        if choix in {"0", "q", "quitter", "exit", "quit"}:
            print("À bientôt !")
            break
        if choix in LECONS:
            description, fichier = LECONS[choix]
            print(f"\n--- {description} ---")
            lancer(fichier)
        else:
            print("Choix inconnu. Tape un numéro du menu (ou 0 pour quitter).")

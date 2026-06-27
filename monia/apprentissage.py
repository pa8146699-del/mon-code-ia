#!/usr/bin/env python3
"""Leçon 2 — Apprendre : faire en sorte que le neurone trouve la règle tout seul.

On veut que l'IA apprenne la fonction  y = 2·x  sans qu'on lui donne le « 2 ».
On lui montre seulement des exemples (x, y) et elle ajuste son poids et son biais
par **descente de gradient** jusqu'à coller aux exemples.

On utilise pour ça le réseau maison de `reseau.py`, configuré au plus simple :
un seul neurone linéaire ([1, 1], sortie "identite"). Après l'entraînement, le
poids doit s'approcher de 2 et le biais de 0.
"""

from reseau import Reseau

if __name__ == "__main__":
    # Exemples de la règle cachée y = 2x.
    donnees = [([x], [2 * x]) for x in range(-5, 6)]

    ia = Reseau([1, 1], sortie="identite", seed=0)
    ia.entrainer(donnees, epochs=2000, taux=0.01)

    print(f"Poids appris : {ia.poids[0][0][0]}")
    print(f"Biais appris : {ia.biais[0][0]}")
    print("Test :")
    print(f"Pour x=5, IA répond : {ia.predire([5])[0]}")

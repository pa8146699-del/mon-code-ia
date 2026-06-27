#!/usr/bin/env python3
"""Leçon 3 — L'entraînement en détail : suivre l'erreur baisser au fil des epochs.

Même objectif que la leçon 2 (apprendre y = 2·x), mais cette fois on **affiche
la progression** : à chaque jalon, l'erreur moyenne doit diminuer — c'est le
signe que l'IA apprend vraiment. À la fin, on la teste sur une valeur jamais vue
(x = 10) : elle doit répondre environ 20.
"""

from reseau import Reseau

if __name__ == "__main__":
    donnees = [([x], [2 * x]) for x in range(-5, 6)]

    ia = Reseau([1, 1], sortie="identite", seed=0)
    ia.entrainer(
        donnees,
        epochs=1000,
        taux=0.01,
        rappel=lambda e, err: print(f"Epoch {e} Erreur : {err}"),
    )

    print("\nRésultat final")
    print(f"Poids : {ia.poids[0][0][0]}")
    print(f"Biais : {ia.biais[0][0]}")

    print("\nTest x=10")
    print(f"IA répond : {ia.predire([10])[0]}")

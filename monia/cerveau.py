#!/usr/bin/env python3
"""Leçon 1 — Le neurone : la plus petite brique d'une IA.

Un neurone fait un calcul tout simple :

    réponse = entrée × poids + biais

Le « poids » dit à quel point l'entrée compte ; le « biais » décale le résultat.
Au départ ils sont tirés au hasard, donc l'IA répond n'importe quoi : elle n'a
encore rien appris. C'est le point de départ de tout (voir `apprentissage.py`).
"""

import random


def neurone(entree, poids, biais):
    return entree * poids + biais


if __name__ == "__main__":
    rng = random.Random()  # mets un nombre dans Random(...) pour figer le hasard

    poids = rng.uniform(-2, 2)
    biais = rng.uniform(-1, 1)
    entree = 5

    print(f"Entrée : {entree}")
    print(f"Poids : {poids}")
    print(f"Biais : {biais}")
    print(f"Réponse de l'IA : {neurone(entree, poids, biais)}")

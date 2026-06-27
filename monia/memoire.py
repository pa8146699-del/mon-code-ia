#!/usr/bin/env python3
"""Leçon 4 — La mémoire : garder ce que l'IA a appris, même après extinction.

Dans tes premiers essais, la « mémoire » était un dictionnaire en RAM : perdue
dès que le programme se ferme. Ici on fait mieux et pour de vrai : on entraîne
le réseau, on **sauvegarde ses poids dans un fichier JSON**, puis on les
**recharge** dans une IA toute neuve. Elle retrouve son savoir sans réapprendre.

C'est exactement comme ça que les vrais modèles gardent leurs connaissances :
les poids appris *sont* la mémoire.
"""

import os

from reseau import Reseau

FICHIER = os.path.join(os.path.dirname(__file__), "memoire.json")

if __name__ == "__main__":
    donnees = [([x], [2 * x]) for x in range(-5, 6)]

    # 1) Une IA neuve : elle ne sait rien.
    neuve = Reseau([1, 1], sortie="identite", seed=0)
    print("Avant apprentissage :")
    print(f"  Pour x=4, IA répond : {neuve.predire([4])[0]:.4f}")

    # 2) On l'entraîne puis on enregistre sa mémoire sur le disque.
    neuve.entrainer(donnees, epochs=2000, taux=0.01)
    neuve.sauvegarder(FICHIER)
    print("Après apprentissage :")
    print(f"  Pour x=4, IA répond : {neuve.predire([4])[0]:.4f}")
    print(f"  Mémoire sauvegardée dans : {os.path.basename(FICHIER)}")

    # 3) Une autre IA, vierge, recharge la mémoire : elle sait déjà, sans réapprendre.
    rechargee = Reseau.charger(FICHIER)
    print("Après rechargement de la mémoire (sans réapprendre) :")
    print(f"  Pour x=4, IA répond : {rechargee.predire([4])[0]:.4f}")

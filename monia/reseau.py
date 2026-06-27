#!/usr/bin/env python3
"""MonIA — un réseau de neurones « from scratch », 100 % maison.

Aucune dépendance : ni numpy, ni torch, ni tensorflow. Juste la bibliothèque
standard de Python (`math`, `random`, `json`). C'est *ton* IA, écrite à la main,
que tu peux lire en entier et comprendre ligne par ligne.

Un neurone calcule simplement :  sortie = activation( poids·entrée + biais ).
Un réseau, c'est plusieurs couches de neurones empilées. En empilant des
couches avec une activation non-linéaire (tanh, sigmoïde, relu) le réseau peut
apprendre des fonctions que ton premier neurone linéaire ne pouvait pas (par
exemple le XOR). On l'entraîne par **rétropropagation** (descente de gradient).

Utilisation rapide :

    from reseau import Reseau

    # 2 entrées -> 1 sortie, avec une couche cachée de 4 neurones
    ia = Reseau([2, 4, 1], activation="tanh", sortie="sigmoide", seed=1)
    ia.entrainer(donnees, epochs=2000, taux=0.5)
    print(ia.predire([1, 0]))

Tout est en listes Python pures (les matrices sont des listes de listes), pour
que ça tourne partout — y compris dans Termux sur un téléphone, sans rien
installer.
"""

import json
import math
import random


# --- Fonctions d'activation -------------------------------------------------
# Chaque activation est un couple (f, df) où :
#   f(z)  : la valeur de sortie du neurone pour la pré-activation z
#   df(z) : la dérivée de f en z (nécessaire pour la rétropropagation)


def _sigmoide(z):
    # On borne z pour éviter un overflow de math.exp sur de grandes valeurs.
    if z < -60.0:
        return 0.0
    if z > 60.0:
        return 1.0
    return 1.0 / (1.0 + math.exp(-z))


ACTIVATIONS = {
    # Linéaire : utile pour une sortie de régression (prédire un nombre).
    "identite": (lambda z: z, lambda z: 1.0),
    # Sigmoïde : écrase tout dans ]0, 1[ — idéale pour une probabilité.
    "sigmoide": (_sigmoide, lambda z: _sigmoide(z) * (1.0 - _sigmoide(z))),
    # Tanh : comme la sigmoïde mais centrée sur 0 (]-1, 1[), apprend souvent mieux.
    "tanh": (math.tanh, lambda z: 1.0 - math.tanh(z) ** 2),
    # ReLU : simple et rapide, garde les positifs, met les négatifs à 0.
    "relu": (lambda z: z if z > 0.0 else 0.0, lambda z: 1.0 if z > 0.0 else 0.0),
}


class Reseau:
    """Un perceptron multicouche (MLP) entraînable, en Python pur."""

    def __init__(self, tailles, activation="tanh", sortie="identite", seed=None):
        """Construit le réseau.

        tailles    : liste [n_entrées, n_cachées..., n_sorties].
                     Ex. [2, 4, 1] = 2 entrées, 1 couche cachée de 4, 1 sortie.
        activation : activation des couches cachées ("tanh", "sigmoide", "relu").
        sortie     : activation de la dernière couche ("identite" pour régression,
                     "sigmoide" pour une probabilité 0–1).
        seed       : graine aléatoire pour des poids reproductibles (optionnel).
        """
        if len(tailles) < 2:
            raise ValueError("tailles doit contenir au moins [entrées, sorties]")
        if activation not in ACTIVATIONS or sortie not in ACTIVATIONS:
            raise ValueError("activation inconnue")

        self.tailles = list(tailles)
        self.activation = activation
        self.sortie = sortie

        rng = random.Random(seed)
        self.poids = []  # un par couche : matrice (n_sortie x n_entrée)
        self.biais = []  # un par couche : vecteur (n_sortie)
        for n_in, n_out in zip(tailles[:-1], tailles[1:]):
            # Initialisation type Xavier : garde les signaux à une échelle saine.
            limite = math.sqrt(6.0 / (n_in + n_out))
            self.poids.append(
                [[rng.uniform(-limite, limite) for _ in range(n_in)] for _ in range(n_out)]
            )
            self.biais.append([0.0 for _ in range(n_out)])

    # -- Passe avant ---------------------------------------------------------

    def _avant(self, x):
        """Propage l'entrée à travers le réseau.

        Renvoie (pre, activations) où `pre[i]` = pré-activations (z) de la
        couche i et `activations[i]` = sorties de la couche i, avec
        activations[0] = entrée. Ces deux listes servent à la rétropropagation.
        """
        activations = [list(x)]
        pre = []
        a = activations[0]
        derniere = len(self.poids) - 1
        for i, (W, b) in enumerate(zip(self.poids, self.biais)):
            z = [sum(W[j][k] * a[k] for k in range(len(a))) + b[j] for j in range(len(W))]
            f = ACTIVATIONS[self.sortie if i == derniere else self.activation][0]
            a = [f(zj) for zj in z]
            pre.append(z)
            activations.append(a)
        return pre, activations

    def predire(self, x):
        """Calcule la sortie du réseau pour une entrée `x` (liste de nombres)."""
        return self._avant(x)[1][-1]

    # -- Apprentissage -------------------------------------------------------

    def _retropropager(self, x, y, taux):
        """Un pas de descente de gradient sur un exemple (x, y).

        Renvoie l'erreur quadratique (MSE) avant la mise à jour des poids.
        """
        pre, activations = self._avant(x)
        L = len(self.poids)
        sortie = activations[-1]

        # Erreur en sortie : dérivée de la perte 0.5·Σ(sortie − y)² composée avec
        # la dérivée de l'activation de sortie.
        df_sortie = ACTIVATIONS[self.sortie][1]
        deltas = [None] * L
        deltas[L - 1] = [
            (sortie[j] - y[j]) * df_sortie(pre[-1][j]) for j in range(len(sortie))
        ]

        # On remonte l'erreur couche par couche (rétropropagation).
        df_cachee = ACTIVATIONS[self.activation][1]
        for i in range(L - 2, -1, -1):
            W_suiv = self.poids[i + 1]
            z = pre[i]
            deltas[i] = [
                sum(W_suiv[k][j] * deltas[i + 1][k] for k in range(len(W_suiv)))
                * df_cachee(z[j])
                for j in range(len(z))
            ]

        # Mise à jour des poids et biais dans le sens opposé au gradient.
        for i in range(L):
            a_prec = activations[i]
            for j in range(len(self.poids[i])):
                d = deltas[i][j]
                ligne = self.poids[i][j]
                for k in range(len(a_prec)):
                    ligne[k] -= taux * d * a_prec[k]
                self.biais[i][j] -= taux * d

        return 0.5 * sum((sortie[j] - y[j]) ** 2 for j in range(len(sortie)))

    def entrainer(self, donnees, epochs=1000, taux=0.1, rappel=None):
        """Entraîne le réseau sur `donnees` = liste de couples (x, y).

        epochs : nombre de passages complets sur le jeu de données.
        taux   : pas d'apprentissage (learning rate).
        rappel : fonction optionnelle rappel(epoch, erreur_moyenne) appelée
                 régulièrement — pratique pour afficher la progression.
        Renvoie l'historique des erreurs moyennes par epoch.
        """
        historique = []
        jalon = max(1, epochs // 10)
        for e in range(epochs):
            erreur = sum(self._retropropager(list(x), list(y), taux) for x, y in donnees)
            erreur /= len(donnees)
            historique.append(erreur)
            if rappel and (e % jalon == 0 or e == epochs - 1):
                rappel(e, erreur)
        return historique

    # -- Mémoire persistante (sauvegarde / chargement) -----------------------

    def sauvegarder(self, chemin):
        """Écrit les poids appris dans un fichier JSON : la « mémoire » de l'IA."""
        with open(chemin, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "tailles": self.tailles,
                    "activation": self.activation,
                    "sortie": self.sortie,
                    "poids": self.poids,
                    "biais": self.biais,
                },
                f,
            )

    @classmethod
    def charger(cls, chemin):
        """Recrée un réseau depuis un fichier JSON produit par `sauvegarder`."""
        with open(chemin, encoding="utf-8") as f:
            etat = json.load(f)
        ia = cls(etat["tailles"], etat["activation"], etat["sortie"])
        ia.poids = etat["poids"]
        ia.biais = etat["biais"]
        return ia


# --- Démo : apprendre le XOR (impossible pour un seul neurone linéaire) ------

if __name__ == "__main__":
    # Le XOR est l'exemple classique : non-linéaire, donc hors de portée d'un
    # neurone unique. Un réseau avec une couche cachée y arrive très bien.
    donnees = [
        ([0, 0], [0]),
        ([0, 1], [1]),
        ([1, 0], [1]),
        ([1, 1], [0]),
    ]

    ia = Reseau([2, 4, 1], activation="tanh", sortie="sigmoide", seed=1)
    ia.entrainer(
        donnees,
        epochs=3000,
        taux=0.5,
        rappel=lambda e, err: print(f"Epoch {e:>4}  erreur : {err:.6f}"),
    )

    print("\nTable de vérité apprise (XOR) :")
    for entree, attendu in donnees:
        prediction = ia.predire(entree)[0]
        print(f"  {entree} -> {prediction:.3f}  (attendu {attendu[0]})")

#!/usr/bin/env python3
"""Leçon 6 — Lire un livre : apprendre BEAUCOUP de mots et écrire.

Le chatbot de `discussion.py` apprend des paires « question → réponse ». Un
livre, lui, ne contient pas de questions/réponses : c'est du texte d'affilée.
Pour apprendre un livre, il faut une autre technique — un **générateur de
texte**.

Le principe (un « modèle de Markov », simple et puissant) :
  1. On lit tout le texte et on le découpe en mots.
  2. Pour chaque suite de N mots, on retient quels mots viennent juste après,
     et à quelle fréquence. C'est ça, « apprendre le livre ».
  3. Pour écrire, on part de quelques mots et on tire le mot suivant au hasard
     parmi ceux que le livre a montrés — encore et encore.

Résultat : il connaît TOUT le vocabulaire du livre et écrit dans son style.
Ce n'est pas un réseau de neurones (c'est statistique), mais c'est la bonne
outil pour « avaler » un livre entier — et ça reste 100 % stdlib, sur ton
téléphone.

Utilisation :
    python3 ecrivain.py mon_livre.txt      # apprend ton livre puis écrit
    python3 ecrivain.py                     # apprend un petit texte d'exemple

Où trouver des livres gratuits (.txt) : voir le README (Projet Gutenberg).
"""

import json
import os
import random
import re
import sys


def jetons(texte):
    """Découpe un texte en mots et ponctuation (minuscules)."""
    return re.findall(r"\w+|[.,!?;:]", texte.lower())


def _joindre(tokens):
    """Recolle des jetons en texte lisible (pas d'espace avant la ponctuation)."""
    sortie = ""
    for t in tokens:
        if re.fullmatch(r"[.,!?;:]", t):
            sortie += t
        else:
            sortie += (" " if sortie else "") + t
    return sortie


class Ecrivain:
    """Un générateur de texte qui apprend le vocabulaire et le style d'un livre."""

    def __init__(self, ordre=2):
        # ordre = combien de mots de contexte on regarde pour deviner le suivant.
        self.ordre = ordre
        self.modele = {}   # "mot1 mot2" -> {mot_suivant: nombre_de_fois}
        self.debuts = []   # contextes qui démarrent une phrase
        self._mots = set()

    def apprendre_texte(self, texte):
        """Apprend (en plus de ce qu'il sait déjà) le texte donné."""
        toks = jetons(texte)
        self._mots.update(toks)
        for i in range(len(toks) - self.ordre):
            cle = " ".join(toks[i:i + self.ordre])
            suivant = toks[i + self.ordre]
            self.modele.setdefault(cle, {})
            self.modele[cle][suivant] = self.modele[cle].get(suivant, 0) + 1
            if i == 0 or toks[i - 1] in {".", "!", "?"}:
                self.debuts.append(cle)

    def lire_livre(self, chemin):
        """Lit un fichier texte (.txt) entier et l'apprend."""
        with open(chemin, encoding="utf-8", errors="ignore") as f:
            self.apprendre_texte(f.read())

    def vocabulaire(self):
        """Nombre de mots différents appris."""
        return len(self._mots)

    def generer(self, amorce=None, nb_mots=40, seed=None):
        """Écrit du texte. `amorce` = mots de départ optionnels."""
        if not self.modele:
            return ""
        rng = random.Random(seed)

        if amorce:
            etat = jetons(amorce)[-self.ordre:]
            cle = " ".join(etat)
            if cle not in self.modele:
                cle = rng.choice(self.debuts or list(self.modele))
        else:
            cle = rng.choice(self.debuts or list(self.modele))

        sortie = cle.split(" ")
        for _ in range(nb_mots):
            choix = self.modele.get(" ".join(sortie[-self.ordre:]))
            if not choix:  # cul-de-sac : on repart d'un début de phrase
                sortie += rng.choice(self.debuts or list(self.modele)).split(" ")
                continue
            mots_possibles, poids = zip(*choix.items())
            sortie.append(rng.choices(mots_possibles, weights=poids, k=1)[0])
        return _joindre(sortie)

    # -- Mémoire (sauvegarde / chargement) -----------------------------------

    def sauvegarder(self, chemin):
        with open(chemin, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "ordre": self.ordre,
                    "modele": self.modele,
                    "debuts": self.debuts,
                    "mots": list(self._mots),
                },
                f,
                ensure_ascii=False,
            )

    @classmethod
    def charger(cls, chemin):
        with open(chemin, encoding="utf-8") as f:
            etat = json.load(f)
        ec = cls(ordre=etat["ordre"])
        ec.modele = etat["modele"]
        ec.debuts = etat["debuts"]
        ec._mots = set(etat["mots"])
        return ec


# Un petit texte d'exemple, libre de droits (Jean de La Fontaine, 1668).
EXEMPLE = """
Maître Corbeau, sur un arbre perché, tenait en son bec un fromage.
Maître Renard, par l'odeur alléché, lui tint à peu près ce langage :
Et bonjour, Monsieur du Corbeau. Que vous êtes joli ! que vous me semblez beau !
Sans mentir, si votre ramage se rapporte à votre plumage,
vous êtes le Phénix des hôtes de ces bois.
À ces mots le Corbeau ne se sent pas de joie ;
et pour montrer sa belle voix, il ouvre un large bec, laisse tomber sa proie.
Le Renard s'en saisit, et dit : Mon bon Monsieur,
apprenez que tout flatteur vit aux dépens de celui qui l'écoute.
Cette leçon vaut bien un fromage, sans doute.
Le Corbeau, honteux et confus, jura, mais un peu tard, qu'on ne l'y prendrait plus.
"""


if __name__ == "__main__":
    ec = Ecrivain(ordre=2)

    if len(sys.argv) > 1:
        ec.lire_livre(sys.argv[1])
        print(f"📖 Livre lu : {sys.argv[1]}")
    else:
        ec.apprendre_texte(EXEMPLE)
        print("(Aucun livre fourni — j'apprends un petit texte d'exemple.)")

    print(f"J'ai appris {ec.vocabulaire()} mots différents.\n")
    print("Texte généré :")
    print("  " + ec.generer(nb_mots=40))
    print("\nDonne-moi un ou deux mots de départ, je continue (quitter pour sortir).")

    while True:
        try:
            amorce = input("Toi : ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nMonIA : Au revoir !")
            break
        if amorce.lower() in {"quitter", "stop", "exit", "quit"}:
            print("MonIA : Au revoir !")
            break
        if not amorce:
            continue
        print("MonIA : " + ec.generer(amorce=amorce, nb_mots=30))

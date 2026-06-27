#!/usr/bin/env python3
"""Leçon 5 — Discuter : apprendre des mots pour répondre à des questions.

⚠️  À lire d'abord — ce que cette IA peut et ne peut pas faire :
Une IA 100 % maison en Python pur ne peut PAS « connaître tous les mots » du
monde comme ChatGPT (ça demande des milliards de paramètres et d'énormes
données). MAIS elle peut apprendre à répondre aux questions que **tu lui
enseignes**, même quand tu les reformules un peu. C'est un vrai chatbot, en
petit, et 100 % à toi.

Comment ça marche (et c'est tout le secret) :
  1. On découpe chaque phrase en mots (le « vocabulaire »).
  2. On transforme une phrase en nombres : un vecteur « sac de mots » qui dit
     quels mots du vocabulaire sont présents (1) ou absents (0).
  3. Le réseau de `reseau.py` apprend à associer ce vecteur à la bonne réponse.
  4. Pour répondre, on encode ta question et on prend la réponse la plus probable.

Tu peux lui apprendre TES propres questions/réponses : ajoute des couples dans
`CONNAISSANCES` ci-dessous, ou passe ta propre liste à `Discussion(...)`.

Lancer la discussion :  python3 discussion.py
"""

import json
import os
import re

from reseau import Reseau


def mots(phrase):
    """Découpe une phrase en mots simples (minuscules, sans ponctuation)."""
    return re.findall(r"[a-zà-ÿ0-9]+", phrase.lower())


class Discussion:
    """Un petit chatbot : il apprend des couples (question, réponse)."""

    def __init__(self, paires, cachees=10, seed=0):
        self._cachees = cachees
        self._seed = seed
        self._construire(paires)

    def _construire(self, paires):
        """(Re)construit le vocabulaire, les classes et le réseau depuis `paires`."""
        self._paires = list(paires)

        # Vocabulaire : tous les mots vus dans les questions (sans doublon).
        self.vocab = []
        for question, _ in self._paires:
            for m in mots(question):
                if m not in self.vocab:
                    self.vocab.append(m)

        # Classes : les réponses distinctes possibles.
        self.classes = []
        for _, reponse in self._paires:
            if reponse not in self.classes:
                self.classes.append(reponse)

        # Le réseau : sac-de-mots en entrée -> une réponse en sortie.
        self.reseau = Reseau(
            [len(self.vocab), self._cachees, len(self.classes)],
            activation="tanh",
            sortie="sigmoide",
            seed=self._seed,
        )

    def apprendre(self, question, reponse, epochs=3000, taux=0.3):
        """Ajoute un couple (question, réponse) et réapprend tout de suite.

        Comme un nouveau mot ou une nouvelle réponse change la taille du réseau,
        on le reconstruit puis on le réentraîne sur l'ensemble des exemples.
        """
        self._construire(self._paires + [(question, reponse)])
        return self.entrainer(epochs, taux)

    def _encoder(self, phrase):
        """Transforme une phrase en vecteur sac-de-mots (des 0 et des 1)."""
        vecteur = [0.0] * len(self.vocab)
        for m in mots(phrase):
            if m in self.vocab:
                vecteur[self.vocab.index(m)] = 1.0
        return vecteur

    def entrainer(self, epochs=3000, taux=0.3, rappel=None):
        """Apprend à associer chaque question à sa réponse."""
        donnees = []
        for question, reponse in self._paires:
            cible = [0.0] * len(self.classes)
            cible[self.classes.index(reponse)] = 1.0
            donnees.append((self._encoder(question), cible))
        return self.reseau.entrainer(donnees, epochs, taux, rappel)

    def repondre(self, question, seuil=0.5):
        """Renvoie la réponse la plus probable, ou avoue ne pas savoir."""
        vecteur = self._encoder(question)
        # Si aucun mot de la question n'est dans son vocabulaire, elle ne peut
        # rien en faire : autant le dire honnêtement.
        if sum(vecteur) == 0:
            return "Je ne sais pas encore répondre à ça. Apprends-le moi !"
        sortie = self.reseau.predire(vecteur)
        i = max(range(len(sortie)), key=lambda k: sortie[k])
        if sortie[i] < seuil:
            return "Je ne sais pas encore répondre à ça. Apprends-le moi !"
        return self.classes[i]

    # -- Mémoire : tout sauvegarder dans un seul fichier JSON ----------------

    def sauvegarder(self, chemin):
        with open(chemin, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "paires": self._paires,
                    "vocab": self.vocab,
                    "classes": self.classes,
                    "poids": self.reseau.poids,
                    "biais": self.reseau.biais,
                },
                f,
                ensure_ascii=False,
            )

    @classmethod
    def charger(cls, chemin):
        with open(chemin, encoding="utf-8") as f:
            etat = json.load(f)
        chat = cls(etat["paires"])
        chat.vocab = etat["vocab"]
        chat.classes = etat["classes"]
        chat.reseau.poids = etat["poids"]
        chat.reseau.biais = etat["biais"]
        return chat


# --- Ce que l'IA sait au départ (apprends-lui-en plus !) --------------------
# Ajoute tes propres couples ici : ("ta question", "sa réponse").
# Donne plusieurs formulations d'une même question pour qu'elle généralise mieux.

CONNAISSANCES = [
    ("bonjour", "Bonjour ! Comment puis-je t'aider ?"),
    ("salut", "Bonjour ! Comment puis-je t'aider ?"),
    ("coucou", "Bonjour ! Comment puis-je t'aider ?"),
    ("comment tu t'appelles", "Je m'appelle MonIA, ton IA faite maison."),
    ("quel est ton nom", "Je m'appelle MonIA, ton IA faite maison."),
    ("qui es-tu", "Je suis MonIA, un réseau de neurones que tu as fabriqué toi-même."),
    ("comment vas-tu", "Je vais très bien, merci ! Et toi ?"),
    ("ça va", "Je vais très bien, merci ! Et toi ?"),
    ("que sais-tu faire", "J'apprends à répondre aux questions que tu m'enseignes."),
    ("quel âge as-tu", "Je viens de naître dans ton téléphone, je suis toute jeune !"),
    ("merci", "De rien, avec plaisir !"),
    ("au revoir", "Au revoir ! À bientôt."),
]


FICHIER = os.path.join(os.path.dirname(__file__), "chat.json")

AIDE = (
    "Pour m'apprendre une réponse, écris :  apprends: ta question = ma réponse\n"
    "  exemple :  apprends: quelle est la capitale de la France = Paris\n"
    "Autres commandes :  aide  (revoir ceci)   |   quitter  (arrêter)"
)


if __name__ == "__main__":
    # Si elle a déjà appris des choses la dernière fois, on les recharge.
    if os.path.exists(FICHIER):
        chat = Discussion.charger(FICHIER)
        print("J'ai rechargé tout ce que tu m'as appris. 🧠")
    else:
        print("J'apprends mes connaissances de départ...")
        chat = Discussion(CONNAISSANCES, seed=0)
        chat.entrainer(epochs=3000, taux=0.3)
        chat.sauvegarder(FICHIER)

    print("Prête ! " + AIDE + "\n")

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

        # Enseignement en direct : "apprends: question = réponse"
        if phrase.lower().startswith("apprends"):
            corps = phrase.split(":", 1)[1] if ":" in phrase else ""
            if "=" not in corps:
                print("MonIA : Dis-moi plutôt :  apprends: ta question = ma réponse")
                continue
            question, reponse = corps.split("=", 1)
            question, reponse = question.strip(), reponse.strip()
            if not question or not reponse:
                print("MonIA : Il me faut une question ET une réponse.")
                continue
            chat.apprendre(question, reponse)
            chat.sauvegarder(FICHIER)  # je le retiens pour la prochaine fois
            print(f"MonIA : Compris ! Désormais à « {question} » je répondrai « {reponse} ».")
            continue

        print(f"MonIA : {chat.repondre(phrase)}")

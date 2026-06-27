#!/usr/bin/env python3
"""Outil — Mini-CTF : des défis de hacking pour s'entraîner LÉGALEMENT.

Un CTF (Capture The Flag) est un jeu de cybersécurité : tu résous des énigmes
pour trouver des « flags » (réponses secrètes). C'est la façon légale et fun de
progresser — ici, tout se passe sur ton téléphone, tu n'attaques personne.

Chaque défi te donne un message à décoder. Trouve la réponse, gagne des points.
Tape `indice` pour un coup de pouce, `passer` pour le défi suivant, `quitter`
pour arrêter.

Lancer :  python3 ctf.py
"""


def cesar(texte, decalage):
    """Décale chaque lettre de l'alphabet (chiffre/déchiffre de César)."""
    resultat = []
    for c in texte:
        if c.isalpha():
            base = ord("a") if c.islower() else ord("A")
            resultat.append(chr((ord(c) - base + decalage) % 26 + base))
        else:
            resultat.append(c)
    return "".join(resultat)


# Chaque défi : titre, énoncé, réponse attendue, indice, points.
DEFIS = [
    {
        "titre": "Le chiffre de César",
        "enonce": "Déchiffre ce mot (chaque lettre a été avancée de 3) : 'erqmrxu'",
        "reponse": "bonjour",
        "indice": "Recule chaque lettre de 3 dans l'alphabet : e->b, r->o, q->n...",
        "points": 10,
    },
    {
        "titre": "Le message à l'envers",
        "enonce": "Lis ce mot à l'envers : 'terces'",
        "reponse": "secret",
        "indice": "Commence par la dernière lettre : s, e, c...",
        "points": 10,
    },
    {
        "titre": "Le Base64",
        "enonce": "Décode ce texte Base64 : 'bW90ZGVwYXNzZQ=='",
        "reponse": "motdepasse",
        "indice": "En Python : import base64 ; base64.b64decode('...').decode()",
        "points": 15,
    },
    {
        "titre": "L'acrostiche",
        "enonce": "Prends la 1re lettre de chaque mot : 'Hardi Esprit Libre Lance Ours'",
        "reponse": "hello",
        "indice": "H... E... L... L... O...",
        "points": 15,
    },
    {
        "titre": "Le binaire",
        "enonce": "Décode ce binaire (8 bits = 1 lettre) : '01001000 01101001'",
        "reponse": "hi",
        "indice": "01001000 = 72 = 'H' dans la table ASCII ; 01101001 = 105 = 'i'.",
        "points": 20,
    },
]


def jouer(defis):
    """Fait jouer la liste de défis et renvoie le score total obtenu."""
    score = 0
    for numero, defi in enumerate(defis, 1):
        print(f"\n=== Défi {numero}/{len(defis)} : {defi['titre']} ({defi['points']} pts) ===")
        print(defi["enonce"])
        while True:
            try:
                reponse = input("Ta réponse : ").strip()
            except (EOFError, KeyboardInterrupt):
                print(f"\nScore final : {score} points. À bientôt !")
                return score
            bas = reponse.lower()
            if bas in {"quitter", "stop", "exit", "quit"}:
                print(f"\nScore final : {score} points. À bientôt !")
                return score
            if bas == "indice":
                print("💡 " + defi["indice"])
                continue
            if bas == "passer":
                print(f"On passe. La réponse était : {defi['reponse']}")
                break
            if bas == defi["reponse"].lower():
                score += defi["points"]
                print(f"✅ Bravo ! +{defi['points']} points (total : {score})")
                break
            print("❌ Raté. Tape 'indice', 'passer' ou réessaie.")

    print(f"\n🏁 Terminé ! Score final : {score} / {sum(d['points'] for d in defis)} points.")
    if score == sum(d["points"] for d in defis):
        print("🏆 Sans-faute, tu es un vrai hacker (éthique) !")
    return score


if __name__ == "__main__":
    print("🚩 Mini-CTF — résous les énigmes, trouve les flags, gagne des points !")
    print("   (tout est légal : tu joues sur ton téléphone, tu n'attaques personne)")
    jouer(DEFIS)

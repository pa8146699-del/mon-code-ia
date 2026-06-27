#!/usr/bin/env python3
"""Outil — Mots de passe : en générer un solide et tester la force du tien.

Deux fonctions utiles au quotidien, 100 % stdlib :
  • generer(longueur) : fabrique un mot de passe aléatoire fort avec le module
    `secrets` (le bon module pour les secrets — pas `random`, qui n'est pas sûr).
  • force(mdp) : évalue la robustesse (entropie en bits) et donne des conseils.

C'est le même esprit que `dataguard/toolkit.py`, en version MonIA.

Lancer :  python3 motdepasse.py
"""

import math
import secrets
import string

# Quelques mots de passe parmi les plus courants — à ne JAMAIS utiliser.
COMMUNS = {
    "123456", "12345678", "password", "motdepasse", "azerty", "qwerty",
    "000000", "111111", "admin", "bonjour", "soleil", "iloveyou",
}

SYMBOLES = "!@#$%^&*-_=+?"


def generer(longueur=16, symboles=True):
    """Crée un mot de passe aléatoire fort, avec au moins un caractère de chaque type."""
    longueur = max(8, longueur)
    classes = [string.ascii_lowercase, string.ascii_uppercase, string.digits]
    if symboles:
        classes.append(SYMBOLES)
    alphabet = "".join(classes)

    # Garantir au moins un caractère de chaque classe demandée.
    mdp = [secrets.choice(classe) for classe in classes]
    while len(mdp) < longueur:
        mdp.append(secrets.choice(alphabet))

    # Mélanger de façon sûre (Fisher-Yates avec secrets).
    for i in range(len(mdp) - 1, 0, -1):
        j = secrets.randbelow(i + 1)
        mdp[i], mdp[j] = mdp[j], mdp[i]
    return "".join(mdp)


def force(mdp):
    """Évalue un mot de passe. Renvoie (niveau, bits_d_entropie, [conseils])."""
    if not mdp:
        return ("vide", 0, ["Le mot de passe est vide."])
    if mdp.lower() in COMMUNS:
        return ("très faible", 0, ["Ce mot de passe est dans la liste des plus courants !"])

    taille_alphabet = 0
    if any(c.islower() for c in mdp):
        taille_alphabet += 26
    if any(c.isupper() for c in mdp):
        taille_alphabet += 26
    if any(c.isdigit() for c in mdp):
        taille_alphabet += 10
    if any(not c.isalnum() for c in mdp):
        taille_alphabet += len(SYMBOLES)

    bits = len(mdp) * math.log2(taille_alphabet) if taille_alphabet else 0

    conseils = []
    if len(mdp) < 12:
        conseils.append("Allonge-le : au moins 12 caractères.")
    if not any(c.isupper() for c in mdp):
        conseils.append("Ajoute des MAJUSCULES.")
    if not any(c.isdigit() for c in mdp):
        conseils.append("Ajoute des chiffres.")
    if not any(not c.isalnum() for c in mdp):
        conseils.append("Ajoute des symboles (!, ?, #...).")

    if bits < 28:
        niveau = "très faible"
    elif bits < 36:
        niveau = "faible"
    elif bits < 60:
        niveau = "moyen"
    elif bits < 128:
        niveau = "fort"
    else:
        niveau = "excellent"
    return (niveau, round(bits), conseils)


def _afficher_force(mdp):
    niveau, bits, conseils = force(mdp)
    print(f"MonIA : force = {niveau} (~{bits} bits d'entropie)")
    for c in conseils:
        print("   • " + c)


if __name__ == "__main__":
    print("🔐 Outils mots de passe")
    print("  genere           -> un mot de passe fort")
    print("  genere 24        -> un mot de passe de 24 caractères")
    print("  teste: monmdp    -> évalue la force d'un mot de passe")
    print("  (ou tape directement un mot de passe pour le tester ; quitter pour sortir)\n")

    while True:
        try:
            phrase = input("Toi : ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nMonIA : Au revoir !")
            break
        bas = phrase.lower()
        if bas in {"quitter", "stop", "exit", "quit"}:
            print("MonIA : Au revoir !")
            break
        if not phrase:
            continue

        if bas.startswith("genere") or bas.startswith("génère"):
            morceaux = phrase.split()
            longueur = 16
            if len(morceaux) > 1 and morceaux[1].isdigit():
                longueur = int(morceaux[1])
            mdp = generer(longueur)
            print(f"MonIA : voici un mot de passe fort :\n   {mdp}")
            _afficher_force(mdp)
            continue

        if bas.startswith("teste"):
            cible = phrase.split(":", 1)[1].strip() if ":" in phrase else ""
            if not cible:
                print("MonIA : écris :  teste: ton_mot_de_passe")
                continue
            _afficher_force(cible)
            continue

        # Sinon, on teste directement ce qui a été tapé.
        _afficher_force(phrase)

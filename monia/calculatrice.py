#!/usr/bin/env python3
"""Outil — La calculatrice intelligente : elle comprend tes calculs en français.

Contrairement au chatbot (qui restitue des réponses apprises), la calculatrice
**calcule vraiment**. Tu écris en français (« combien font 12 fois 8 ? ») et elle
trouve le résultat.

Important : on n'utilise PAS eval() (ce serait une faille — ton analyseur la
signalerait !). On lit l'expression de façon sûre avec le module `ast`, qui
n'autorise que des nombres et les opérations + - * / ** % (). Aucun code étranger
ne peut s'exécuter.

Lancer :  python3 calculatrice.py
"""

import ast
import operator
import re

# Opérations autorisées (et rien d'autre).
_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _evaluer(noeud):
    """Évalue un nœud de l'arbre `ast`, en n'autorisant que les maths sûres."""
    if isinstance(noeud, ast.Constant) and isinstance(noeud.value, (int, float)):
        return noeud.value
    if isinstance(noeud, ast.BinOp) and type(noeud.op) in _OPS:
        return _OPS[type(noeud.op)](_evaluer(noeud.left), _evaluer(noeud.right))
    if isinstance(noeud, ast.UnaryOp) and type(noeud.op) in _OPS:
        return _OPS[type(noeud.op)](_evaluer(noeud.operand))
    raise ValueError("expression non autorisée")


def calculer(expression):
    """Calcule une expression arithmétique sûre (ex : '12 * 8')."""
    return _evaluer(ast.parse(expression, mode="eval").body)


def normaliser(texte):
    """Transforme une phrase française en expression mathématique."""
    t = texte.lower()
    # "racine (carrée) de 16" -> "(16) ** 0.5"
    t = re.sub(r"racines?\s+(?:carrées?\s+)?de\s+(\d+(?:[.,]\d+)?)", r"(\1) ** 0.5", t)
    mots = [
        ("multiplié par", "*"), ("multiplie par", "*"), ("fois", "*"), (" x ", " * "),
        ("divisé par", "/"), ("divise par", "/"), ("sur", "/"),
        ("puissance", "**"), ("exposant", "**"), ("au carré", "** 2"),
        ("plus", "+"), ("moins", "-"), ("modulo", "%"),
    ]
    for mot, signe in mots:
        t = t.replace(mot, signe)
    t = t.replace(",", ".")                       # virgule décimale -> point
    t = re.sub(r"[^0-9+\-*/%.() ]", " ", t)        # on ne garde que les maths
    return t.strip()


def repondre(question):
    """Renvoie le résultat du calcul, ou None si ce n'est pas un calcul compris."""
    expression = normaliser(question)
    if not re.search(r"\d", expression):
        return None
    try:
        resultat = calculer(expression)
    except Exception:
        return None
    if isinstance(resultat, float) and resultat.is_integer():
        resultat = int(resultat)
    elif isinstance(resultat, float):
        resultat = round(resultat, 6)
    return resultat


if __name__ == "__main__":
    print("Calculatrice intelligente — écris un calcul en français.")
    print("  exemples :  combien font 12 fois 8 ?   |   racine de 144   |   2 puissance 10")
    print("  (quitter pour sortir)\n")

    while True:
        try:
            question = input("Toi : ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nMonIA : Au revoir !")
            break
        if question.lower() in {"quitter", "stop", "exit", "quit"}:
            print("MonIA : Au revoir !")
            break
        if not question:
            continue
        resultat = repondre(question)
        if resultat is None:
            print("MonIA : Je n'ai pas compris le calcul. Essaie '12 fois 8' ou '45 + 7'.")
        else:
            print(f"MonIA : = {resultat}")

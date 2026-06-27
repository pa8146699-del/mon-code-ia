#!/usr/bin/env python3
"""Leçon 12 — L'analyseur : trouver des failles dans TON code, légalement.

La façon légale et utile de « trouver des failles », c'est d'examiner du code que
tu possèdes pour y repérer les pratiques dangereuses — avant qu'un attaquant ne
le fasse. C'est de l'analyse statique : on lit le code et on cherche des motifs à
risque (secrets en clair, eval, injection SQL, TLS désactivé...). Pour chaque
trouvaille, l'outil explique le risque ET comment corriger.

✅ Légal : tu analyses TON propre code, sur ta machine. Aucune attaque, aucune
cible distante. C'est le même esprit que `dataguard/`, la boîte à outils du repo.

Utilisation :
    python3 analyseur.py mon_fichier.py     # analyse un fichier
    python3 analyseur.py                     # mode interactif (colle du code)

100 % stdlib (juste `re`). Heuristique : il signale des motifs probables, à toi
de juger — comme tout bon outil d'analyse.
"""

import os
import re
import sys

# Chaque règle : (nom, motif, sévérité, conseil de correction, masquer_le_secret).
REGLES = [
    ("Exécution de code (eval/exec)",
     re.compile(r"\b(eval|exec)\s*\("), "HAUTE",
     "eval()/exec() exécutent du code arbitraire. Évite-les ; sinon valide très strictement l'entrée.", False),
    ("Commande shell (os.system/popen)",
     re.compile(r"\bos\.(system|popen)\s*\("), "HAUTE",
     "Risque d'injection de commande. Utilise subprocess avec une liste d'arguments, sans shell.", False),
    ("Shell activé (shell=True)",
     re.compile(r"shell\s*=\s*True"), "HAUTE",
     "shell=True permet l'injection de commande. Passe les arguments en liste et shell=False.", False),
    ("Secret en clair",
     re.compile(r"(?i)\b(password|passwd|secret|api[_-]?key|token)\b\s*=\s*['\"][^'\"]+['\"]"), "HAUTE",
     "Ne mets jamais un secret dans le code. Lis-le depuis une variable d'environnement (os.environ).", True),
    ("Injection SQL possible",
     re.compile(r"(?i)\b(select|insert|update|delete|drop)\b.*(\+|%|\{)"), "HAUTE",
     "Risque d'injection SQL. Utilise des requêtes paramétrées (placeholders), pas de concaténation.", False),
    ("Désérialisation non sûre (pickle)",
     re.compile(r"\bpickle\.loads?\s*\("), "MOYENNE",
     "pickle peut exécuter du code en chargeant des données. Préfère json pour des données non fiables.", False),
    ("Chargement YAML non sûr",
     re.compile(r"\byaml\.load\s*\("), "MOYENNE",
     "yaml.load peut exécuter du code. Utilise yaml.safe_load().", False),
    ("Hachage faible (md5/sha1)",
     re.compile(r"\bhashlib\.(md5|sha1)\s*\("), "MOYENNE",
     "MD5/SHA1 sont faibles. Utilise SHA-256, ou bcrypt/scrypt pour des mots de passe.", False),
    ("Vérification TLS désactivée",
     re.compile(r"verify\s*=\s*False"), "MOYENNE",
     "Désactiver la vérification TLS ouvre à l'homme du milieu. Garde verify=True.", False),
    ("Aléa non sûr pour un secret",
     re.compile(r"\brandom\.(random|randint|choice|randrange)\b"), "BASSE",
     "Le module random n'est pas sûr pour des secrets/tokens. Utilise le module secrets.", False),
    ("Lien non chiffré (http)",
     re.compile(r"http://"), "BASSE",
     "http:// n'est pas chiffré. Préfère https://.", False),
    ("Mode debug activé",
     re.compile(r"\bdebug\s*=\s*True"), "BASSE",
     "Ne laisse jamais debug=True en production : ça peut exposer des infos sensibles.", False),
    ("Fichier temporaire non sûr (mktemp)",
     re.compile(r"\btempfile\.mktemp\s*\("), "BASSE",
     "mktemp est sujet à une condition de course. Utilise tempfile.mkstemp().", False),
]

_ORDRE = {"HAUTE": 0, "MOYENNE": 1, "BASSE": 2}


def _masquer(ligne):
    """Remplace le contenu des guillemets par *** (pour ne pas afficher un secret)."""
    return re.sub(r"(['\"])([^'\"]+)\1", r"\1***\1", ligne)


def analyser_texte(texte):
    """Analyse un texte ligne par ligne.

    Renvoie une liste de trouvailles, chacune un dict :
    {ligne, severite, nom, conseil, extrait}.
    """
    trouvailles = []
    for numero, ligne in enumerate(texte.splitlines(), start=1):
        for nom, motif, severite, conseil, masquer in REGLES:
            if motif.search(ligne):
                extrait = _masquer(ligne).strip() if masquer else ligne.strip()
                trouvailles.append({
                    "ligne": numero,
                    "severite": severite,
                    "nom": nom,
                    "conseil": conseil,
                    "extrait": extrait[:100],
                })
    trouvailles.sort(key=lambda t: (t["ligne"], _ORDRE[t["severite"]]))
    return trouvailles


def analyser_fichier(chemin):
    with open(chemin, encoding="utf-8", errors="ignore") as f:
        return analyser_texte(f.read())


def _afficher(trouvailles, source):
    if not trouvailles:
        print(f"✅ Aucune faille évidente trouvée dans {source}.")
        return
    print(f"🛡️  {len(trouvailles)} point(s) à vérifier dans {source} :\n")
    for t in trouvailles:
        print(f"  [{t['severite']}] ligne {t['ligne']} — {t['nom']}")
        print(f"      > {t['extrait']}")
        print(f"      → {t['conseil']}\n")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        chemin = sys.argv[1]
        if not os.path.isfile(chemin):
            print(f"❌ Fichier introuvable : {chemin}")
            print("   Donne le chemin d'un VRAI fichier. Exemples :")
            print("   python3 analyseur.py discussion.py")
            print("   python3 analyseur.py ~/mon-code-ia/monia/reseau.py")
            raise SystemExit(1)
        _afficher(analyser_fichier(chemin), chemin)
    else:
        print("Analyseur de failles — colle une ligne de code, ou tape le nom")
        print("d'un fichier à analyser (quitter pour sortir).\n")
        while True:
            try:
                entree = input("Code/fichier : ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nAu revoir !")
                break
            if entree.lower() in {"quitter", "stop", "exit", "quit"}:
                print("Au revoir !")
                break
            if not entree:
                continue
            if os.path.isfile(entree):
                _afficher(analyser_fichier(entree), entree)
            else:
                _afficher(analyser_texte(entree), "ton code")

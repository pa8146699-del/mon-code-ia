#!/usr/bin/env python3
"""
monia/telecharger_texte.py — Donne un vrai gros livre français à lire à ton IA.

Télécharge un livre du domaine public (gratuit, libre) depuis Project Gutenberg
et l'enregistre dans monia/data.txt, en enlevant l'en-tête/pied légal pour ne
garder que le texte du livre.

Aucune dépendance : Python standard uniquement (urllib). Pas de clé API.

Usage :
    python monia/telecharger_texte.py                 # livre par défaut
    python monia/telecharger_texte.py 13951           # un autre livre (numéro Gutenberg)
    python monia/telecharger_texte.py https://.../x.txt   # n'importe quelle URL .txt

Trouver d'autres livres français : https://www.gutenberg.org/browse/languages/fr
(prends le numéro dans l'URL du livre, ex. .../ebooks/17489 -> 17489)
"""

import os
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data.txt")

# Quelques gros livres français du domaine public (numéro Gutenberg -> titre).
LIVRES = {
    "17489": "Les Misérables, Tome I — Victor Hugo",
    "13951": "Les Trois Mousquetaires — Alexandre Dumas",
    "5423":  "Vingt mille lieues sous les mers — Jules Verne",
    "4650":  "Candide — Voltaire",
    "798":   "Le Comte de Monte-Cristo, Tome I — Alexandre Dumas",
}

DEFAUT = "17489"  # Les Misérables : énorme et tout en français, parfait pour apprendre


def url_pour(arg):
    if arg.startswith("http"):
        return arg
    return f"https://www.gutenberg.org/cache/epub/{arg}/pg{arg}.txt"


def nettoyer(texte):
    """Enlève l'en-tête et le pied de page légaux de Project Gutenberg."""
    debut = texte.find("*** START OF")
    if debut != -1:
        debut = texte.find("\n", debut) + 1
        texte = texte[debut:]
    fin = texte.find("*** END OF")
    if fin != -1:
        texte = texte[:fin]
    return texte.strip()


def main():
    arg = sys.argv[1] if len(sys.argv) > 1 else DEFAUT
    url = url_pour(arg)
    titre = LIVRES.get(arg, "")
    print(f"Téléchargement {'(' + titre + ') ' if titre else ''}depuis :\n  {url}")

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "monia/1.0"})
        with urllib.request.urlopen(req, timeout=60) as r:
            brut = r.read().decode("utf-8", "replace")
    except Exception as e:
        raise SystemExit(
            f"❌ Échec du téléchargement : {e}\n"
            "   Vérifie ta connexion, ou donne une autre URL/numéro.\n"
            "   Livres français : https://www.gutenberg.org/browse/languages/fr"
        )

    texte = nettoyer(brut)
    with open(DATA, "w", encoding="utf-8") as f:
        f.write(texte)

    print(f"✅ {len(texte):,} caractères enregistrés dans {DATA}")
    print("   Ton IA a maintenant un vrai livre à lire.")
    print("   Entraîne-la avec :  python monia/train.py")


if __name__ == "__main__":
    main()

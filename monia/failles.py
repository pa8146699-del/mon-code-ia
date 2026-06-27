#!/usr/bin/env python3
"""Leçon 11 — Les failles : connaître les vulnérabilités pour les corriger.

Cet assistant explique les grandes familles de failles de sécurité (à la manière
de l'OWASP) : pour chacune, ce que c'est, pourquoi c'est dangereux, et surtout
**comment s'en protéger**. C'est le savoir de base du défenseur et du hacker
éthique.

⚠️ Cadre légal — c'est ce qui fait toute la différence : chercher des failles est
légal seulement sur TES systèmes, dans un programme de bug bounty autorisé, ou
sur des CTF/labos faits pour ça. Tester le système d'autrui sans autorisation
écrite est un délit. Cet assistant reste **conceptuel** : il t'apprend à
reconnaître et corriger les failles, pas à les exploiter contre des cibles
réelles.

Même moteur que le chatbot (`discussion.py`). Mémoire auto dans `failles.json`.

Lancer :  python3 failles.py
"""

import os

from discussion import Discussion

FICHIER = os.path.join(os.path.dirname(__file__), "failles.json")
SEPARATEUR = ">>>"

AIDE = (
    "Pose ta question sur une faille, je t'explique (et comment s'en protéger).\n"
    "  exemples :  c'est quoi l'injection sql ?  |  c'est quoi le xss ?\n"
    "M'apprendre une note :  apprends: ta question " + SEPARATEUR + " ton explication\n"
    "Autres :  aide   |   quitter"
)

# Familles de vulnérabilités : définition + risque + défense (angle défensif).
CONNAISSANCES_FAILLES = [
    ("c'est quoi une faille de sécurité", "Une faille (vulnérabilité) est un défaut dans un logiciel ou une configuration qui peut être exploité pour faire ce qui n'était pas prévu : voler des données, prendre le contrôle, etc. On les corrige par les mises à jour et de bonnes pratiques."),
    ("c'est quoi l'injection sql", "L'injection SQL arrive quand une entrée utilisateur non filtrée est insérée dans une requête de base de données, ce qui permet de la détourner. Défense : requêtes paramétrées (préparées), ne jamais coller du texte brut dans une requête, et valider les entrées."),
    ("c'est quoi le xss", "Le XSS (cross-site scripting) injecte du code dans une page web qui s'exécute dans le navigateur d'autres visiteurs. Défense : échapper/encoder tout ce qui est affiché, valider les entrées, et une politique CSP."),
    ("c'est quoi le csrf", "Le CSRF (cross-site request forgery) piège un utilisateur connecté pour qu'il envoie une action sans le vouloir. Défense : jetons anti-CSRF, vérifier l'origine, et cookies SameSite."),
    ("c'est quoi le contrôle d'accès cassé", "Le contrôle d'accès cassé (broken access control), c'est quand on peut accéder à des données ou actions qui devraient être interdites (ex : changer un id dans l'URL). Défense : vérifier les droits côté serveur à chaque requête."),
    ("c'est quoi une mauvaise configuration", "Une mauvaise configuration (misconfiguration) laisse une porte ouverte : service exposé, page d'admin accessible, droits trop larges. Défense : durcir les réglages, désactiver ce qui ne sert pas, principe du moindre privilège."),
    ("c'est quoi les identifiants par défaut", "Beaucoup d'appareils/logiciels sont livrés avec un identifiant et mot de passe par défaut (admin/admin). Les laisser, c'est laisser la clé sur la porte. Défense : toujours les changer à l'installation."),
    ("c'est quoi un secret en clair", "Un secret en clair (mot de passe, clé d'API, token) écrit dans le code ou un fichier peut fuiter et donner un accès direct. Défense : variables d'environnement, coffres à secrets, et un scanner comme ton outil dataguard pour les repérer."),
    ("c'est quoi l'exposition de données sensibles", "C'est quand des données privées (mots de passe, cartes) circulent ou sont stockées sans protection. Défense : chiffrement en transit (HTTPS) et au repos, et ne garder que le strict nécessaire."),
    ("c'est quoi un composant obsolète", "Utiliser une bibliothèque ou un système non mis à jour expose à des failles déjà connues et publiées. Défense : tenir l'inventaire des dépendances et tout mettre à jour régulièrement."),
    ("c'est quoi un débordement de tampon", "Le débordement de tampon (buffer overflow) écrit au-delà de la zone mémoire prévue, ce qui peut planter ou détourner un programme (surtout en C/C++). Défense : langages/fonctions sûrs, vérifier les tailles, protections mémoire du système."),
    ("c'est quoi l'exécution de code à distance", "L'exécution de code à distance (RCE) permet à un attaquant de faire tourner ses commandes sur une machine cible : c'est parmi les failles les plus graves. Défense : valider les entrées, isoler les services, et patcher vite."),
    ("c'est quoi le path traversal", "Le path traversal (traversée de répertoire) abuse d'un chemin de fichier (../../) pour lire des fichiers hors du dossier autorisé. Défense : nettoyer/normaliser les chemins et n'autoriser qu'un dossier précis."),
    ("c'est quoi le ssrf", "Le SSRF (server-side request forgery) pousse un serveur à faire des requêtes à la place de l'attaquant, parfois vers des ressources internes. Défense : restreindre les URLs autorisées et filtrer les destinations."),
    ("c'est quoi une élévation de privilèges", "L'élévation de privilèges, c'est passer d'un accès limité à un accès administrateur en exploitant une faille. Défense : moindre privilège, mises à jour, et séparation stricte des rôles."),
    ("c'est quoi un déni de service", "Le déni de service (DoS/DDoS) sature un service de requêtes pour le rendre indisponible. Défense : limitation de débit, filtrage, et services anti-DDoS en amont."),
    ("c'est quoi une attaque de l'homme du milieu", "L'homme du milieu (man-in-the-middle) intercepte la communication entre deux parties pour l'espionner ou la modifier. Défense : HTTPS/TLS, vérifier les certificats, éviter les wifi publics non protégés."),
    ("c'est quoi une faille zero day", "Une faille zero-day est une vulnérabilité inconnue de l'éditeur, donc sans correctif au moment où elle est exploitée. Défense : défense en profondeur, détection d'anomalies, et appliquer le patch dès qu'il sort."),
    ("c'est quoi un téléversement de fichier dangereux", "Permettre d'envoyer un fichier sans contrôle peut laisser déposer un script malveillant. Défense : vérifier le type et la taille, renommer, stocker hors de la racine web, et ne pas exécuter les fichiers reçus."),
    ("c'est quoi une redirection ouverte", "Une redirection ouverte (open redirect) utilise un site de confiance pour rediriger la victime vers un site piège. Défense : n'autoriser que des destinations connues, pas d'URL libre dans le paramètre."),
    ("c'est quoi l'owasp top 10", "L'OWASP Top 10 est la liste de référence des risques de sécurité web les plus courants (contrôle d'accès cassé, injection, mauvaise config...). C'est un excellent point de départ pour apprendre les failles et les défenses."),
    ("comment chercher des failles légalement", "Sur tes propres machines/labos, dans un programme de bug bounty qui t'y autorise, ou sur des CTF. La règle d'or : pas d'autorisation écrite = illégal, même 'pour aider'."),
    ("c'est quoi le bug bounty", "Le bug bounty est un programme où une entreprise t'autorise à chercher des failles sur ses systèmes et te récompense si tu en trouves et les signales correctement. C'est légal, encadré, et ça peut payer."),
    ("c'est quoi un cve", "Un CVE est l'identifiant public standard d'une faille connue (ex : CVE-2021-44228). Suivre les CVE de tes logiciels permet de savoir quoi corriger en priorité."),
]


if __name__ == "__main__":
    if os.path.exists(FICHIER):
        failles = Discussion.charger(FICHIER)
        print("J'ai rechargé tout ce que je sais sur les failles. 🛡️")
    else:
        print("Je révise les familles de failles...")
        failles = Discussion(CONNAISSANCES_FAILLES, cachees=20, seed=0)
        failles.entrainer(epochs=4000, taux=0.3)
        failles.sauvegarder(FICHIER)

    print("Prêt ! " + AIDE + "\n")

    while True:
        try:
            phrase = input("Toi : ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nMonIA : Au revoir, et code en sécurité !")
            break

        if phrase.lower() in {"quitter", "stop", "exit", "quit"}:
            print("MonIA : Au revoir, et code en sécurité !")
            break
        if not phrase:
            continue
        if phrase.lower() in {"aide", "help", "?"}:
            print("MonIA :\n" + AIDE)
            continue

        if phrase.lower().startswith("apprends"):
            corps = phrase.split(":", 1)[1] if ":" in phrase else ""
            if SEPARATEUR not in corps:
                print(f"MonIA : Écris :  apprends: ta question {SEPARATEUR} ton explication")
                continue
            question, explication = corps.split(SEPARATEUR, 1)
            question, explication = question.strip(), explication.strip()
            if not question or not explication:
                print("MonIA : Il me faut une question ET une explication.")
                continue
            failles.apprendre(question, explication)
            failles.sauvegarder(FICHIER)
            print(f"MonIA : Note apprise ! « {question} »")
            continue

        print("MonIA : " + failles.repondre(phrase))

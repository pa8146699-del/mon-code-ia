#!/usr/bin/env python3
"""Leçon 10 — La cybersécurité : comprendre les attaques pour mieux se défendre.

Cet assistant t'apprend la cybersécurité : ce que c'est, comment les attaques
fonctionnent, et surtout comment te protéger. Il couvre les deux côtés —
l'attaque ET la défense — parce qu'on ne peut pas se protéger de ce qu'on ne
comprend pas.

⚠️ À lire, c'est important : comprendre une attaque est légal et utile ;
l'utiliser contre les systèmes des autres ne l'est pas. Pirater une machine sans
autorisation est un délit. Pour pratiquer « sans limite » et en toute légalité :
fais-le sur TES propres machines, ou sur des plateformes faites pour ça (les
CTF, « Capture The Flag »). Demande-lui « comment apprendre le hacking
légalement » pour les détails.

Même moteur que le chatbot (`discussion.py`). Il comprend les reformulations,
avoue quand il ne sait pas, apprend tes notes en direct (`apprends: ... >>> ...`)
et retient tout dans `cyber.json`.

Lancer :  python3 cyber.py
"""

import os

from discussion import Discussion, boucle

FICHIER = os.path.join(os.path.dirname(__file__), "cyber.json")
SEPARATEUR = ">>>"

AIDE = (
    "Pose ta question de cybersécurité, je t'explique.\n"
    "  exemples :  c'est quoi le phishing ?  |  comment faire un bon mot de passe ?\n"
    "M'apprendre une note :  apprends: ta question " + SEPARATEUR + " ton explication\n"
    "Autres :  aide   |   quitter"
)

# Base de connaissances : concepts de cybersécurité (défense + compréhension).
CONNAISSANCES_CYBER = [
    ("c'est quoi la cybersécurité", "La cybersécurité, c'est l'ensemble des moyens pour protéger les ordinateurs, les téléphones, les réseaux et les données contre les attaques, le vol et la casse."),
    ("c'est quoi le phishing", "Le phishing (hameçonnage) est un faux message (mail, SMS) qui imite une vraie entreprise pour te pousser à donner ton mot de passe ou ta carte bancaire. Indices : urgence, fautes, adresse bizarre, lien trompeur. Ton outil dataguard sait les détecter."),
    ("comment reconnaître un phishing", "Méfie-toi des messages urgents, des liens qui ne mènent pas au vrai site, des fautes d'orthographe, des demandes de mot de passe ou de carte. En cas de doute, ne clique pas et va sur le site officiel toi-même."),
    ("comment faire un bon mot de passe", "Long (12+ caractères), unique pour chaque site, mélangeant majuscules, minuscules, chiffres et symboles. Le mieux : une phrase de passe et un gestionnaire de mots de passe. Ton outil toolkit dans dataguard mesure leur force."),
    ("c'est quoi la double authentification", "La double authentification (2FA) ajoute une 2e preuve en plus du mot de passe : un code sur ton téléphone, une appli, une clé. Même si on vole ton mot de passe, on ne peut pas entrer sans le 2e facteur. Active-la partout."),
    ("c'est quoi un malware", "Un malware est un logiciel malveillant. Familles : virus (se propage), ver, cheval de Troie (caché dans un vrai logiciel), ransomware (chiffre tes fichiers et demande une rançon), spyware (espionne)."),
    ("c'est quoi un ransomware", "Un ransomware chiffre tes fichiers et réclame une rançon pour les rendre. La meilleure défense : des sauvegardes régulières hors-ligne, pour pouvoir tout restaurer sans payer."),
    ("c'est quoi un cheval de troie", "Un cheval de Troie (trojan) est un programme qui a l'air utile mais cache une fonction malveillante. C'est pourquoi on n'installe que depuis des sources de confiance."),
    ("c'est quoi un virus", "Un virus est un programme malveillant qui se copie d'un fichier à l'autre pour se propager. Un antivirus à jour et la prudence aux téléchargements limitent le risque."),
    ("c'est quoi un pare-feu", "Un pare-feu (firewall) filtre les connexions réseau : il laisse passer ce qui est autorisé et bloque le reste. C'est une porte d'entrée contrôlée pour ta machine ou ton réseau."),
    ("c'est quoi un vpn", "Un VPN crée un tunnel chiffré entre ton appareil et un serveur : ton fournisseur d'accès ne voit plus ce que tu fais, et les sites voient l'adresse du serveur. Utile sur le wifi public, mais ça ne te rend pas anonyme."),
    ("c'est quoi le chiffrement", "Le chiffrement transforme des données en charabia illisible sans la clé. C'est ce qui protège tes messages et le HTTPS. Sans la bonne clé, les données volées sont inutilisables."),
    ("c'est quoi le https", "HTTPS, c'est du HTTP chiffré : le cadenas dans le navigateur veut dire que la connexion entre toi et le site est protégée contre l'espionnage. Évite de saisir des infos sensibles sur un site en simple HTTP."),
    ("c'est quoi l'ingénierie sociale", "L'ingénierie sociale manipule les humains plutôt que les machines : se faire passer pour le support, créer l'urgence, jouer sur la confiance. La défense, c'est la vigilance et la vérification."),
    ("c'est quoi une vulnérabilité", "Une vulnérabilité est une faille dans un logiciel ou une configuration qu'un attaquant peut exploiter. On les corrige avec les mises à jour — d'où l'importance de tout garder à jour."),
    ("c'est quoi une attaque par force brute", "La force brute essaie un maximum de mots de passe jusqu'à trouver le bon. Défenses : mots de passe longs, limiter les tentatives, et la double authentification."),
    ("c'est quoi un keylogger", "Un keylogger enregistre tout ce que tu tapes au clavier pour voler tes mots de passe. Il arrive souvent via un malware ; antivirus, prudence et 2FA limitent les dégâts."),
    ("le wifi public est-il dangereux", "Oui : sur un wifi public, quelqu'un peut tenter d'intercepter ton trafic. Privilégie le HTTPS, évite les opérations sensibles, et utilise un VPN si possible."),
    ("c'est quoi une fuite de données", "Une fuite de données, c'est quand des informations (emails, mots de passe) d'un service se retrouvent exposées. Réflexe : change le mot de passe concerné et active la 2FA. Ton outil dataguard aide à repérer des secrets exposés."),
    ("c'est quoi un hacker", "Un hacker est quelqu'un qui comprend les systèmes en profondeur. Les 'white hats' protègent (avec autorisation), les 'black hats' attaquent illégalement, les 'grey hats' sont entre les deux. Le hacking éthique est un vrai métier."),
    ("c'est quoi le hacking éthique", "Le hacking éthique (pentest), c'est chercher des failles AVEC l'autorisation du propriétaire, pour l'aider à se protéger. C'est légal, encadré par un contrat, et très demandé."),
    ("est-ce légal de pirater", "Attaquer un système sans autorisation est illégal, même 'pour tester'. Ce qui est légal : tes propres machines, un labo que tu montes, ou des plateformes prévues pour ça (CTF). L'autorisation écrite fait toute la différence."),
    ("comment apprendre le hacking légalement", "Monte ton propre labo (machines virtuelles), entraîne-toi sur des plateformes légales et des CTF (Capture The Flag), apprends le réseau et Linux. Tu attaques des cibles faites pour être attaquées — sans limite et sans risque juridique."),
    ("c'est quoi un ctf", "Un CTF (Capture The Flag) est un jeu de cybersécurité où tu résous des défis (crypto, web, reverse...) pour trouver des 'flags'. C'est la façon la plus fun et légale de progresser en hacking."),
    ("comment réagir si je suis piraté", "Déconnecte l'appareil d'internet, change tes mots de passe depuis un appareil sain, active la 2FA, vérifie tes comptes (banque, mail), et restaure depuis une sauvegarde si besoin."),
    ("comment protéger mon téléphone", "Mets à jour le système et les applis, n'installe que depuis les magasins officiels, verrouille avec un code/biométrie, active le chiffrement et la 2FA, et méfie-toi des liens dans les SMS."),
    ("c'est quoi le dark web", "Le dark web est une partie d'internet accessible seulement avec des outils spéciaux (comme Tor). On y trouve du légal comme de l'illégal ; des données volées s'y revendent. Mieux vaut savoir ce que c'est que d'y traîner."),
]


if __name__ == "__main__":
    import sys

    voix = "voix" in sys.argv

    if os.path.exists(FICHIER):
        cyber = Discussion.charger(FICHIER)
        print("J'ai rechargé tout ce que je sais en cybersécurité. 🛡️")
    else:
        print("Je révise la cybersécurité...")
        cyber = Discussion(CONNAISSANCES_CYBER, cachees=20, seed=0)
        cyber.entrainer(epochs=4000, taux=0.3)
        cyber.sauvegarder(FICHIER)

    boucle(cyber, FICHIER, separateur=SEPARATEUR, aide=AIDE, voix=voix)

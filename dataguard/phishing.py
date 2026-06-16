#!/usr/bin/env python3
"""DataGuard — analyseur anti-phishing.

Analyse un texte (e-mail, message, SMS) et calcule un score de risque
d'hameçonnage à partir d'indices heuristiques : langage d'urgence,
demande d'identifiants, liens suspects, domaines sosies, etc.

100 % hors-ligne, aucune dépendance externe.
"""

import re
from dataclasses import dataclass

# --- Listes d'indices ------------------------------------------------------

# Mots/expressions qui créent un sentiment d'urgence ou de pression.
URGENCY_TERMS = [
    "urgent", "immédiatement", "immediatement", "dès maintenant", "des maintenant",
    "agissez maintenant", "act now", "dernier avertissement", "expire", "suspendu",
    "suspendue", "bloqué", "bloque", "bloquée", "désactivé", "desactive",
    "votre compte sera", "sous 24 heures", "sous 48 heures", "verify now",
    "vérifiez maintenant", "verifiez maintenant",
]

# Demandes d'informations confidentielles.
CREDENTIAL_TERMS = [
    "mot de passe", "password", "identifiant", "identifiants", "code pin",
    "code secret", "numéro de carte", "numero de carte", "carte bancaire",
    "cvv", "code de sécurité", "code de securite", "confirmez vos",
    "confirmer vos", "mettez à jour vos", "mettez a jour vos", "vos coordonnées bancaires",
    "vos coordonnees bancaires", "connectez-vous", "saisissez vos",
]

# Salutations génériques typiques des envois de masse.
GENERIC_GREETINGS = [
    "cher client", "chère cliente", "chere cliente", "cher utilisateur",
    "dear customer", "dear user", "cher membre", "bonjour cher",
]

# TLD souvent associés à des campagnes malveillantes.
SUSPICIOUS_TLDS = {".xyz", ".top", ".tk", ".ml", ".ga", ".cf", ".gq", ".zip", ".mov"}

# Raccourcisseurs d'URL qui masquent la vraie destination.
URL_SHORTENERS = {
    "bit.ly", "tinyurl.com", "goo.gl", "t.co", "ow.ly", "is.gd", "buff.ly",
    "cutt.ly", "rebrand.ly", "shorturl.at",
}

# Marques fréquemment usurpées (pour repérer les domaines sosies).
COMMON_BRANDS = [
    "paypal", "google", "apple", "microsoft", "amazon", "netflix", "facebook",
    "instagram", "impots", "ameli", "laposte", "orange", "free", "sfr",
    "bnpparibas", "creditagricole", "societegenerale", "banque",
]

URL_REGEX = re.compile(r"https?://[^\s<>\"')]+", re.IGNORECASE)
DOMAIN_REGEX = re.compile(r"https?://([^/\s:]+)", re.IGNORECASE)
ATTACHMENT_REGEX = re.compile(
    r"\b[\w\-. ]+\.(?:exe|scr|zip|rar|js|vbs|bat|cmd|iso|docm|xlsm)\b", re.IGNORECASE
)


@dataclass
class PhishingSignal:
    """Un indice d'hameçonnage relevé dans le texte."""

    category: str
    detail: str
    weight: int


def _contains_any(text: str, terms: list[str]) -> list[str]:
    """Retourne les termes présents dans le texte (insensible à la casse)."""
    low = text.lower()
    return [t for t in terms if t in low]


def _looks_like_lookalike(domain: str) -> str | None:
    """Détecte un domaine qui imite une marque connue sans être officiel.

    Exemple : 'paypa1.com', 'g00gle-secure.net', 'apple.verify-login.com'.
    Retourne la marque imitée si suspicion, sinon None.
    """
    host = domain.lower().split(":")[0]
    # Caractères trompeurs : chiffres remplaçant des lettres.
    normalized = (
        host.replace("0", "o").replace("1", "l").replace("3", "e").replace("5", "s")
    )
    for brand in COMMON_BRANDS:
        if brand in normalized:
            # Domaine officiel approximatif : brand.tld ou www.brand.tld
            labels = host.split(".")
            # Le label principal (avant le TLD) est-il exactement la marque ?
            main = labels[-2] if len(labels) >= 2 else host
            if main == brand:
                return None  # ressemble au domaine légitime
            # La marque apparaît ailleurs (sous-domaine, tirets, sosie).
            return brand
    return None


def analyze(text: str) -> tuple[int, list[PhishingSignal]]:
    """Analyse un texte et retourne (score 0-100, liste d'indices)."""
    signals: list[PhishingSignal] = []

    for term in _contains_any(text, URGENCY_TERMS):
        signals.append(PhishingSignal("Urgence", f"Expression de pression : « {term} »", 10))

    for term in _contains_any(text, CREDENTIAL_TERMS):
        signals.append(
            PhishingSignal("Identifiants", f"Demande d'information sensible : « {term} »", 15)
        )

    for term in _contains_any(text, GENERIC_GREETINGS):
        signals.append(
            PhishingSignal("Salutation", f"Salutation générique : « {term} »", 5)
        )

    # Analyse des URLs.
    urls = URL_REGEX.findall(text)
    domains = DOMAIN_REGEX.findall(text)
    for url in urls:
        if not url.lower().startswith("https://"):
            signals.append(PhishingSignal("Lien", f"Lien non sécurisé (http) : {url}", 8))
        if "xn--" in url.lower():
            signals.append(PhishingSignal("Lien", f"Domaine punycode trompeur : {url}", 20))

    for domain in domains:
        host = domain.lower().split(":")[0]
        # URL basée sur une adresse IP.
        if re.fullmatch(r"(?:\d{1,3}\.){3}\d{1,3}", host):
            signals.append(PhishingSignal("Lien", f"Lien vers une adresse IP : {host}", 20))
        if host in URL_SHORTENERS:
            signals.append(
                PhishingSignal("Lien", f"Raccourcisseur d'URL masquant la cible : {host}", 12)
            )
        if any(host.endswith(tld) for tld in SUSPICIOUS_TLDS):
            signals.append(PhishingSignal("Lien", f"Extension de domaine à risque : {host}", 12))
        if host.count(".") >= 4:
            signals.append(
                PhishingSignal("Lien", f"Domaine à sous-domaines multiples : {host}", 8)
            )
        brand = _looks_like_lookalike(host)
        if brand:
            signals.append(
                PhishingSignal(
                    "Sosie",
                    f"Domaine imitant « {brand} » sans être officiel : {host}",
                    25,
                )
            )

    # Pièces jointes dangereuses.
    for att in ATTACHMENT_REGEX.findall(text):
        signals.append(
            PhishingSignal("Pièce jointe", f"Type de fichier à risque mentionné : {att}", 15)
        )

    score = min(100, sum(s.weight for s in signals))
    return score, signals


def risk_level(score: int) -> str:
    """Convertit un score en niveau lisible."""
    if score >= 60:
        return "ÉLEVÉ"
    if score >= 30:
        return "MOYEN"
    if score > 0:
        return "FAIBLE"
    return "AUCUN"

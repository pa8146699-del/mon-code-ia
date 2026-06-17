#!/usr/bin/env python3
"""DataGuard — analyseur anti-phishing.

Analyse un texte (e-mail, message, SMS) et calcule un score de risque
d'hameçonnage à partir d'indices heuristiques : langage d'urgence,
demande d'identifiants, liens suspects, domaines sosies, etc.

100 % hors-ligne, aucune dépendance externe.
"""

import re
from dataclasses import dataclass

# --- Listes d'indices ---------------------------------------------------------

URGENCY_TERMS = [
    # Français
    "urgent", "immédiatement", "immediatement", "dès maintenant", "des maintenant",
    "agissez maintenant", "dernier avertissement", "expire", "suspendu",
    "suspendue", "bloqué", "bloque", "bloquée", "désactivé", "desactive",
    "votre compte sera", "sous 24 heures", "sous 48 heures", "dans les 24",
    "dans les 48", "48h", "24h", "vérifiez maintenant", "verifiez maintenant",
    "accès restreint", "acces restreint", "compte bloqué", "compte suspendu",
    "avertissement final", "dernière chance", "derniere chance",
    # Anglais
    "act now", "verify now", "immediate action", "action required",
    "limited time", "expires soon", "your account has been", "warning:",
    "final notice", "last chance", "account suspended", "account locked",
    "unusual activity", "suspicious activity",
]

CREDENTIAL_TERMS = [
    # Français
    "mot de passe", "identifiant", "identifiants", "code pin",
    "code secret", "numéro de carte", "numero de carte", "carte bancaire",
    "cvv", "code de sécurité", "code de securite", "confirmez vos",
    "confirmer vos", "mettez à jour vos", "mettez a jour vos",
    "vos coordonnées bancaires", "vos coordonnees bancaires",
    "connectez-vous", "saisissez vos", "numéro de sécurité sociale",
    "numero de securite sociale", "code de vérification",
    # Anglais
    "password", "username", "enter your", "social security", "ssn",
    "authentication code", "one-time password", "otp", "2fa code",
    "credit card", "bank account", "routing number", "verify your",
]

GENERIC_GREETINGS = [
    "cher client", "chère cliente", "chere cliente", "cher utilisateur",
    "dear customer", "dear user", "cher membre", "bonjour cher",
    "valued customer", "dear account holder",
]

FAKE_SECURITY_TERMS = [
    "système sécurisé", "systeme securise", "connexion sécurisée",
    "official notice", "avis officiel", "we have detected",
    "nous avons détecté", "nous avons detecte", "votre appareil a été",
    "your device has been", "virus detected", "your computer is infected",
]

SUSPICIOUS_TLDS = {
    ".xyz", ".top", ".tk", ".ml", ".ga", ".cf", ".gq",
    ".zip", ".mov", ".club", ".work", ".date", ".faith",
    ".loan", ".win", ".bid", ".stream",
}

URL_SHORTENERS = {
    "bit.ly", "tinyurl.com", "goo.gl", "t.co", "ow.ly", "is.gd",
    "buff.ly", "cutt.ly", "rebrand.ly", "shorturl.at",
    "rb.gy", "qr.ae", "bl.ink", "short.io", "v.gd",
}

COMMON_BRANDS = [
    "paypal", "google", "apple", "microsoft", "amazon", "netflix",
    "facebook", "instagram", "impots", "ameli", "laposte", "orange",
    "free", "sfr", "bnpparibas", "creditagricole", "societegenerale",
    "banque", "twitter", "linkedin", "ebay", "dhl", "fedex", "ups",
    "caf", "securitesociale", "assurancemaladie",
]

URL_REGEX = re.compile(r"https?://[^\s<>\"')]+", re.IGNORECASE)
DOMAIN_REGEX = re.compile(r"https?://([^/\s:]+)", re.IGNORECASE)
ATTACHMENT_REGEX = re.compile(
    r"\b[\w\-. ]+\.(?:exe|scr|zip|rar|js|vbs|bat|cmd|iso|docm|xlsm|ps1|lnk)\b",
    re.IGNORECASE,
)
PUNYCODE_REGEX = re.compile(r"xn--[a-z0-9\-]+", re.IGNORECASE)


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
    """Détecte un domaine qui imite une marque connue sans être officiel."""
    host = domain.lower().split(":")[0]
    normalized = (
        host.replace("0", "o").replace("1", "l").replace("3", "e").replace("5", "s")
    )
    for brand in COMMON_BRANDS:
        if brand in normalized:
            labels = host.split(".")
            main = labels[-2] if len(labels) >= 2 else host
            if main == brand:
                return None
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
        signals.append(PhishingSignal("Salutation", f"Salutation générique : « {term} »", 5))

    for term in _contains_any(text, FAKE_SECURITY_TERMS):
        signals.append(
            PhishingSignal("Fausse sécurité", f"Discours de sécurité trompeur : « {term} »", 12)
        )

    # Analyse des URLs.
    urls = URL_REGEX.findall(text)
    domains = DOMAIN_REGEX.findall(text)

    for url in urls:
        if not url.lower().startswith("https://"):
            signals.append(PhishingSignal("Lien", f"Lien non sécurisé (http) : {url[:60]}", 8))
        if PUNYCODE_REGEX.search(url):
            signals.append(
                PhishingSignal("Lien", f"Domaine punycode (homoglyphe) : {url[:60]}", 25)
            )

    for domain in domains:
        host = domain.lower().split(":")[0]
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

"""toolkit.py — outils de cybersécurité complémentaires (stdlib uniquement).

Regroupe des utilitaires sans dépendance externe, réutilisables par toutes les
interfaces (CLI, mobile) au même titre que detectors.py et phishing.py :

- ``password_strength(pw)``  — analyse la robustesse d'un mot de passe.
- ``generate_password(...)`` — génère un mot de passe aléatoire sûr.
- ``hash_text(text)``        — calcule les empreintes (SHA-256, SHA-1, MD5).

Aucune valeur sensible n'est journalisée ; tout reste en mémoire.
"""

from __future__ import annotations

import hashlib
import math
import secrets
import string
from dataclasses import dataclass, field

# Mots de passe les plus répandus : à bannir quel que soit le reste.
COMMON_PASSWORDS = {
    "123456", "password", "123456789", "12345678", "12345", "qwerty",
    "azerty", "111111", "123123", "motdepasse", "admin", "welcome",
    "iloveyou", "abc123", "000000", "password1", "root", "toor", "1234",
    "123321", "azertyuiop", "qwertyuiop", "soleil", "loulou", "doudou",
}

# Suites évidentes (clavier et alphabet) recherchées en sous-chaîne.
_SEQUENCES = ("abcdefghijklmnopqrstuvwxyz", "0123456789", "azertyuiop", "qwertyuiop")


@dataclass
class PasswordReport:
    """Résultat de l'analyse d'un mot de passe."""

    score: int                       # 0-100
    level: str                       # TRÈS FAIBLE … TRÈS FORT
    entropy_bits: float              # estimation de l'entropie
    issues: list[str] = field(default_factory=list)   # problèmes bloquants
    tips: list[str] = field(default_factory=list)      # conseils d'amélioration


def _has_sequence(low: str) -> bool:
    """Vrai si le mot de passe contient une suite de 3+ caractères connus."""
    for seq in _SEQUENCES:
        for i in range(len(seq) - 2):
            if seq[i:i + 3] in low:
                return True
    return False


def _too_repetitive(pw: str) -> bool:
    """Vrai si un caractère revient 3 fois de suite ou domine le mot de passe."""
    if not pw:
        return False
    for i in range(len(pw) - 2):
        if pw[i] == pw[i + 1] == pw[i + 2]:
            return True
    most_common = max(pw.count(c) for c in set(pw))
    return most_common > len(pw) / 2


def password_strength(pw: str) -> PasswordReport:
    """Évalue la robustesse d'un mot de passe (score 0-100 + conseils)."""
    if not pw:
        return PasswordReport(0, "TRÈS FAIBLE", 0.0, issues=["Mot de passe vide."])

    length = len(pw)
    has_lower = any(c.islower() for c in pw)
    has_upper = any(c.isupper() for c in pw)
    has_digit = any(c.isdigit() for c in pw)
    has_symbol = any(not c.isalnum() for c in pw)

    pool = (26 if has_lower else 0) + (26 if has_upper else 0)
    pool += (10 if has_digit else 0) + (32 if has_symbol else 0)
    pool = pool or 1
    entropy = length * math.log2(pool)

    issues: list[str] = []
    tips: list[str] = []
    if length < 12:
        tips.append("Vise au moins 12 à 16 caractères.")
    if not has_upper:
        tips.append("Ajoute des majuscules.")
    if not has_lower:
        tips.append("Ajoute des minuscules.")
    if not has_digit:
        tips.append("Ajoute des chiffres.")
    if not has_symbol:
        tips.append("Ajoute des caractères spéciaux (! ? # …).")

    low = pw.lower()
    penalty = 0
    if low in COMMON_PASSWORDS:
        issues.append("Mot de passe très courant, à bannir.")
    if _has_sequence(low):
        issues.append("Contient une suite évidente (abc, 123, azerty…).")
        penalty += 15
    if _too_repetitive(pw):
        issues.append("Trop de caractères répétés.")
        penalty += 15

    # ~80 bits d'entropie ≈ score maximal.
    score = int(min(100, entropy / 80 * 100))
    score = max(0, score - penalty)
    if low in COMMON_PASSWORDS:
        score = min(score, 5)

    if score < 20:
        level = "TRÈS FAIBLE"
    elif score < 40:
        level = "FAIBLE"
    elif score < 60:
        level = "MOYEN"
    elif score < 80:
        level = "FORT"
    else:
        level = "TRÈS FORT"

    return PasswordReport(score, level, round(entropy, 1), issues, tips)


def generate_password(length: int = 16, use_symbols: bool = True) -> str:
    """Génère un mot de passe aléatoire sûr (module ``secrets``).

    Garantit la présence d'au moins une minuscule, une majuscule, un chiffre
    (et un symbole si demandé). Longueur minimale forcée à 8.
    """
    length = max(8, length)
    lower, upper, digits = string.ascii_lowercase, string.ascii_uppercase, string.digits
    symbols = "!@#$%^&*()-_=+[]{}" if use_symbols else ""

    pools = [lower, upper, digits] + ([symbols] if symbols else [])
    alphabet = "".join(pools)

    # Au moins un caractère de chaque catégorie requise.
    chars = [secrets.choice(p) for p in pools]
    chars += [secrets.choice(alphabet) for _ in range(length - len(chars))]

    # Mélange cryptographiquement sûr (pas random.shuffle).
    for i in range(len(chars) - 1, 0, -1):
        j = secrets.randbelow(i + 1)
        chars[i], chars[j] = chars[j], chars[i]
    return "".join(chars)


def hash_text(text: str) -> dict[str, str]:
    """Renvoie les empreintes SHA-256, SHA-1 et MD5 du texte (UTF-8)."""
    data = text.encode("utf-8")
    return {
        "SHA-256": hashlib.sha256(data).hexdigest(),
        "SHA-1": hashlib.sha1(data).hexdigest(),
        "MD5": hashlib.md5(data).hexdigest(),
    }

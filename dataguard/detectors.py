#!/usr/bin/env python3
"""DataGuard — détecteurs de données sensibles."""

import re
from dataclasses import dataclass
from pathlib import Path

# --- Niveaux de gravité -------------------------------------------------------

SEVERITY_HIGH = "élevée"
SEVERITY_MEDIUM = "moyenne"
SEVERITY_LOW = "faible"

SEVERITY_ORDER = {SEVERITY_HIGH: 0, SEVERITY_MEDIUM: 1, SEVERITY_LOW: 2}


@dataclass
class Detector:
    name: str
    regex: re.Pattern
    severity: str


# --- Catalogue de détecteurs --------------------------------------------------
#
# Pour étendre la couverture, ajoute simplement un Detector ici.

DETECTORS: list[Detector] = [

    # --- Clés privées ----------------------------------------------------------
    Detector(
        "Clé privée",
        re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |PGP )?PRIVATE KEY-----"),
        SEVERITY_HIGH,
    ),

    # --- Clés API services cloud -----------------------------------------------
    Detector(
        "Clé API AWS",
        re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"),
        SEVERITY_HIGH,
    ),
    Detector(
        "Clé API Anthropic",
        re.compile(r"\bsk-ant-[A-Za-z0-9_\-]{20,}\b"),
        SEVERITY_HIGH,
    ),
    Detector(
        "Clé API OpenAI",
        re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"),
        SEVERITY_HIGH,
    ),
    Detector(
        "Clé Stripe",
        re.compile(r"\b(?:sk|pk|rk)_(?:live|test)_[0-9A-Za-z]{16,}\b"),
        SEVERITY_HIGH,
    ),
    Detector(
        "Clé API Google / Firebase",
        re.compile(r"\bAIza[0-9A-Za-z_\-]{35}\b"),
        SEVERITY_HIGH,
    ),
    Detector(
        "Jeton OAuth Google",
        re.compile(r"\bya29\.[0-9A-Za-z_\-]{20,}\b"),
        SEVERITY_HIGH,
    ),
    Detector(
        "Jeton GitHub",
        re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b"),
        SEVERITY_HIGH,
    ),
    Detector(
        "Jeton Slack",
        re.compile(r"\bxox[baprs]-[0-9A-Za-z\-]{10,}\b"),
        SEVERITY_HIGH,
    ),
    Detector(
        "Clé SendGrid",
        re.compile(r"\bSG\.[A-Za-z0-9_\-]{22}\.[A-Za-z0-9_\-]{43}\b"),
        SEVERITY_HIGH,
    ),
    Detector(
        "Jeton Discord",
        re.compile(r"\b[MN][A-Za-z\d]{23}\.[\w\-]{6}\.[\w\-]{27}\b"),
        SEVERITY_HIGH,
    ),
    Detector(
        "Clé API Twilio",
        re.compile(r"\bSK[0-9a-fA-F]{32}\b"),
        SEVERITY_HIGH,
    ),
    Detector(
        "Clé API Mailgun",
        re.compile(r"\bkey-[a-zA-Z0-9]{32}\b"),
        SEVERITY_HIGH,
    ),

    # --- Connexions base de données --------------------------------------------
    Detector(
        "URL de connexion DB",
        re.compile(
            r"(?i)(?:mysql|postgresql|postgres|mongodb(?:\+srv)?|redis|mssql)"
            r"://[^:\s]+:[^@\s]{3,}@"
        ),
        SEVERITY_HIGH,
    ),
    Detector(
        "Chaîne Azure Storage",
        re.compile(
            r"DefaultEndpointsProtocol=https?;AccountName=[^;]+;"
            r"AccountKey=[A-Za-z0-9+/=]{50,}"
        ),
        SEVERITY_HIGH,
    ),

    # --- Patterns malware ------------------------------------------------------
    Detector(
        "Malware — Reverse shell",
        re.compile(
            r"(?i)(?:/dev/tcp/\d|nc\s+-e\s+/bin/|bash\s+-i\s+>&\s+/dev/tcp|"
            r"ncat\s+--sh-exec|python\d?\s+-c\s+['\"]import\s+socket)"
        ),
        SEVERITY_HIGH,
    ),
    Detector(
        "Malware — Code obfusqué",
        re.compile(
            r"(?i)(?:eval\s*\(\s*base64|exec\s*\(\s*base64|exec\s*\(\s*compile|"
            r"eval\s*\(\s*__import__|__import__\s*\(\s*['\"]os['\"]\s*\)\s*\.system)"
        ),
        SEVERITY_HIGH,
    ),
    Detector(
        "Malware — PowerShell encodé",
        re.compile(r"(?i)-(?:EncodedCommand|enc)\s+[A-Za-z0-9+/=]{50,}"),
        SEVERITY_HIGH,
    ),
    Detector(
        "Malware — Téléchargement pipe shell",
        re.compile(r"(?i)(?:curl|wget)\s+[^\|\n]+\|\s*(?:ba)?sh"),
        SEVERITY_HIGH,
    ),
    Detector(
        "Malware — Cryptomineur",
        re.compile(r"(?i)(?:stratum\+tcp://|xmrig\b|--mining-threads\b|minerd\s+--)"),
        SEVERITY_HIGH,
    ),
    Detector(
        "Malware — Commande destructrice",
        re.compile(r"(?:rm\s+-rf\s+/(?:\s|$)|dd\s+if=/dev/zero\s+of=/dev/|mkfs\.\w+\s+/dev/)"),
        SEVERITY_HIGH,
    ),

    # --- Secrets génériques ---------------------------------------------------
    Detector(
        "Webhook Slack",
        re.compile(r"https://hooks\.slack\.com/services/[A-Za-z0-9/]+"),
        SEVERITY_MEDIUM,
    ),
    Detector(
        "Jeton JWT",
        re.compile(r"\beyJ[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+\b"),
        SEVERITY_MEDIUM,
    ),
    Detector(
        "Mot de passe en clair",
        re.compile(
            r"(?i)(?:password|passwd|mot_de_passe|motdepasse|pwd)\s*[:=]\s*"
            r"['\"]?[^\s'\"]{4,}"
        ),
        SEVERITY_HIGH,
    ),
    Detector(
        "Secret / token générique",
        re.compile(
            r"(?i)(?:secret|api[_\-]?key|token|access[_\-]?key)\s*[:=]\s*"
            r"['\"]?[A-Za-z0-9_\-]{12,}"
        ),
        SEVERITY_MEDIUM,
    ),

    # --- Données personnelles -------------------------------------------------
    Detector(
        "IBAN",
        re.compile(r"\b[A-Z]{2}\d{2}(?:[ ]?[A-Z0-9]{4}){2,7}[ ]?[A-Z0-9]{1,3}\b"),
        SEVERITY_HIGH,
    ),
    Detector(
        "Carte bancaire",
        re.compile(r"\b(?:\d[ \-]?){13,16}\b"),
        SEVERITY_HIGH,
    ),
    Detector(
        "Numéro de téléphone (FR)",
        re.compile(r"\b(?:\+33|0)[1-9](?:[ .\-]?\d{2}){4}\b"),
        SEVERITY_LOW,
    ),
    Detector(
        "Adresse e-mail",
        re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"),
        SEVERITY_LOW,
    ),
    Detector(
        "Adresse IPv4",
        re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
        SEVERITY_LOW,
    ),
]

# Extensions binaires à ignorer lors d'un scan de dossier.
BINARY_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".pdf", ".zip",
    ".gz", ".tar", ".exe", ".dll", ".so", ".dylib", ".pyc", ".bin",
    ".mp3", ".mp4", ".mov", ".avi", ".wav", ".woff", ".woff2", ".ttf",
}

# Dossiers à ne jamais explorer.
SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv", ".mypy_cache"}


@dataclass
class Finding:
    """Une fuite potentielle détectée."""

    file: str
    line: int
    type: str
    severity: str
    excerpt: str


def luhn_valid(number: str) -> bool:
    """Valide un numéro de carte via l'algorithme de Luhn."""
    digits = [int(d) for d in re.sub(r"[ \-]", "", number)]
    if not 13 <= len(digits) <= 16:
        return False
    checksum = 0
    parity = len(digits) % 2
    for i, d in enumerate(digits):
        if i % 2 == parity:
            d *= 2
            if d > 9:
                d -= 9
        checksum += d
    return checksum % 10 == 0


def redact(text: str) -> str:
    """Masque le milieu d'une chaîne sensible pour ne pas la réafficher."""
    text = text.strip()
    if len(text) <= 8:
        return text[0] + "***" if text else "***"
    return f"{text[:4]}***{text[-2:]}"


def scan_line(line: str, line_no: int, file: str) -> list[Finding]:
    """Applique tous les détecteurs à une ligne."""
    findings: list[Finding] = []
    for detector in DETECTORS:
        for match in detector.regex.finditer(line):
            value = match.group(0)
            if detector.name == "Carte bancaire" and not luhn_valid(value):
                continue
            findings.append(
                Finding(
                    file=file,
                    line=line_no,
                    type=detector.name,
                    severity=detector.severity,
                    excerpt=redact(value),
                )
            )
    return findings


def scan_file(path: Path) -> list[Finding]:
    """Scanne un fichier texte ligne par ligne."""
    import sys

    findings: list[Finding] = []
    try:
        with path.open("r", encoding="utf-8", errors="ignore") as f:
            for line_no, line in enumerate(f, start=1):
                findings.extend(scan_line(line, line_no, str(path)))
    except OSError as e:
        print(f"Impossible de lire {path} : {e}", file=sys.stderr)
    return findings


def iter_files(root: Path):
    """Parcourt récursivement les fichiers texte d'un dossier."""
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.suffix.lower() in BINARY_EXTENSIONS:
            continue
        yield path


def scan(target: Path) -> list[Finding]:
    """Scanne un fichier ou un dossier."""
    if target.is_file():
        return scan_file(target)
    if target.is_dir():
        findings: list[Finding] = []
        for path in iter_files(target):
            findings.extend(scan_file(path))
        return findings
    raise FileNotFoundError(f"Cible introuvable : {target}")


def sort_findings(findings: list[Finding]) -> list[Finding]:
    """Trie par gravité décroissante, puis par fichier et ligne."""
    return sorted(
        findings, key=lambda f: (SEVERITY_ORDER[f.severity], f.file, f.line)
    )

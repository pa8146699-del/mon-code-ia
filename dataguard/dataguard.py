#!/usr/bin/env python3
"""DataGuard — scanner anti-fuite de données.

Analyse un fichier ou un dossier et détecte les données sensibles
(clés API, mots de passe, e-mails, numéros de carte bancaire, etc.)
afin d'éviter qu'elles ne fuient avant un partage ou un commit.
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path

# --- Définition des motifs sensibles ---------------------------------------
#
# Chaque détecteur a un nom, une expression régulière compilée et un niveau
# de gravité. La sévérité aide à trier les fuites les plus graves.

SEVERITY_HIGH = "élevée"
SEVERITY_MEDIUM = "moyenne"
SEVERITY_LOW = "faible"


@dataclass
class Detector:
    name: str
    regex: re.Pattern
    severity: str


DETECTORS: list[Detector] = [
    Detector(
        "Clé privée",
        re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |PGP )?PRIVATE KEY-----"),
        SEVERITY_HIGH,
    ),
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
        "Jeton GitHub",
        re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b"),
        SEVERITY_HIGH,
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
    Detector(
        "Adresse e-mail",
        re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"),
        SEVERITY_LOW,
    ),
    Detector(
        "Carte bancaire",
        re.compile(r"\b(?:\d[ \-]?){13,16}\b"),
        SEVERITY_HIGH,
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
            # Réduit les faux positifs sur les cartes bancaires.
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


def print_report(findings: list[Finding]) -> None:
    """Affiche un rapport lisible dans le terminal."""
    if not findings:
        print("✓ Aucune donnée sensible détectée.")
        return

    order = {SEVERITY_HIGH: 0, SEVERITY_MEDIUM: 1, SEVERITY_LOW: 2}
    findings = sorted(findings, key=lambda f: (order[f.severity], f.file, f.line))

    print(f"⚠ {len(findings)} fuite(s) potentielle(s) détectée(s) :\n")
    for f in findings:
        print(f"  [{f.severity:<7}] {f.type}")
        print(f"            {f.file}:{f.line}  →  {f.excerpt}\n")

    high = sum(1 for f in findings if f.severity == SEVERITY_HIGH)
    if high:
        print(f"→ Dont {high} de gravité élevée à corriger en priorité.")


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="dataguard",
        description="Scanne un fichier ou un dossier à la recherche de données sensibles.",
    )
    parser.add_argument("target", help="Fichier ou dossier à analyser")
    parser.add_argument(
        "--json", action="store_true", help="Affiche le résultat au format JSON"
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Code de sortie 1 dès qu'une fuite est trouvée (utile en CI)",
    )
    args = parser.parse_args()

    try:
        findings = scan(Path(args.target))
    except FileNotFoundError as e:
        print(e, file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps([asdict(f) for f in findings], ensure_ascii=False, indent=2))
    else:
        print_report(findings)

    if args.strict and findings:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

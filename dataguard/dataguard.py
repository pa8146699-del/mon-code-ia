#!/usr/bin/env python3
"""DataGuard — boîte à outils anti-fuite de données et anti-phishing.

Sous-commandes :
  scan          Analyse un fichier/dossier à la recherche de données sensibles.
  phishing      Évalue le risque d'hameçonnage d'un texte ou d'un e-mail.
  install-hook  Installe un hook git pre-commit qui bloque les fuites.

Aucune dépendance externe : bibliothèque standard de Python 3 uniquement.
"""

import argparse
import json
import stat
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path

import detectors
import phishing
from report import build_html


# --- Sous-commande : scan --------------------------------------------------

def print_report(findings: list[detectors.Finding]) -> None:
    """Affiche un rapport lisible dans le terminal."""
    if not findings:
        print("✓ Aucune donnée sensible détectée.")
        return

    findings = detectors.sort_findings(findings)
    print(f"⚠ {len(findings)} fuite(s) potentielle(s) détectée(s) :\n")
    for f in findings:
        print(f"  [{f.severity:<7}] {f.type}")
        print(f"            {f.file}:{f.line}  →  {f.excerpt}\n")

    high = sum(1 for f in findings if f.severity == detectors.SEVERITY_HIGH)
    if high:
        print(f"→ Dont {high} de gravité élevée à corriger en priorité.")


def cmd_scan(args: argparse.Namespace) -> int:
    try:
        findings = detectors.scan(Path(args.target))
    except FileNotFoundError as e:
        print(e, file=sys.stderr)
        return 2

    if args.html:
        Path(args.html).write_text(
            build_html(findings, args.target), encoding="utf-8"
        )
        print(f"Rapport HTML écrit dans {args.html}")
    elif args.json:
        print(json.dumps([asdict(f) for f in findings], ensure_ascii=False, indent=2))
    else:
        print_report(findings)

    if args.strict and findings:
        return 1
    return 0


# --- Sous-commande : phishing ---------------------------------------------

def cmd_phishing(args: argparse.Namespace) -> int:
    if args.text:
        text = args.text
    elif args.file:
        try:
            text = Path(args.file).read_text(encoding="utf-8", errors="ignore")
        except OSError as e:
            print(e, file=sys.stderr)
            return 2
    else:
        text = sys.stdin.read()

    score, signals = phishing.analyze(text)
    level = phishing.risk_level(score)

    if args.json:
        print(
            json.dumps(
                {
                    "score": score,
                    "level": level,
                    "signals": [
                        {"category": s.category, "detail": s.detail, "weight": s.weight}
                        for s in signals
                    ],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        _print_phishing(text)

    if args.strict and level in {"MOYEN", "ÉLEVÉ"}:
        return 1
    return 0


# --- Sous-commande : install-hook -----------------------------------------

HOOK_TEMPLATE = """#!/bin/sh
# Hook pre-commit installé par DataGuard.
# Bloque le commit si des données sensibles sont détectées dans les
# fichiers indexés.
python3 "{script}" scan-staged --strict
"""


def _git_dir() -> Path | None:
    """Retourne le dossier .git du dépôt courant, ou None."""
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--git-dir"], stderr=subprocess.DEVNULL, text=True
        )
        return Path(out.strip())
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def cmd_install_hook(args: argparse.Namespace) -> int:
    git_dir = _git_dir()
    if git_dir is None:
        print("Erreur : ce dossier n'est pas un dépôt git.", file=sys.stderr)
        return 2

    hooks_dir = git_dir / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    hook_path = hooks_dir / "pre-commit"

    if hook_path.exists() and not args.force:
        print(
            f"Un hook pre-commit existe déjà : {hook_path}\n"
            "Relance avec --force pour l'écraser.",
            file=sys.stderr,
        )
        return 1

    script = Path(__file__).resolve()
    hook_path.write_text(HOOK_TEMPLATE.format(script=script), encoding="utf-8")
    hook_path.chmod(hook_path.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP)
    print(f"✓ Hook pre-commit installé : {hook_path}")
    print("  Les commits contenant des secrets seront désormais bloqués.")
    return 0


def cmd_scan_staged(args: argparse.Namespace) -> int:
    """Scanne uniquement les fichiers indexés (utilisé par le hook git)."""
    try:
        out = subprocess.check_output(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
            text=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"Erreur git : {e}", file=sys.stderr)
        return 2

    files = [Path(p) for p in out.splitlines() if p.strip()]
    findings: list[detectors.Finding] = []
    for path in files:
        if path.is_file() and path.suffix.lower() not in detectors.BINARY_EXTENSIONS:
            findings.extend(detectors.scan_file(path))

    print_report(findings)
    if args.strict and findings:
        print("\n✗ Commit bloqué par DataGuard. Retire les secrets puis recommence.")
        return 1
    return 0


# --- Sous-commande : menu interactif --------------------------------------

MENU = """
========== 🛡️  DataGuard ==========
  1) Scanner un fichier / dossier
  2) Analyser un texte (phishing)
  3) Scanner un texte collé (secrets)
  4) Quitter
===================================="""


def cmd_menu(args: argparse.Namespace) -> int:
    """Menu interactif, pratique au doigt sur téléphone."""
    while True:
        print(MENU)
        try:
            choix = input("Ton choix (1-4) : ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nAu revoir !")
            return 0

        if choix == "1":
            cible = input("Chemin du fichier ou dossier : ").strip()
            if not cible:
                continue
            try:
                print_report(detectors.scan(Path(cible)))
            except FileNotFoundError as e:
                print(e)

        elif choix == "2":
            texte = input("Colle le texte/e-mail à vérifier : ").strip()
            if texte:
                _print_phishing(texte)

        elif choix == "3":
            texte = input("Colle le texte à scanner : ").strip()
            if texte:
                findings: list[detectors.Finding] = []
                for i, ligne in enumerate(texte.splitlines() or [texte], start=1):
                    findings.extend(detectors.scan_line(ligne, i, "(texte)"))
                print_report(findings)

        elif choix in {"4", "q", "quitter", "quit", "exit"}:
            print("Au revoir !")
            return 0

        else:
            print("Choix invalide, tape 1, 2, 3 ou 4.")

        input("\nAppuie sur Entrée pour revenir au menu...")


def _print_phishing(text: str) -> None:
    """Affiche le rapport d'hameçonnage d'un texte (partagé menu/CLI)."""
    score, signals = phishing.analyze(text)
    print(f"\nRisque d'hameçonnage : {phishing.risk_level(score)} (score {score}/100)\n")
    if not signals:
        print("✓ Aucun indice d'hameçonnage relevé.")
    for s in signals:
        print(f"  • [{s.category}] {s.detail}")


# --- Analyseur d'arguments -------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dataguard",
        description="Boîte à outils anti-fuite de données et anti-phishing.",
    )
    # Pas de sous-commande → menu interactif (pratique sur téléphone).
    sub = parser.add_subparsers(dest="command", required=False)

    p_menu = sub.add_parser("menu", help="Menu interactif (mode par défaut)")
    p_menu.set_defaults(func=cmd_menu)

    p_scan = sub.add_parser("scan", help="Analyse un fichier ou un dossier")
    p_scan.add_argument("target", help="Fichier ou dossier à analyser")
    p_scan.add_argument("--json", action="store_true", help="Sortie JSON")
    p_scan.add_argument("--html", metavar="FICHIER", help="Écrit un rapport HTML")
    p_scan.add_argument("--strict", action="store_true", help="Code 1 si fuite trouvée")
    p_scan.set_defaults(func=cmd_scan)

    p_phish = sub.add_parser("phishing", help="Évalue le risque d'hameçonnage d'un texte")
    src = p_phish.add_mutually_exclusive_group()
    src.add_argument("--file", help="Fichier texte à analyser")
    src.add_argument("--text", help="Texte à analyser directement")
    p_phish.add_argument("--json", action="store_true", help="Sortie JSON")
    p_phish.add_argument("--strict", action="store_true", help="Code 1 si risque moyen/élevé")
    p_phish.set_defaults(func=cmd_phishing)

    p_hook = sub.add_parser("install-hook", help="Installe le hook git pre-commit")
    p_hook.add_argument("--force", action="store_true", help="Écrase un hook existant")
    p_hook.set_defaults(func=cmd_install_hook)

    p_staged = sub.add_parser("scan-staged", help="Scanne les fichiers indexés (git)")
    p_staged.add_argument("--strict", action="store_true", help="Code 1 si fuite trouvée")
    p_staged.set_defaults(func=cmd_scan_staged)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    # Sans sous-commande, on lance le menu interactif.
    if getattr(args, "func", None) is None:
        return cmd_menu(args)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

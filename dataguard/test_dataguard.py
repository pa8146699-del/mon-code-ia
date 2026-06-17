#!/usr/bin/env python3
"""Tests pour DataGuard. Lancer avec : python -m pytest dataguard/

Fonctionne aussi sans pytest : python dataguard/test_dataguard.py
"""

from pathlib import Path

import detectors
import phishing
import toolkit
from report import build_html


# --- Détecteurs de secrets -------------------------------------------------

def test_detecte_mot_de_passe():
    findings = detectors.scan_line("password = SuperSecret123", 1, "f")
    assert any(f.type == "Mot de passe en clair" for f in findings)


def test_detecte_cle_aws():
    findings = detectors.scan_line("key=AKIA1234567890ABCDEF", 1, "f")
    assert any(f.type == "Clé API AWS" for f in findings)


def test_detecte_cle_stripe():
    findings = detectors.scan_line("stripe sk_live_abcdefghij1234567890XYZ", 1, "f")
    assert any(f.type == "Clé Stripe" for f in findings)


def test_detecte_cle_google():
    findings = detectors.scan_line("AIzaSyA1234567890abcdefghijklmnopqrstuv", 1, "f")
    assert any(f.type == "Clé API Google" for f in findings)


def test_detecte_iban():
    findings = detectors.scan_line("IBAN FR76 3000 6000 0112 3456 7890 189", 1, "f")
    assert any(f.type == "IBAN" for f in findings)


def test_detecte_email():
    findings = detectors.scan_line("contact: a@b.com", 1, "f")
    assert any(f.type == "Adresse e-mail" for f in findings)


def test_carte_valide_luhn():
    findings = detectors.scan_line("carte 4539 1488 0343 6467", 1, "f")
    assert any(f.type == "Carte bancaire" for f in findings)


def test_carte_invalide_ignoree():
    findings = detectors.scan_line("ref 1234 5678 9012 3456", 1, "f")
    assert not any(f.type == "Carte bancaire" for f in findings)


def test_ligne_propre():
    findings = detectors.scan_line("texte normal sans secret", 1, "f")
    assert findings == []


def test_redaction_masque_le_secret():
    masque = detectors.redact("SuperSecret123")
    assert "SuperSecret123" not in masque
    assert "***" in masque


def test_scan_fichier(tmp_path: Path):
    f = tmp_path / "secrets.txt"
    f.write_text("password = abcd1234\n", encoding="utf-8")
    findings = detectors.scan(f)
    assert len(findings) >= 1


# --- Anti-phishing ---------------------------------------------------------

def test_phishing_texte_propre():
    score, signals = phishing.analyze("Bonjour, voici le compte-rendu de la réunion.")
    assert score == 0
    assert signals == []


def test_phishing_urgence_et_identifiants():
    text = (
        "URGENT : votre compte sera suspendu. Confirmez vos identifiants "
        "et votre numéro de carte immédiatement."
    )
    score, signals = phishing.analyze(text)
    assert score > 0
    assert any(s.category == "Identifiants" for s in signals)
    assert phishing.risk_level(score) in {"MOYEN", "ÉLEVÉ"}


def test_phishing_domaine_sosie():
    score, signals = phishing.analyze("Connectez-vous sur http://paypa1-secure.com/login")
    assert any(s.category == "Sosie" for s in signals)


def test_phishing_lien_ip():
    score, signals = phishing.analyze("Cliquez ici http://192.168.0.5/verify")
    assert any("adresse IP" in s.detail for s in signals)


def test_phishing_domaine_legitime_non_signale():
    score, signals = phishing.analyze("Voir https://www.paypal.com/fr/account")
    assert not any(s.category == "Sosie" for s in signals)


# --- Boîte à outils (mots de passe, hash) ----------------------------------

def test_mot_de_passe_courant_tres_faible():
    rapport = toolkit.password_strength("123456")
    assert rapport.level == "TRÈS FAIBLE"
    assert rapport.score <= 5
    assert any("courant" in i for i in rapport.issues)


def test_mot_de_passe_solide_bien_note():
    rapport = toolkit.password_strength("J8!vQ2#mZ9pL@wR4")
    assert rapport.level in {"FORT", "TRÈS FORT"}
    assert rapport.score >= 60


def test_mot_de_passe_vide():
    rapport = toolkit.password_strength("")
    assert rapport.score == 0


def test_generation_mot_de_passe():
    pw = toolkit.generate_password(16)
    assert len(pw) == 16
    assert any(c.islower() for c in pw)
    assert any(c.isupper() for c in pw)
    assert any(c.isdigit() for c in pw)
    # Deux générations successives diffèrent (aléatoire).
    assert toolkit.generate_password(16) != toolkit.generate_password(16)


def test_hash_text_coherent():
    import hashlib

    h = toolkit.hash_text("bonjour")
    assert h["SHA-256"] == hashlib.sha256(b"bonjour").hexdigest()
    assert len(h["SHA-256"]) == 64
    assert len(h["SHA-1"]) == 40
    assert len(h["MD5"]) == 32


# --- Rapport HTML ----------------------------------------------------------

def test_html_contient_resume():
    findings = detectors.scan_line("password = abcd1234", 1, "f.txt")
    html = build_html(findings, "f.txt")
    assert "<html" in html
    assert "Rapport DataGuard" in html
    # Le secret en clair ne doit pas apparaître dans le HTML.
    assert "abcd1234" not in html


if __name__ == "__main__":
    import tempfile

    passed = 0
    failed = 0
    for name, fn in sorted(globals().items()):
        if not name.startswith("test_") or not callable(fn):
            continue
        try:
            if "tmp_path" in fn.__code__.co_varnames:
                with tempfile.TemporaryDirectory() as d:
                    fn(Path(d))
            else:
                fn()
            passed += 1
            print(f"✓ {name}")
        except AssertionError as e:
            failed += 1
            print(f"✗ {name} : {e}")

    print(f"\n{passed} réussi(s), {failed} échec(s)")
    raise SystemExit(1 if failed else 0)

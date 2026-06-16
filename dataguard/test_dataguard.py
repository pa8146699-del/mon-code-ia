#!/usr/bin/env python3
"""Tests pour DataGuard. Lancer avec : python -m pytest dataguard/

Fonctionne aussi sans pytest : python dataguard/test_dataguard.py
"""

from pathlib import Path

import dataguard


def test_detecte_mot_de_passe():
    findings = dataguard.scan_line("password = SuperSecret123", 1, "f")
    types = {f.type for f in findings}
    assert "Mot de passe en clair" in types


def test_detecte_cle_aws():
    findings = dataguard.scan_line("key=AKIA1234567890ABCDEF", 1, "f")
    assert any(f.type == "Clé API AWS" for f in findings)


def test_detecte_email():
    findings = dataguard.scan_line("contact: a@b.com", 1, "f")
    assert any(f.type == "Adresse e-mail" for f in findings)


def test_carte_valide_luhn():
    # 4539 1488 0343 6467 est un numéro valide au sens de Luhn.
    findings = dataguard.scan_line("carte 4539 1488 0343 6467", 1, "f")
    assert any(f.type == "Carte bancaire" for f in findings)


def test_carte_invalide_ignoree():
    # Numéro qui échoue à Luhn → ne doit pas être signalé comme carte.
    findings = dataguard.scan_line("ref 1234 5678 9012 3456", 1, "f")
    assert not any(f.type == "Carte bancaire" for f in findings)


def test_ligne_propre():
    findings = dataguard.scan_line("texte normal sans secret", 1, "f")
    assert findings == []


def test_redaction_masque_le_secret():
    masque = dataguard.redact("SuperSecret123")
    assert "SuperSecret123" not in masque
    assert "***" in masque


def test_scan_fichier(tmp_path: Path):
    f = tmp_path / "secrets.txt"
    f.write_text("password = abcd1234\n", encoding="utf-8")
    findings = dataguard.scan(f)
    assert len(findings) >= 1


if __name__ == "__main__":
    # Exécution manuelle sans pytest.
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

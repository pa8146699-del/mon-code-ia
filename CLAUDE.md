# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`mon-code-ia` is a personal Python toolkit with three components:

- `jarvis/` — a vocal/text assistant powered by the Claude API.
- `dataguard/` — a command-line data-leak / phishing security toolkit (no external dependencies).
- `mobile/` — a Kivy GUI wrapper around DataGuard, built into an Android APK by GitHub Actions.

`jarvis/` and `dataguard/` share no code. `mobile/` reuses `dataguard/detectors.py` and `dataguard/phishing.py` (copied in at build time, never committed under `mobile/`).

## Repository Layout

```
mon-code-ia/
├── .github/workflows/build-apk.yml   # CI: Android APK builder
├── .gitignore
├── CLAUDE.md
├── README.md
├── jarvis/
│   ├── jarvis.py                     # Single-file assistant (~100 lines)
│   └── requirements.txt
├── dataguard/
│   ├── dataguard.py                  # Argparse dispatcher (cmd_* functions)
│   ├── detectors.py                  # Secret-detection engine + Luhn + redact
│   ├── phishing.py                   # Heuristic phishing scorer
│   ├── report.py                     # HTML report generator
│   ├── test_dataguard.py             # Test suite (pytest + zero-dep runner)
│   └── README.md
└── mobile/
    ├── main.py                       # Kivy GUI (touch-friendly)
    ├── buildozer.spec                # Android build config
    └── README.md
```

Files git-ignored under `mobile/`: `detectors.py`, `phishing.py`, `bin/`, `.buildozer/`, `*.apk`.

## Setup

```bash
pip install -r jarvis/requirements.txt
export ANTHROPIC_API_KEY=your-key-here
```

## Running Jarvis

```bash
python jarvis/jarvis.py          # text mode (terminal only)
python jarvis/jarvis.py --voice  # voice mode (microphone + speech synthesis)
```

## Jarvis Architecture

`jarvis/jarvis.py` is a single-file application (~100 lines). Key design points:

- **Voice dependency loading** is conditional at module level (not lazy): if `--voice` is in `sys.argv`, `pyttsx3` and `speech_recognition` are imported immediately on startup. A missing voice dependency crashes at import time, not at first use.
- **Conversation state** (`_history: list[dict]`) is a module-level global. It accumulates the full turn-by-turn exchange and is passed to every Claude API call, giving multi-turn context. Lost when the process exits.
- **Model and limits**: hardcoded to `claude-sonnet-4-6` with `max_tokens=1024`.
- **Language**: the system prompt instructs Claude to reply in French by default, switching to the user's language if they write in another one.
- **Exit keywords**: `"quitter"`, `"stop"`, `"exit"`, `"quit"` (checked case-insensitively) terminate the loop.
- `ANTHROPIC_API_KEY` is read via `os.environ["ANTHROPIC_API_KEY"]` — raises `KeyError` if unset.

## DataGuard

`dataguard/` is a self-contained security toolkit (Python 3 standard library only) exposed through subcommands on `dataguard.py`:

```bash
python dataguard/dataguard.py                              # interactive menu (default with no args)
python dataguard/dataguard.py menu                         # same, explicit
python dataguard/dataguard.py scan <file-or-dir> [--json|--html FILE] [--strict]
python dataguard/dataguard.py phishing [--text STR | --file PATH] [--json] [--strict]
python dataguard/dataguard.py install-hook [--force]
python dataguard/dataguard.py scan-staged [--strict]       # used by the git hook
```

`phishing` also reads from stdin when neither `--text` nor `--file` is given:
```bash
cat mail.txt | python dataguard/dataguard.py phishing
```

Module layout (all flat, imported by simple name since `dataguard/` is on `sys.path[0]` when run directly):

- `dataguard.py` — argparse subcommand dispatch (`cmd_*` functions). Each subcommand sets `func` via `set_defaults`. Interactive menu is `cmd_menu` (options 1–4).
- `detectors.py` — the `DETECTORS` list and scanning logic (`scan`, `scan_file`, `scan_line`, `sort_findings`). Extend coverage by adding a `Detector(name, compiled_regex, severity)` entry. Credit-card hits are confirmed with the **Luhn checksum** (`luhn_valid`); all reported values are **redacted** (`redact`: first 4 chars + `***` + last 2 chars).
- `phishing.py` — heuristic phishing scorer. `analyze(text)` returns `(score 0-100, [PhishingSignal])`; lookalike-domain detection normalizes digit-for-letter swaps (`paypa1` → `paypal`) and skips legitimate `brand.tld` hosts.
- `report.py` — standalone HTML report (`build_html`); never embeds raw secrets.

### What `scan` detects

| Type | Severity |
|---|---|
| Private key (RSA, EC, OpenSSH…) | HIGH |
| AWS access key | HIGH |
| API keys: Anthropic, OpenAI, Google, Stripe, SendGrid | HIGH |
| GitHub token, Slack token, Google OAuth token | HIGH |
| Plaintext password | HIGH |
| IBAN | HIGH |
| Credit card number (Luhn-validated) | HIGH |
| JWT token, Slack webhook, generic secret/api_key/token | MEDIUM |
| Email address, FR phone number, IPv4 address | LOW |

Binary files (`.png`, `.jpg`, `.pdf`, `.pyc`, `.zip`, `.mp4`, `.ttf`, `.so`, etc.) and directories (`.git`, `__pycache__`, `node_modules`, `venv`, `.venv`, `.mypy_cache`) are skipped during directory scans.

### Phishing scoring signals

`analyze(text)` sums weighted signals (capped at 100):

| Signal | Weight |
|---|---|
| Urgency language ("urgent", "immédiatement", "expire", "suspendu"…) | 10 |
| Credentials demand ("password", "code pin", "numéro de carte"…) | 15 |
| Generic greeting ("cher client", "dear customer") | 5 |
| HTTP link (not HTTPS) | 8 |
| Punycode domain (xn--) | 20 |
| IP-based link | 20 |
| URL shortener (bit.ly, tinyurl…) | 12 |
| Suspicious TLD (.xyz, .top, .tk, .ml, .ga, .cf, .gq, .zip, .mov) | 12 |
| Excessive subdomains (4+ dots) | 8 |
| Lookalike domain (paypa1.com → paypal) | 25 |
| Dangerous attachment (.exe, .scr, .zip, .rar, .js, .vbs, .bat, .cmd, .iso, .docm, .xlsm) | 15 |

`risk_level(score)` → `"AUCUN"` (0) / `"FAIBLE"` (1–29) / `"MOYEN"` (30–59) / `"ÉLEVÉ"` (60+).

`--strict` exits with code 1 if score reaches MOYEN or higher.

### Git pre-commit hook

`scan-staged` + `install-hook` implement a pre-commit guard: the hook calls `scan-staged --strict` to block commits whose staged files contain secrets. The hook is written to `$(git rev-parse --git-dir)/hooks/pre-commit`. **Do not run `install-hook` from inside this repo's working tree** — it would install a pre-commit hook into `mon-code-ia/.git` and block your own commits; test it in a throwaway repo instead.

### Tests

```bash
python -m pytest dataguard/                      # if pytest is installed
cd dataguard && python test_dataguard.py         # zero-dependency fallback runner
```

`test_dataguard.py` includes 18 tests: detector coverage (password, AWS key, Stripe key, Google API key, IBAN, email, valid/invalid credit card, clean text), redaction correctness, file scan, phishing scenarios (clean text, urgency+credentials, lookalike domain, IP link, legitimate domain not flagged), and HTML report correctness. The fallback runner auto-discovers `test_*` functions and supports a `tmp_path` fixture via `tempfile.TemporaryDirectory`.

## Mobile App (`mobile/`)

`mobile/main.py` is a Kivy GUI exposing DataGuard's two text-based features (secret scan + phishing analysis) for touch use. It imports `detectors` and `phishing` by bare name; those files live in `dataguard/` and are **copied into `mobile/` at build time** by `.github/workflows/build-apk.yml` (they are git-ignored under `mobile/` to avoid drift — the single source of truth stays in `dataguard/`).

UI layout (`DataGuardLayout(BoxLayout)`):
1. Title label — "🛡️ DataGuard"
2. Instruction label
3. Multi-line `TextInput` (paste area, 40% screen height)
4. Two buttons side-by-side: "🔍 Scanner les secrets" (blue) and "🎣 Analyser phishing" (orange)
5. `ScrollView` + result `Label` (height binds to `texture_size[1]`, auto-expands; uses Kivy markup for colour coding)

`scan_text()` calls `detectors.scan_line()` per line and colour-codes results with Kivy markup (green = clean, red = HIGH, orange = MEDIUM, blue = LOW). `analyze_phishing()` calls `phishing.analyze()` and colour-codes by risk level.

Build:
- The `Build APK DataGuard` GitHub Actions workflow triggers on **manual `workflow_dispatch`** or **push to `main` touching `mobile/**` or the workflow file itself**.
- Runner: `ubuntu-latest` with `ghcr.io/kivy/buildozer:latest` container (includes Android SDK/NDK).
- Steps: checkout → git safe.directory → copy `detectors.py` + `phishing.py` into `mobile/` → `buildozer android debug` → upload `.apk` as `dataguard-apk` artifact.
- **APKs are built in CI, not locally** (Buildozer requires the Android SDK/NDK).
- Config lives in `mobile/buildozer.spec` (`requirements = python3,kivy`, targets API 34, minapi 24, both arm64-v8a and armeabi-v7a).
- Local UI test: `pip install kivy`, copy the two modules in, then `python mobile/main.py`.

## Dependencies

| Package | Required for |
|---|---|
| `anthropic>=0.40.0` | Claude API client — always required by jarvis/ |
| `SpeechRecognition>=3.10.0` | Microphone → text (`--voice` only) |
| `pyttsx3>=2.90` | Text → speech, offline (`--voice` only) |
| `PyAudio>=0.2.14` | Audio I/O backend for SpeechRecognition (`--voice` only) |

`dataguard/` has **zero external dependencies** (pure Python 3 stdlib: `re`, `pathlib`, `subprocess`, `argparse`, `json`, `dataclasses`, `html`, `datetime`, `stat`).

## Key Architectural Decisions

- **Modular separation**: the three components are independent; only `dataguard/` ↔ `mobile/` share code, via copy (not import), keeping `dataguard/` the single source of truth.
- **Conditional voice loading**: jarvis imports audio libs only when `--voice` is present, avoiding dependency failures for text-only mode.
- **Luhn validation**: credit card regex matches are verified by the Luhn checksum to suppress false positives.
- **Redaction-first**: secrets are masked (`a***34`) before any display or logging; raw values never appear in output.
- **CI-only APK builds**: Buildozer requires Android SDK/NDK; the GitHub Actions container provides both; local builds are not supported.
- **No persistent state in jarvis**: `_history` lives only in memory for the process lifetime; there is no database or file backing.

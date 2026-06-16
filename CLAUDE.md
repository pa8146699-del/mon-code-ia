# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`mon-code-ia` is a personal Python toolkit with three components:

- `jarvis/` — a vocal/text assistant powered by the Claude API.
- `dataguard/` — a command-line data-leak / phishing security toolkit (no external dependencies).
- `mobile/` — a Kivy GUI wrapper around DataGuard, built into an Android APK by GitHub Actions.

`jarvis/` and `dataguard/` share no code. `mobile/` reuses `dataguard/detectors.py` and `dataguard/phishing.py` (copied in at build time, never committed under `mobile/`).

## Setup

```bash
pip install -r jarvis/requirements.txt
export ANTHROPIC_API_KEY=your-key-here
```

## Running Jarvis

```bash
# Text mode (terminal only)
python jarvis/jarvis.py

# Voice mode (microphone input + speech synthesis)
python jarvis/jarvis.py --voice
```

## Architecture

`jarvis/jarvis.py` is a single-file application (~100 lines). Key design points:

- **Voice dependency loading** is conditional at module level (not lazy): if `--voice` is in `sys.argv`, `pyttsx3` and `speech_recognition` are imported immediately on startup. This means a missing voice dependency crashes at import time, not at first use.
- **Conversation state** (`_history: list[dict]`) is a module-level global. It accumulates the full turn-by-turn exchange and is passed to every Claude API call, giving multi-turn context. It is lost when the process exits.
- **Model and limits**: hardcoded to `claude-sonnet-4-6` with `max_tokens=1024`.
- **Language**: the system prompt instructs Claude to reply in French by default, switching to the user's language if they write in another one.
- **Exit keywords**: `"quitter"`, `"stop"`, `"exit"`, `"quit"` (checked case-insensitively) terminate the loop.
- `ANTHROPIC_API_KEY` is read directly from the environment via `os.environ["ANTHROPIC_API_KEY"]` — it will raise `KeyError` if unset.

## DataGuard

`dataguard/` is a self-contained security toolkit (Python 3 standard library only) exposed through subcommands on `dataguard.py`:

```bash
python dataguard/dataguard.py                          # interactive menu (default with no args)
python dataguard/dataguard.py scan <file-or-dir> [--json|--html FILE] [--strict]
python dataguard/dataguard.py phishing [--text STR | --file PATH] [--json] [--strict]
python dataguard/dataguard.py install-hook [--force]
python dataguard/dataguard.py scan-staged [--strict]   # used by the git hook
```

Module layout (all flat, imported by simple name since `dataguard/` is on `sys.path[0]` when run directly):

- `dataguard.py` — argparse subcommand dispatch (`cmd_*` functions). Each subcommand maps to `func` via `set_defaults`.
- `detectors.py` — the `DETECTORS` list and scanning logic (`scan`, `scan_file`, `scan_line`, `sort_findings`). Extend coverage by adding a `Detector(name, compiled_regex, severity)` entry. Credit-card hits are confirmed with the **Luhn checksum** (`luhn_valid`); all reported values are **redacted** (`redact`).
- `phishing.py` — heuristic phishing scorer. `analyze(text)` returns `(score 0-100, [PhishingSignal])`; lookalike-domain detection normalizes digit-for-letter swaps (`paypa1` → `paypal`) and skips legitimate `brand.tld` hosts.
- `report.py` — standalone HTML report (`build_html`); never embeds raw secrets.

`scan-staged` + `install-hook` implement a git `pre-commit` guard: the hook calls `scan-staged --strict` to block commits whose staged files contain secrets. The hook is written to `$(git rev-parse --git-dir)/hooks/pre-commit`. **Do not run `install-hook` from inside this repo's working tree** — it would install a pre-commit hook into `mon-code-ia/.git` and block your own commits; test it in a throwaway repo instead.

Tests live in `dataguard/test_dataguard.py` and import the modules by name, so run them from inside `dataguard/`:

```bash
python -m pytest dataguard/        # if pytest is installed
cd dataguard && python test_dataguard.py   # zero-dependency fallback runner
```

## Mobile app (`mobile/`)

`mobile/main.py` is a Kivy GUI exposing DataGuard's two text-based features (secret scan + phishing analysis) for touch use. It imports `detectors` and `phishing` by bare name; those files live in `dataguard/` and are **copied into `mobile/` at build time** by `.github/workflows/build-apk.yml` (they are git-ignored under `mobile/` to avoid drift — the single source of truth stays in `dataguard/`).

- Build: the `Build APK DataGuard` GitHub Actions workflow (manual `workflow_dispatch`, or on push touching `mobile/`) runs Buildozer via `ArtemSBulgakov/buildozer-action@v1` and uploads the `.apk` as the `dataguard-apk` artifact. **APKs are built in CI, not locally** (Buildozer can't run on a phone, and a local build needs the Android SDK/NDK).
- Config lives in `mobile/buildozer.spec` (`requirements = python3,kivy`).
- Local UI test: `pip install kivy`, copy the two modules in, then `python mobile/main.py`.

## Dependencies

| Package | Required for |
|---|---|
| `anthropic>=0.40.0` | Claude API client — always required |
| `SpeechRecognition>=3.10.0` | Microphone → text (`--voice` only) |
| `pyttsx3>=2.90` | Text → speech, offline (`--voice` only) |
| `PyAudio>=0.2.14` | Audio I/O backend for SpeechRecognition (`--voice` only) |

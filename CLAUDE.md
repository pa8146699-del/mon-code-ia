# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`mon-code-ia` is a personal Python toolkit with two independent components:

- `jarvis/` — a vocal/text assistant powered by the Claude API.
- `dataguard/` — a command-line data-leak scanner (no external dependencies).

The two components share no code and can be run separately.

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

`dataguard/dataguard.py` is a self-contained CLI that scans a file or directory for sensitive data (API keys, passwords, e-mails, credit card numbers, IPs…) to prevent leaks before sharing or committing.

```bash
python dataguard/dataguard.py <file-or-dir>          # human-readable report
python dataguard/dataguard.py <file-or-dir> --json   # machine-readable output
python dataguard/dataguard.py <file-or-dir> --strict # exit 1 on any finding (CI)
```

Design points:

- **No external dependencies** — Python 3 standard library only.
- Detection is **regex-driven** via the `DETECTORS` list; add a new `Detector(name, compiled_regex, severity)` entry to extend coverage.
- Credit-card matches are confirmed with the **Luhn checksum** (`luhn_valid`) to cut false positives.
- Reported values are **redacted** (`redact`) so secrets are never re-printed in full.
- `.git`, `node_modules`, `__pycache__`, `venv`/`.venv` and common binary extensions are skipped during directory scans.

Tests live in `dataguard/test_dataguard.py`:

```bash
python -m pytest dataguard/        # if pytest is installed
python dataguard/test_dataguard.py # zero-dependency fallback runner
```

## Dependencies

| Package | Required for |
|---|---|
| `anthropic>=0.40.0` | Claude API client — always required |
| `SpeechRecognition>=3.10.0` | Microphone → text (`--voice` only) |
| `pyttsx3>=2.90` | Text → speech, offline (`--voice` only) |
| `PyAudio>=0.2.14` | Audio I/O backend for SpeechRecognition (`--voice` only) |

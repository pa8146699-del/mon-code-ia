# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`mon-code-ia` is a personal AI assistant project. The main component is `jarvis/`, a Python-based vocal/text assistant powered by the Claude API. The assistant persona is "Jarvis" and defaults to French.

## Setup

```bash
pip install -r jarvis/requirements.txt
export ANTHROPIC_API_KEY=sk-...
```

`ANTHROPIC_API_KEY` is read at import time via `os.environ["ANTHROPIC_API_KEY"]` — the process crashes immediately with a `KeyError` if it is not set.

## Running Jarvis

```bash
# Mode texte (terminal)
python jarvis/jarvis.py

# Mode vocal (microphone + synthèse vocale)
python jarvis/jarvis.py --voice
```

Exit the assistant by typing (or saying) `quitter`, `stop`, `exit`, or `quit`.

## Architecture

### `jarvis/jarvis.py`

Single-file application. All global state lives at module level:

- `VOICE_MODE` — set once at import from `sys.argv`; voice dependencies (`pyttsx3`, `speech_recognition`) are imported **at module top-level** only when this is `True`, not lazily inside functions
- `_client` — `anthropic.Anthropic` instance, initialised at import
- `_history` — `list[dict]` of `{role, content}` pairs; grows unboundedly for the lifetime of the process and is sent in full to the API on every turn

Key functions:

| Function | Description |
|---|---|
| `read_input()` | Reads from stdin; returns `"quitter"` on EOF/Ctrl-C |
| `listen()` | Captures microphone audio, calls Google Speech Recognition (`fr-FR`); returns `""` on recognition failure |
| `respond(user_message)` | Appends to `_history`, calls `claude-sonnet-4-6` (max 1024 tokens), appends reply, returns text |
| `speak(text)` | pyttsx3 TTS, blocks until audio finishes |
| `main()` | Event loop; picks `listen` or `read_input` based on `VOICE_MODE` |

### Key design constraints

- **No token/history truncation** — `_history` is sent whole each turn. Long sessions will eventually exceed the model context window.
- **Google Speech Recognition requires internet** — `listen()` calls Google's cloud API. `pyttsx3` TTS is fully offline.
- **Blocking I/O throughout** — no async, no threading; `listen()` blocks until speech is detected, `speak()` blocks until audio finishes.
- **System prompt** — Jarvis is instructed to respond in French unless the user writes in another language.

### Dependencies

| Package | Purpose |
|---|---|
| `anthropic>=0.40.0` | Claude API client (always required) |
| `SpeechRecognition>=3.10.0` | Microphone → text (voice mode only) |
| `pyttsx3>=2.90` | Text → speech, offline (voice mode only) |
| `PyAudio>=0.2.14` | Audio I/O backend for SpeechRecognition (voice mode only) |

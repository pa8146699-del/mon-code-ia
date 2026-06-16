# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`mon-code-ia` is a personal AI assistant project. The main component is `jarvis/`, a Python-based vocal/text assistant powered by the Claude API.

## Setup

```bash
pip install -r jarvis/requirements.txt
export ANTHROPIC_API_KEY=sk-...
```

## Running Jarvis

```bash
# Mode texte (terminal)
python jarvis/jarvis.py

# Mode vocal (microphone + synthèse vocale)
python jarvis/jarvis.py --voice
```

## Architecture

### `jarvis/jarvis.py`

- `read_input()` — reads a command from stdin (text mode)
- `listen()` — captures audio from the microphone and converts to text via Google Speech Recognition (voice mode, `--voice` flag)
- `respond(user_message)` — sends the message to Claude (`claude-sonnet-4-6`) with full conversation history and returns the reply
- `speak(text)` — synthesizes text to speech via pyttsx3 (voice mode only)
- `main()` — event loop that selects input method based on `--voice` flag and exits on "quitter"/"stop"/"exit"/"quit"

Conversation history (`_history`) is kept in memory for the duration of the session, giving Claude multi-turn context.

### Dependencies

| Package | Purpose |
|---|---|
| `anthropic` | Claude API client (required) |
| `SpeechRecognition` | Microphone → text (voice mode) |
| `pyttsx3` | Text → speech, works offline (voice mode) |
| `PyAudio` | Audio I/O backend for SpeechRecognition (voice mode) |

Voice dependencies are only imported when `--voice` is passed, so the text-only mode has no extra requirements beyond `anthropic`.

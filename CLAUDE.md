# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`mon-code-ia` is a personal AI assistant project. The main component is `jarvis/`, a Python-based vocal/text assistant powered by **Ollama** (local AI, free, no API key required).

## Setup

```bash
# 1. Installer Ollama (https://ollama.com)
#    Linux :
curl -fsSL https://ollama.com/install.sh | sh
#    macOS/Windows : télécharger depuis https://ollama.com/download

# 2. Télécharger le modèle (une seule fois, ~2 Go)
ollama pull llama3.2

# 3. Installer les dépendances Python
pip install -r jarvis/requirements.txt
```

## Running Jarvis

```bash
# Mode texte (terminal)
python jarvis/jarvis.py

# Mode vocal (microphone + synthèse vocale)
python jarvis/jarvis.py --voice
```

Ollama doit tourner en arrière-plan (lancé automatiquement après installation, ou manuellement avec `ollama serve`).

## Changer de modèle

Modifier la constante `MODEL` dans `jarvis/jarvis.py` :

```python
MODEL = "llama3.2"      # par défaut (~2 Go)
# MODEL = "mistral"     # alternative (~4 Go)
# MODEL = "phi3"        # très léger (~2 Go)
```

Liste des modèles disponibles : `ollama list` / `ollama pull <nom>`.

## Architecture

### `jarvis/jarvis.py`

- `read_input()` — lit une commande depuis stdin (mode texte)
- `listen()` — capte le micro et transcrit via Google Speech Recognition (mode `--voice`)
- `respond(user_message)` — envoie le message à Ollama avec l'historique complet et retourne la réponse
- `speak(text)` — synthèse vocale via pyttsx3 (mode `--voice` uniquement)
- `main()` — boucle principale ; quitte sur "quitter"/"stop"/"exit"/"quit"

L'historique (`_history`) est conservé en mémoire le temps de la session.

### Dependencies

| Package | Purpose |
|---|---|
| `ollama` | Client Ollama — IA locale gratuite (obligatoire) |
| `SpeechRecognition` | Microphone → texte (mode vocal) |
| `pyttsx3` | Texte → parole, fonctionne hors ligne (mode vocal) |
| `PyAudio` | Backend audio pour SpeechRecognition (mode vocal) |

Les dépendances vocales ne sont importées que si `--voice` est passé.

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`mon-code-ia` is a personal AI assistant project. The main component is `jarvis/`, a Python-based assistant powered by **Ollama** (local AI, free, no API key required). It has two interfaces:

- `jarvis.py` — CLI terminal (text or voice via microphone)
- `app.py` — Web server with a mobile-friendly chat UI accessible from any browser/phone on the same Wi-Fi

## Setup

```bash
# 1. Installer Ollama — https://ollama.com
curl -fsSL https://ollama.com/install.sh | sh   # Linux
# macOS/Windows : télécharger depuis https://ollama.com/download

# 2. Télécharger le modèle (une seule fois, ~2 Go)
ollama pull llama3.2

# 3. Installer les dépendances Python
pip install -r jarvis/requirements.txt
```

## Running

```bash
# Interface web (téléphone / navigateur)
python jarvis/app.py
# → http://localhost:5000  ou  http://<IP-du-PC>:5000 depuis le téléphone

# CLI texte
python jarvis/jarvis.py

# CLI vocal (microphone + synthèse vocale)
python jarvis/jarvis.py --voice
```

Ollama doit tourner en arrière-plan (automatique après installation, ou `ollama serve`).

## Changer de modèle

Modifier la constante `MODEL` dans `app.py` ou `jarvis.py` :

```python
MODEL = "llama3.2"   # par défaut (~2 Go)
# MODEL = "mistral"  # ~4 Go
# MODEL = "phi3"     # très léger
```

`ollama list` liste les modèles installés ; `ollama pull <nom>` en télécharge un nouveau.

## Architecture

### `jarvis/app.py`
Serveur Flask exposé sur `0.0.0.0:5000`.
- `GET /` — sert `templates/index.html`
- `POST /chat` — reçoit `{message}`, appelle Ollama, retourne `{reply}`
- `POST /reset` — vide l'historique de conversation

L'historique (`_history`) est conservé en mémoire pour toute la session du serveur (global, mono-utilisateur).

### `jarvis/templates/index.html`
Interface chat sans dépendance externe (CSS/JS vanilla).
- Micro via **Web Speech API** du navigateur (Chrome/Edge/Safari)
- Synthèse vocale via **SpeechSynthesis** du navigateur
- Bulles de chat, indicateur de frappe animé, bouton "Nouvelle conv."

### `jarvis/jarvis.py`
CLI alternatif (même logique, sans Flask).
- Mode texte : `read_input()` + `respond()` en boucle
- Mode vocal (`--voice`) : `listen()` via SpeechRecognition + `speak()` via pyttsx3

### Dependencies

| Package | Usage |
|---|---|
| `ollama` | Client Ollama (IA locale gratuite) — obligatoire |
| `flask` | Serveur web pour `app.py` — obligatoire |
| `SpeechRecognition` | Micro → texte pour CLI vocal |
| `pyttsx3` | Texte → parole pour CLI vocal |
| `PyAudio` | Backend audio pour SpeechRecognition |

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`mon-code-ia` is a personal AI assistant project. The main component is `jarvis/`, a Python assistant powered by **Groq** (free cloud API, no credit card). It has two interfaces:

- `app.py` — Serveur web Flask avec interface chat mobile, accessible depuis le navigateur du téléphone
- `jarvis.py` — CLI texte (terminal)

## Setup

### 1. Clé API Groq (gratuite)
Créer un compte sur [console.groq.com](https://console.groq.com) → API Keys → Create.

### 2. Installation

**Termux (Android) :**
```bash
pkg update && pkg install python
pip install flask groq
export GROQ_API_KEY=gsk_...
```

**Alpine Linux :**
```bash
apk add python3 py3-pip
pip3 install flask groq
export GROQ_API_KEY=gsk_...
```

**Linux/macOS classique :**
```bash
pip install -r jarvis/requirements.txt
export GROQ_API_KEY=gsk_...
```

## Running

```bash
# Interface web (ouvrir http://localhost:5000 dans le navigateur)
python jarvis/app.py

# CLI texte
python jarvis/jarvis.py
```

## Changer de modèle

Modifier la constante `MODEL` dans `app.py` ou `jarvis.py` :

```python
MODEL = "llama-3.3-70b-versatile"   # qualité maximale (défaut)
# MODEL = "llama-3.1-8b-instant"    # plus rapide, plus léger
# MODEL = "mixtral-8x7b-32768"      # bon contexte long
```

Modèles disponibles : [console.groq.com/docs/models](https://console.groq.com/docs/models)

## Architecture

### `jarvis/app.py`
Serveur Flask sur `0.0.0.0:5000`.
- `GET /` — sert `templates/index.html`
- `POST /chat` — reçoit `{message}`, appelle Groq, retourne `{reply}`
- `POST /reset` — vide l'historique

Historique conservé en mémoire (global, mono-utilisateur, réinitialisé au redémarrage du serveur).

### `jarvis/templates/index.html`
Interface chat vanilla (pas de dépendance frontend).
- Micro et synthèse vocale via **Web Speech API** du navigateur (gratuit, intégré à Chrome/Safari)
- Bulles de chat, indicateur de frappe, bouton "Nouvelle conv."

### `jarvis/jarvis.py`
CLI texte uniquement (pas de voix — compatible Termux/Alpine sans dépendances système lourdes).

### Dependencies

| Package | Usage |
|---|---|
| `groq` | Client API Groq (IA cloud gratuite) |
| `flask` | Serveur web pour `app.py` |

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`mon-code-ia` is a personal AI assistant project. The main component is `jarvis/`, a Python assistant powered by **Ollama** (IA locale, gratuite, tourne sur le téléphone via Alpine proot). It has two interfaces:

- `app.py` — Serveur web Flask avec interface chat mobile, accessible depuis le navigateur du téléphone
- `jarvis.py` — CLI texte (terminal)

## Setup — Termux + Alpine proot (Android)

```bash
# ── 1. Dans Termux ──────────────────────────────────────────────
pkg update && pkg install proot-distro
proot-distro install alpine
proot-distro login alpine

# ── 2. Dans Alpine (proot) — installation en une commande ───────
apk add curl git
curl -fsSL https://raw.githubusercontent.com/pa8146699-del/mon-code-ia/main/install-proot-alpine.sh | sh
```

Le script installe Ollama, clone le projet, télécharge le modèle et configure l'**auto-démarrage** dans `~/.profile`. Après ça, chaque ouverture d'Alpine lance Jarvis automatiquement.

**Lancement manuel :**
```bash
sh ~/mon-code-ia/start.sh
```

Ouvrir `http://localhost:5000` dans Chrome → menu ⋮ → **"Ajouter à l'écran d'accueil"** → Jarvis s'installe comme une vraie app.

## Changer de modèle

## Installer comme application sur téléphone (PWA)

L'interface web est une Progressive Web App. Dans Chrome sur Android :
1. Ouvrir `http://localhost:5000` (ou l'IP du serveur)
2. Menu ⋮ → **"Ajouter à l'écran d'accueil"**
3. Jarvis s'ouvre désormais en plein écran comme une vraie app, sans barre de navigateur

## Changer de modèle

Modifier la constante `MODEL` dans `app.py` ou `jarvis.py` :

```python
MODEL = "tinyllama"    # ~600 Mo  — défaut, tourne sur tout téléphone
# MODEL = "phi3:mini"  # ~2.2 Go  — meilleure qualité, recommandé si ≥ 4 Go RAM
# MODEL = "llama3.2:1b" # ~1.3 Go  — bon équilibre
```

`ollama list` pour voir les modèles installés, `ollama pull <nom>` pour en ajouter.

## Architecture

### `jarvis/app.py`
Serveur Flask sur `0.0.0.0:5000`.
- `GET /` — sert `templates/index.html`
- `POST /chat` — reçoit `{message}`, appelle Groq, retourne `{reply}`
- `POST /reset` — vide l'historique

Historique conservé en mémoire (global, mono-utilisateur, réinitialisé au redémarrage du serveur).

### `jarvis/templates/index.html`
Interface chat vanilla (pas de dépendance frontend). PWA installable.
- Micro et synthèse vocale via **Web Speech API** du navigateur (gratuit, intégré à Chrome/Safari)
- Bulles de chat, indicateur de frappe, bouton "Nouvelle conv."
- `manifest.json` + service worker → installable sur écran d'accueil Android/iOS

### `jarvis/static/`
- `manifest.json` — déclaration PWA (icône, couleurs, mode standalone)
- `icon.svg` — icône de l'application
- `sw.js` — service worker minimal (rend l'app installable)

### `jarvis/jarvis.openrc`
Script OpenRC pour Alpine. Installé dans `/etc/init.d/jarvis` par `install-alpine.sh`.
Lit la clé API depuis `/etc/conf.d/jarvis`.

### `start.sh`
Lance Ollama (s'il n'est pas déjà actif) + télécharge le modèle si absent + démarre `app.py`. Point d'entrée unique pour tout démarrer.

### `install-proot-alpine.sh`
Installation clé-en-main dans Alpine proot : installe Ollama, clone le projet, tire le modèle, configure l'auto-démarrage dans `~/.profile`.

### `install-alpine.sh`
Script d'installation pour Alpine natif (VM/PC) avec service OpenRC.

### `jarvis/jarvis.py`
CLI texte uniquement (pas de voix — compatible Termux/Alpine sans dépendances système lourdes).

### Dependencies

| Package | Usage |
|---|---|
| `ollama` | Client Ollama — IA locale sur le téléphone |
| `flask` | Serveur web pour `app.py` |

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

**Termux + Alpine (proot-distro) — setup recommandé sur Android :**
```bash
# — Dans Termux —
pkg update && pkg install proot-distro git
proot-distro install alpine
proot-distro login alpine

# — Dans Alpine (proot) —
apk add python3 py3-pip git
git clone https://github.com/pa8146699-del/mon-code-ia
cd mon-code-ia
pip3 install flask groq
export GROQ_API_KEY=gsk_...
python3 jarvis/app.py
```
Puis ouvrir `http://localhost:5000` dans Chrome sur le téléphone.

> Note : OpenRC ne fonctionne pas dans proot. Pour relancer Jarvis automatiquement à l'ouverture de Termux, ajouter la ligne suivante dans `~/.bashrc` ou `~/.profile` de l'Alpine proot :
> ```bash
> python3 ~/mon-code-ia/jarvis/app.py &
> ```

**Alpine Linux natif (VM / PC) :**
```bash
sh install-alpine.sh   # installe, configure le service OpenRC, démarre
```
La clé API est stockée dans `/etc/conf.d/jarvis` (mode 600).

**Linux/macOS classique :**
```bash
pip install -r jarvis/requirements.txt
export GROQ_API_KEY=gsk_...
python jarvis/app.py
```

## Running

```bash
# Interface web (ouvrir http://localhost:5000 dans le navigateur)
python3 jarvis/app.py

# CLI texte
python3 jarvis/jarvis.py
```

## Installer comme application sur téléphone (PWA)

L'interface web est une Progressive Web App. Dans Chrome sur Android :
1. Ouvrir `http://localhost:5000` (ou l'IP du serveur)
2. Menu ⋮ → **"Ajouter à l'écran d'accueil"**
3. Jarvis s'ouvre désormais en plein écran comme une vraie app, sans barre de navigateur

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

### `install-alpine.sh`
Script d'installation clé-en-main pour Alpine : installe les dépendances, copie les fichiers dans `/opt/jarvis`, configure et démarre le service OpenRC.

### `jarvis/jarvis.py`
CLI texte uniquement (pas de voix — compatible Termux/Alpine sans dépendances système lourdes).

### Dependencies

| Package | Usage |
|---|---|
| `groq` | Client API Groq (IA cloud gratuite) |
| `flask` | Serveur web pour `app.py` |

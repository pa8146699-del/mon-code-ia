# HackNotes 🏴‍☠️

Carnet de notes de pirate pour Android — une appli **Kivy autonome** pour garder
tes notes de bug bounty / pentest organisées et toujours sur toi.

100% locale et hors-ligne : tes notes sont stockées dans une base **SQLite**
privée à l'application (aucune permission, aucun accès réseau, rien ne sort du
téléphone).

## Fonctionnalités

- **Ajouter / modifier / supprimer** des notes (titre + catégorie + contenu).
- **Catégories** colorées : `Lab`, `Cible`, `Technique`, `Recon`, `Faille`
  (ou n'importe quelle catégorie libre, affichée en gris).
- **Recherche** instantanée sur le titre, la catégorie et le contenu.
- **Tri** automatique par date de dernière modification (plus récent en haut).

## Architecture

Application **100% autonome** (stdlib `sqlite3` + Kivy), comme `netscan/` : elle
ne réutilise aucun autre module du dépôt, donc le workflow CI **ne copie rien**.

- `main.py` — UI Kivy à deux écrans via le `ScreenManager` intégré :
  - **ListScreen** : barre de recherche + liste défilante des notes + bouton
    « Nouvelle note ».
  - **EditorScreen** : titre, catégorie, contenu, et les actions Retour /
    Supprimer / Enregistrer.
- Base SQLite dans `App.user_data_dir/hacknotes.db` (écrivable sur Android).
  Table `notes(id, title, category, content, created, updated)`.
- `_esc()` échappe le markup Kivy avant tout affichage de texte dynamique
  (même convention que `monappli/` et `netscan/`).

## Build

- Le workflow **`Build APK HackNotes`** se déclenche sur `workflow_dispatch` ou
  sur un push vers `main` touchant `hacknotes/**` (ou son workflow).
- Runner : `ubuntu-latest` avec le conteneur `ghcr.io/kivy/buildozer:latest`.
- Étapes : checkout → git safe.directory → `buildozer android debug` → upload de
  l'`.apk` en artéfact `hacknotes-apk`.
- **Les APK sont construits en CI**, pas en local (Buildozer exige le SDK/NDK).
- Config dans `hacknotes/buildozer.spec` (`requirements = python3,kivy`, API 34,
  minapi 24, arm64-v8a + armeabi-v7a, aucune permission).

## Test local (UI)

```bash
pip install kivy
python hacknotes/main.py
```

La base SQLite est créée au premier lancement dans le dossier de données de
l'app.

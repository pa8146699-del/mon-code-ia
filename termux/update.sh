#!/data/data/com.termux/files/usr/bin/bash
# update.sh — Met à jour la boîte à outils sur Termux (git pull).
set -euo pipefail
REPO_DIR="$HOME/mon-code-ia"

if [ ! -d "$REPO_DIR/.git" ]; then
    printf '\033[1;33m!\033[0m Dépôt introuvable dans %s.\n' "$REPO_DIR"
    printf '  Lance d'\''abord termux/install.sh.\n'
    exit 1
fi

printf '\033[1;36m›\033[0m Mise à jour de la boîte à outils…\n'
git -C "$REPO_DIR" pull --ff-only
printf '\033[1;32m✓\033[0m À jour.\n'

#!/data/data/com.termux/files/usr/bin/bash
# ==========================================================================
#  install.sh — Installateur Termux pour la boîte à outils cybersécurité
#               DataGuard (du dépôt mon-code-ia).
#
#  Ce script :
#    1. met à jour les paquets Termux ;
#    2. installe python + git (seules dépendances : DataGuard est en
#       bibliothèque standard, zéro paquet pip) ;
#    3. clone (ou met à jour) le dépôt dans ~/mon-code-ia ;
#    4. installe un lanceur « dataguard » dans $PREFIX/bin pour pouvoir
#       taper simplement `dataguard` depuis n'importe où.
#
#  Usage (depuis Termux) :
#      pkg install -y git           # si git n'est pas encore là
#      git clone https://github.com/pa8146699-del/mon-code-ia
#      bash mon-code-ia/termux/install.sh
#
#  …ou en une ligne, sans rien cloner à la main :
#      curl -fsSL https://raw.githubusercontent.com/pa8146699-del/mon-code-ia/main/termux/install.sh | bash
# ==========================================================================
set -euo pipefail

REPO_URL="https://github.com/pa8146699-del/mon-code-ia"
REPO_DIR="$HOME/mon-code-ia"

say()  { printf '\033[1;36m›\033[0m %s\n' "$*"; }
ok()   { printf '\033[1;32m✓\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m!\033[0m %s\n' "$*"; }

# --- 0. Vérifie qu'on est bien sous Termux --------------------------------
if [ -z "${PREFIX:-}" ] || [ ! -d "${PREFIX:-/nonexistent}/bin" ]; then
    warn "La variable \$PREFIX de Termux est introuvable."
    warn "Ce script est prévu pour Termux. On continue quand même au mieux."
    PREFIX="${PREFIX:-$HOME/.local}"
    mkdir -p "$PREFIX/bin"
fi

# --- 1. Mise à jour + dépendances -----------------------------------------
say "Mise à jour des paquets Termux…"
pkg update -y && pkg upgrade -y

say "Installation de python et git…"
pkg install -y python git

# --- 2. Clone ou mise à jour du dépôt -------------------------------------
if [ -d "$REPO_DIR/.git" ]; then
    say "Dépôt déjà présent, mise à jour (git pull)…"
    git -C "$REPO_DIR" pull --ff-only || warn "git pull a échoué, on garde la version locale."
else
    say "Clonage du dépôt dans $REPO_DIR…"
    git clone "$REPO_URL" "$REPO_DIR"
fi
ok "Dépôt prêt : $REPO_DIR"

# --- 3. Installe le lanceur « dataguard » ---------------------------------
LAUNCHER="$PREFIX/bin/dataguard"
say "Installation du lanceur : $LAUNCHER"
cat > "$LAUNCHER" <<EOF
#!/data/data/com.termux/files/usr/bin/bash
# Lanceur DataGuard (généré par termux/install.sh).
exec python "$REPO_DIR/dataguard/dataguard.py" "\$@"
EOF
chmod +x "$LAUNCHER"
ok "Lanceur installé."

# --- 4. (Optionnel) accès au stockage du téléphone ------------------------
if command -v termux-setup-storage >/dev/null 2>&1; then
    say "Pour scanner tes fichiers (Téléchargements, etc.), autorise l'accès"
    say "au stockage avec :  termux-setup-storage"
fi

printf '\n'
ok "Installation terminée 🎉"
printf '\n'
say "Lance la boîte à outils avec :"
printf '    \033[1mdataguard\033[0m            (menu interactif)\n'
printf '    \033[1mdataguard scan ~/storage/downloads\033[0m\n'
printf '    \033[1mdataguard phishing --text "..."\033[0m\n'

#!/data/data/com.termux/files/usr/bin/bash
# ==========================================================================
#  setup-distro.sh — Installe un VRAI Linux complet (Debian) DANS Termux,
#                    via proot-distro, et y déploie la boîte à outils
#                    cybersécurité DataGuard.
#
#  Pourquoi ? La version Play Store de Termux est gelée et bridée. La vraie
#  version (F-Droid / GitHub) n'est pas restreinte, et proot-distro te donne
#  par-dessus un userland Linux complet où tu as le contrôle total : apt,
#  ton propre $HOME, n'importe quel paquet — sans root.
#
#  ⚠️  Prérequis : installe Termux depuis F-Droid ou GitHub, PAS le Play Store.
#        F-Droid  : https://f-droid.org/packages/com.termux/
#        GitHub   : https://github.com/termux/termux-app/releases
#
#  Usage (depuis Termux) :
#      pkg install -y git
#      git clone https://github.com/pa8146699-del/mon-code-ia
#      bash mon-code-ia/termux/setup-distro.sh
#
#  …ou en une ligne :
#      curl -fsSL https://raw.githubusercontent.com/pa8146699-del/mon-code-ia/main/termux/setup-distro.sh | bash
#
#  Après installation :
#      debian-cyber            → entre dans le Linux Debian
#      (dedans)  dataguard     → lance la boîte à outils
# ==========================================================================
set -euo pipefail

DISTRO="debian"
REPO_URL="https://github.com/pa8146699-del/mon-code-ia"
# Chemin du dépôt VU DE L'INTÉRIEUR de la distro (son propre $HOME = /root).
REPO_IN_DISTRO="/root/mon-code-ia"

say()  { printf '\033[1;36m›\033[0m %s\n' "$*"; }
ok()   { printf '\033[1;32m✓\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m!\033[0m %s\n' "$*"; }
die()  { printf '\033[1;31m✗\033[0m %s\n' "$*" >&2; exit 1; }

# --- 0. Vérifie qu'on est bien sous Termux (et pas Play Store gelé) --------
[ -n "${PREFIX:-}" ] && [ -d "$PREFIX/bin" ] || \
    die "À lancer depuis Termux (F-Droid/GitHub). \$PREFIX introuvable."

# --- 1. Met à jour Termux et installe proot-distro -------------------------
say "Mise à jour des paquets Termux…"
pkg update -y && pkg upgrade -y

say "Installation de proot-distro…"
pkg install -y proot-distro

# --- 2. Installe la distro Debian (si absente) ----------------------------
if proot-distro list --installed 2>/dev/null | grep -qw "$DISTRO"; then
    ok "Debian déjà installée."
else
    say "Installation de Debian (téléchargement du rootfs)…"
    proot-distro install "$DISTRO"
    ok "Debian installée."
fi

# --- 3. Provisionne l'intérieur de la distro ------------------------------
# Tout ce bloc s'exécute À L'INTÉRIEUR de Debian, en root, avec le contrôle
# complet. On met à jour apt, on installe python+git, on clone le dépôt et on
# pose un lanceur 'dataguard' dans /usr/local/bin.
say "Configuration de l'intérieur de Debian (apt, python, git, dépôt)…"
proot-distro login "$DISTRO" -- bash -lc "
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y python3 git ca-certificates
ln -sf \$(command -v python3) /usr/local/bin/python 2>/dev/null || true

if [ -d '$REPO_IN_DISTRO/.git' ]; then
    git -C '$REPO_IN_DISTRO' pull --ff-only || true
else
    git clone '$REPO_URL' '$REPO_IN_DISTRO'
fi

cat > /usr/local/bin/dataguard <<'LAUNCH'
#!/bin/bash
exec python3 $REPO_IN_DISTRO/dataguard/dataguard.py \"\$@\"
LAUNCH
chmod +x /usr/local/bin/dataguard
echo '✓ Boîte à outils déployée dans Debian.'
"

# --- 4. Crée le raccourci 'debian-cyber' côté Termux ----------------------
LOGIN="$PREFIX/bin/debian-cyber"
say "Création du raccourci d'entrée : $LOGIN"
cat > "$LOGIN" <<EOF
#!/data/data/com.termux/files/usr/bin/bash
# Entre dans le Linux Debian de mon-code-ia (contrôle complet).
exec proot-distro login $DISTRO "\$@"
EOF
chmod +x "$LOGIN"

printf '\n'
ok "Environnement prêt 🎉 — tu as un Debian complet, non bridé, sous la main."
printf '\n'
say "Entre dans ton Linux :"
printf '    \033[1mdebian-cyber\033[0m\n'
say "Puis, à l'intérieur :"
printf '    \033[1mdataguard\033[0m                 (menu interactif)\n'
printf '    \033[1mdataguard scan .\033[0m\n'
printf '    \033[1mapt install <ce-que-tu-veux>\033[0m   (contrôle total : apt complet)\n'

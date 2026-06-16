#!/bin/sh
# Installation de Jarvis sur Alpine Linux
set -e

INSTALL_DIR="/opt/jarvis"

echo "=== Installation de Jarvis ==="

# Dépendances système
apk add --no-cache python3 py3-pip

# Copier les fichiers
mkdir -p "$INSTALL_DIR/templates" "$INSTALL_DIR/static"
cp jarvis/app.py "$INSTALL_DIR/"
cp jarvis/jarvis.py "$INSTALL_DIR/"
cp jarvis/templates/index.html "$INSTALL_DIR/templates/"
cp jarvis/static/* "$INSTALL_DIR/static/"

# Dépendances Python
pip3 install --break-system-packages flask groq 2>/dev/null \
  || pip3 install flask groq

# Clé API Groq
if [ -z "$GROQ_API_KEY" ]; then
    printf "\nClé API Groq (depuis console.groq.com) : "
    read -r GROQ_API_KEY
fi

# Fichier de configuration lu par OpenRC
mkdir -p /etc/conf.d
cat > /etc/conf.d/jarvis << EOF
export GROQ_API_KEY="$GROQ_API_KEY"
EOF
chmod 600 /etc/conf.d/jarvis

# Service OpenRC
cp jarvis/jarvis.openrc /etc/init.d/jarvis
chmod +x /etc/init.d/jarvis
rc-update add jarvis default
rc-service jarvis start

echo ""
echo "Jarvis installé et démarré."
echo "Ouvrir dans le navigateur → http://localhost:5000"

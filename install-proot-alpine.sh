#!/bin/sh
# Installation complète de Jarvis dans Alpine proot (Termux)
# Exécuter depuis l'intérieur du proot Alpine
set -e

REPO_DIR="$HOME/mon-code-ia"
MODEL="${1:-phi3:mini}"   # passer un autre modèle en argument si besoin

echo "=== Installation de Jarvis + Ollama ==="

# Dépendances Alpine
apk add --no-cache python3 py3-pip git curl

# Ollama
if ! command -v ollama > /dev/null 2>&1; then
    echo "--- Installation d'Ollama..."
    curl -fsSL https://ollama.com/install.sh | sh
fi

# Cloner ou mettre à jour le projet
if [ -d "$REPO_DIR" ]; then
    echo "--- Mise à jour du projet..."
    git -C "$REPO_DIR" pull
else
    echo "--- Clonage du projet..."
    git clone https://github.com/pa8146699-del/mon-code-ia "$REPO_DIR"
fi

# Dépendances Python
pip3 install --break-system-packages flask ollama groq anthropic 2>/dev/null \
    || pip3 install flask ollama groq anthropic

# Télécharger le modèle IA
echo "--- Démarrage d'Ollama pour télécharger le modèle $MODEL..."
ollama serve > /tmp/ollama.log 2>&1 &
sleep 3
ollama pull "$MODEL"
pkill ollama 2>/dev/null || true

# Auto-démarrage à chaque ouverture d'Alpine
AUTOSTART="ollama serve > /dev/null 2>&1 & sleep 2 && python3 $REPO_DIR/start.sh"
PROFILE="$HOME/.profile"

if ! grep -q "mon-code-ia" "$PROFILE" 2>/dev/null; then
    echo "" >> "$PROFILE"
    echo "# Jarvis — démarrage automatique" >> "$PROFILE"
    echo "$AUTOSTART" >> "$PROFILE"
    echo "--- Auto-démarrage configuré dans $PROFILE"
fi

echo ""
echo "Installation terminée !"
echo "Lancer maintenant : sh $REPO_DIR/start.sh"
echo "Ou fermer/rouvrir Alpine → Jarvis démarrera automatiquement."
echo "Puis ouvrir Chrome → http://localhost:5000"

#!/bin/sh
# Lance Ollama (IA locale) + Jarvis en une commande

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MODEL="${JARVIS_MODEL:-tinyllama}"

# Démarrer Ollama s'il n'est pas déjà lancé
if ! pgrep -x ollama > /dev/null 2>&1; then
    echo "[Jarvis] Démarrage d'Ollama..."
    ollama serve > /tmp/ollama.log 2>&1 &
    # Attendre qu'Ollama soit prêt
    i=0
    while ! ollama list > /dev/null 2>&1; do
        sleep 1
        i=$((i + 1))
        [ $i -ge 15 ] && echo "[Jarvis] Erreur : Ollama ne répond pas." && exit 1
    done
fi

# Vérifier que le modèle est disponible, le télécharger si besoin
if ! ollama list | grep -q "^$MODEL"; then
    echo "[Jarvis] Téléchargement du modèle $MODEL (première fois)..."
    ollama pull "$MODEL"
fi

echo "[Jarvis] Prêt → http://localhost:5000"
exec python3 "$SCRIPT_DIR/jarvis/app.py"

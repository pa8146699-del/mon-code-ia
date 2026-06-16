#!/bin/sh
# Lance Ollama (IA locale) + Jarvis en une commande

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MODEL="${JARVIS_MODEL:-phi3:mini}"
VISION_MODEL="${JARVIS_VISION_MODEL:-moondream}"   # vision locale hors-ligne

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

# Vérifier que le modèle texte est disponible, le télécharger si besoin
if ! ollama list | grep -q "^$MODEL"; then
    echo "[Jarvis] Téléchargement du modèle $MODEL (première fois)..."
    ollama pull "$MODEL"
fi

# Modèle vision local (analyse d'images hors-ligne) — JARVIS_VISION_MODEL=skip pour ignorer
if [ "$VISION_MODEL" != "skip" ] && ! ollama list | grep -q "^$VISION_MODEL"; then
    echo "[Jarvis] Téléchargement du modèle vision $VISION_MODEL (analyse d'images hors-ligne)..."
    ollama pull "$VISION_MODEL" || echo "[Jarvis] Vision locale ignorée (téléchargement impossible)."
fi

echo "[Jarvis] Prêt → http://localhost:5000"
exec python3 "$SCRIPT_DIR/jarvis/app.py"

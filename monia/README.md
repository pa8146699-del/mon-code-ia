# monia/ — Ton propre modèle d'IA, écrit de zéro

`monia/` est **ta** intelligence artificielle. Pas une API branchée sur le
modèle de quelqu'un d'autre : un vrai **mini-GPT** (la même architecture
Transformer que ChatGPT, en beaucoup plus petit) que tu écris, entraînes et
fais tourner toi-même, sur ton PC Debian (CPU, carte Intel — pas besoin de GPU).

## Ce que c'est (et ce que ce n'est pas)

- ✅ Une vraie architecture GPT de zéro : attention, couches Transformer,
  entraînement, génération de texte. **Tout le code t'appartient.**
- ✅ Ça s'entraîne sur **ton** texte et apprend à écrire dans ce style.
- ✅ Zéro service extérieur, zéro clé d'API, zéro abonnement.
- ❌ Ce n'est pas un ChatGPT : un seul PC ne peut pas entraîner un modèle géant.
  Tu obtiens un **petit** modèle qui génère du texte — mais qui est 100 % le tien.

## Fichiers

| Fichier | Rôle |
|---|---|
| `model.py` | Le mini-GPT de zéro (attention + blocs Transformer). Le coeur. |
| `train.py` | Entraîne le modèle sur `data.txt`, sauvegarde dans `monia.pt`. |
| `generate.py` | Charge `monia.pt` et génère du texte. |
| `data.txt` | Le texte d'entraînement (à remplacer par un gros texte à toi). |
| `requirements.txt` | `torch` (version CPU) + `numpy`. |

## Installation (Debian, CPU)

```bash
cd ~/mon-code-ia              # ou là où tu as cloné le dépôt
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip

# PyTorch version CPU (pas de GPU NVIDIA = on prend la version CPU, plus légère)
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install numpy
```

Vérifier que tout est là :

```bash
python -c "import torch; print('PyTorch', torch.__version__, '| CPU OK')"
```

## Entraîner ton IA

```bash
python monia/train.py
```

Tu verras la **perte (loss) baisser** à chaque palier : c'est ton modèle qui
apprend. À la fin, il est sauvegardé dans `monia/monia.pt`.

> Sur CPU, l'entraînement par défaut prend quelques minutes à quelques dizaines
> de minutes selon ton PC. C'est normal que ce soit lent : entraîner une IA
> demande du calcul.

## Faire parler ton IA

```bash
python monia/generate.py                       # texte libre
python monia/generate.py "Le matin, le soleil" # commence par cette phrase
python monia/generate.py "Bonjour" 800         # 800 caractères
```

## Pour de meilleurs résultats

1. **Mets un GROS texte dans `data.txt`.** C'est le facteur n°1. Le texte de
   départ est minuscule (juste pour tester). Remplace-le par un vrai gros
   corpus : un livre du domaine public (cherche « Project Gutenberg français »),
   tes notes, des paroles, des articles… Vise **au moins 1 million de
   caractères**.
2. **Agrandis le modèle** (dans `train.py`) si ton PC tient le coup :
   augmente `n_embd` (ex. 256), `n_layer` (ex. 6), `n_head` (ex. 6) et
   `max_iters` (ex. 5000). Plus grand = plus malin, mais plus lent.
3. **Sois patient.** Une perte qui descend = ça marche. Si elle stagne très
   haut, c'est souvent que `data.txt` est trop petit.

## La suite, quand tu seras à l'aise

- Passer d'un modèle **caractère par caractère** à un modèle **par mots/tokens**
  (tokenizer BPE) — c'est ce que font les vrais LLM.
- Sauvegarder/reprendre l'entraînement, suivre les courbes de perte.
- Si un jour tu as accès à un GPU (NVIDIA), le même code tournera 10 à 100×
  plus vite et tu pourras viser bien plus gros.

Bienvenue dans la création d'IA, pour de vrai. 🧠

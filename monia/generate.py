#!/usr/bin/env python3
"""
monia/generate.py — Fais parler TON IA entraînée.

Lance :
    python monia/generate.py                       # génère 500 caractères
    python monia/generate.py "Il était une fois"   # commence par ce texte
    python monia/generate.py "Bonjour" 800          # 800 caractères

Il faut avoir entraîné le modèle avant (python monia/train.py), ce qui crée
le fichier monia/monia.pt.
"""

import os
import sys
import torch

from model import GPT

HERE = os.path.dirname(os.path.abspath(__file__))
CKPT = os.path.join(HERE, "monia.pt")

device = "cuda" if torch.cuda.is_available() else "cpu"

if not os.path.exists(CKPT):
    raise SystemExit("❌ Modèle introuvable. Entraîne-le d'abord :  python monia/train.py")

ckpt = torch.load(CKPT, map_location=device)
cfg, stoi, itos = ckpt["config"], ckpt["stoi"], ckpt["itos"]
encode = lambda s: [stoi[c] for c in s if c in stoi]
decode = lambda l: "".join(itos[i] for i in l)

model = GPT(**cfg).to(device)
model.load_state_dict(ckpt["model"])
model.eval()

prompt = sys.argv[1] if len(sys.argv) > 1 else "\n"
n_tokens = int(sys.argv[2]) if len(sys.argv) > 2 else 500

start = encode(prompt) or [0]
idx = torch.tensor([start], dtype=torch.long, device=device)
out = model.generate(idx, max_new_tokens=n_tokens)
print(decode(out[0].tolist()))

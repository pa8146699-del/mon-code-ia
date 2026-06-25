#!/usr/bin/env python3
"""
monia/train.py — Entraîne TON mini-GPT sur le texte de monia/data.txt.

Lance simplement :  python monia/train.py

Tu verras la "perte" (loss) baisser au fil des itérations : c'est ton IA
qui apprend, sous tes yeux. À la fin, le modèle est sauvegardé dans
monia/monia.pt, prêt à générer du texte (voir generate.py).

⚙️  Réglages : tout est en haut. Sur un CPU, garde les valeurs petites.
   Si ton PC est rapide, augmente n_embd / n_layer / max_iters.
"""

import os
import torch

from model import GPT

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data.txt")
CKPT = os.path.join(HERE, "monia.pt")

# ── Hyperparamètres (petits = OK sur CPU Intel) ─────────────────────────────
block_size    = 128     # caractères de contexte
batch_size    = 32      # exemples traités en parallèle
max_iters     = 3000    # nombre d'étapes d'entraînement
eval_interval = 200     # à quelle fréquence afficher la perte
learning_rate = 3e-4
n_embd        = 128
n_head        = 4
n_layer       = 4
dropout       = 0.1
# ────────────────────────────────────────────────────────────────────────────

device = "cuda" if torch.cuda.is_available() else "cpu"
torch.manual_seed(1337)

if not os.path.exists(DATA):
    raise SystemExit(f"❌ Fichier introuvable : {DATA}\n"
                     "   Mets ton texte d'entraînement dans monia/data.txt")

text = open(DATA, encoding="utf-8").read()
if len(text) < 1000:
    print("⚠️  data.txt est très court — l'IA n'aura pas grand-chose à apprendre.")
    print("    Conseil : mets un gros texte (un livre du domaine public, tes notes…).")

# Vocabulaire = l'ensemble des caractères distincts du texte
chars = sorted(set(text))
vocab_size = len(chars)
stoi = {c: i for i, c in enumerate(chars)}   # caractère -> numéro
itos = {i: c for i, c in enumerate(chars)}   # numéro -> caractère
encode = lambda s: [stoi[c] for c in s]
decode = lambda l: "".join(itos[i] for i in l)

data = torch.tensor(encode(text), dtype=torch.long)
n = int(0.9 * len(data))
train_data, val_data = data[:n], data[n:]


def get_batch(split):
    """Tire un petit paquet d'exemples (entrée x, cible y = x décalé d'un cran)."""
    d = train_data if split == "train" else val_data
    ix = torch.randint(len(d) - block_size, (batch_size,))
    x = torch.stack([d[i:i + block_size] for i in ix])
    y = torch.stack([d[i + 1:i + block_size + 1] for i in ix])
    return x.to(device), y.to(device)


@torch.no_grad()
def estimate_loss(model):
    out = {}
    model.eval()
    for split in ("train", "val"):
        losses = torch.zeros(50)
        for k in range(50):
            x, y = get_batch(split)
            _, loss = model(x, y)
            losses[k] = loss.item()
        out[split] = losses.mean().item()
    model.train()
    return out


def main():
    model = GPT(vocab_size, n_embd, n_head, n_layer, block_size, dropout).to(device)
    n_params = sum(p.numel() for p in model.parameters())
    print(f"Appareil : {device}")
    print(f"Vocabulaire : {vocab_size} caractères | Texte : {len(text):,} caractères")
    print(f"Modèle : {n_params / 1e6:.2f}M paramètres\n")

    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate)

    for it in range(max_iters + 1):
        if it % eval_interval == 0:
            losses = estimate_loss(model)
            print(f"itér {it:5d} | perte entraînement {losses['train']:.3f} "
                  f"| perte validation {losses['val']:.3f}")
        x, y = get_batch("train")
        _, loss = model(x, y)
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        optimizer.step()

    torch.save(
        {
            "model": model.state_dict(),
            "config": dict(vocab_size=vocab_size, n_embd=n_embd, n_head=n_head,
                           n_layer=n_layer, block_size=block_size, dropout=dropout),
            "stoi": stoi,
            "itos": itos,
        },
        CKPT,
    )
    print(f"\n✅ Ton IA est sauvegardée dans {CKPT}")
    print("   Génère du texte avec :  python monia/generate.py")


if __name__ == "__main__":
    main()

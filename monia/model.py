#!/usr/bin/env python3
"""
monia/model.py — Un mini-GPT écrit de zéro (architecture style nanoGPT).

C'est le COEUR de ton IA. Rien n'est emprunté à OpenAI, Google ou Anthropic :
chaque couche est écrite ici, à la main. C'est exactement l'architecture
Transformer qui fait tourner ChatGPT — juste beaucoup plus petite, pour
qu'elle s'entraîne sur ton PC (CPU).

Idée générale :
  1. Chaque caractère devient un vecteur de nombres (embedding).
  2. Le mécanisme d'ATTENTION laisse chaque caractère "regarder" les
     caractères précédents pour décider quoi prédire ensuite.
  3. On empile plusieurs blocs (attention + petit réseau) pour aller plus loin.
  4. À la fin, le modèle prédit le PROCHAIN caractère le plus probable.

Entraîner = ajuster tous ces nombres pour que les prédictions soient bonnes.
"""

import torch
import torch.nn as nn
from torch.nn import functional as F


class Head(nn.Module):
    """Une seule tête d'auto-attention.

    Chaque caractère produit une "question" (query), une "clé" (key) et une
    "valeur" (value). On compare les questions aux clés pour savoir à quels
    caractères passés prêter attention, puis on mélange les valeurs en
    conséquence. Le masque triangulaire (tril) empêche de tricher en
    regardant le futur — on ne voit que le passé.
    """

    def __init__(self, n_embd, head_size, block_size, dropout):
        super().__init__()
        self.key = nn.Linear(n_embd, head_size, bias=False)
        self.query = nn.Linear(n_embd, head_size, bias=False)
        self.value = nn.Linear(n_embd, head_size, bias=False)
        self.register_buffer("tril", torch.tril(torch.ones(block_size, block_size)))
        self.dropout = nn.Dropout(dropout)

    def forward(self, x):
        B, T, C = x.shape
        k = self.key(x)      # (B, T, head_size)
        q = self.query(x)    # (B, T, head_size)
        # Score d'attention : à quel point chaque caractère s'intéresse aux autres
        wei = q @ k.transpose(-2, -1) * k.shape[-1] ** -0.5   # (B, T, T)
        wei = wei.masked_fill(self.tril[:T, :T] == 0, float("-inf"))  # masque le futur
        wei = F.softmax(wei, dim=-1)
        wei = self.dropout(wei)
        v = self.value(x)
        return wei @ v       # (B, T, head_size)


class MultiHead(nn.Module):
    """Plusieurs têtes d'attention en parallèle, puis on recombine.

    Plusieurs têtes = le modèle peut prêter attention à plusieurs choses à la
    fois (la grammaire, le sujet, la ponctuation…).
    """

    def __init__(self, n_head, n_embd, block_size, dropout):
        super().__init__()
        head_size = n_embd // n_head
        self.heads = nn.ModuleList(
            [Head(n_embd, head_size, block_size, dropout) for _ in range(n_head)]
        )
        self.proj = nn.Linear(n_embd, n_embd)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x):
        out = torch.cat([h(x) for h in self.heads], dim=-1)
        return self.dropout(self.proj(out))


class FeedForward(nn.Module):
    """Un petit réseau de neurones appliqué à chaque position.

    Après l'attention (où les caractères communiquent), chaque caractère
    "réfléchit" un peu de son côté.
    """

    def __init__(self, n_embd, dropout):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(n_embd, 4 * n_embd),
            nn.ReLU(),
            nn.Linear(4 * n_embd, n_embd),
            nn.Dropout(dropout),
        )

    def forward(self, x):
        return self.net(x)


class Block(nn.Module):
    """Un bloc Transformer = attention + réflexion, avec connexions résiduelles.

    Les `x = x + ...` (connexions résiduelles) et les LayerNorm sont ce qui
    permet d'empiler plein de blocs sans que l'entraînement ne s'effondre.
    """

    def __init__(self, n_embd, n_head, block_size, dropout):
        super().__init__()
        self.sa = MultiHead(n_head, n_embd, block_size, dropout)
        self.ff = FeedForward(n_embd, dropout)
        self.ln1 = nn.LayerNorm(n_embd)
        self.ln2 = nn.LayerNorm(n_embd)

    def forward(self, x):
        x = x + self.sa(self.ln1(x))
        x = x + self.ff(self.ln2(x))
        return x


class GPT(nn.Module):
    """Le modèle complet : ton IA.

    vocab_size : nombre de caractères différents dans ton texte.
    n_embd     : taille des vecteurs (plus grand = plus "intelligent" mais plus lent).
    n_head     : nombre de têtes d'attention.
    n_layer    : nombre de blocs empilés (la "profondeur").
    block_size : combien de caractères de contexte le modèle voit d'un coup.
    """

    def __init__(self, vocab_size, n_embd=128, n_head=4, n_layer=4,
                 block_size=128, dropout=0.1):
        super().__init__()
        self.block_size = block_size
        self.token_emb = nn.Embedding(vocab_size, n_embd)   # chaque caractère -> vecteur
        self.pos_emb = nn.Embedding(block_size, n_embd)     # position dans la phrase -> vecteur
        self.blocks = nn.Sequential(
            *[Block(n_embd, n_head, block_size, dropout) for _ in range(n_layer)]
        )
        self.ln_f = nn.LayerNorm(n_embd)
        self.head = nn.Linear(n_embd, vocab_size)           # -> score par caractère possible

    def forward(self, idx, targets=None):
        B, T = idx.shape
        tok = self.token_emb(idx)                                   # (B, T, n_embd)
        pos = self.pos_emb(torch.arange(T, device=idx.device))      # (T, n_embd)
        x = tok + pos
        x = self.blocks(x)
        x = self.ln_f(x)
        logits = self.head(x)                                       # (B, T, vocab_size)

        loss = None
        if targets is not None:
            B, T, C = logits.shape
            # On compare les prédictions au vrai caractère suivant
            loss = F.cross_entropy(logits.view(B * T, C), targets.view(B * T))
        return logits, loss

    @torch.no_grad()
    def generate(self, idx, max_new_tokens, temperature=1.0):
        """Génère du texte caractère par caractère.

        temperature : <1 = plus prudent/répétitif, >1 = plus créatif/fou.
        """
        for _ in range(max_new_tokens):
            idx_cond = idx[:, -self.block_size:]        # on garde le contexte récent
            logits, _ = self(idx_cond)
            logits = logits[:, -1, :] / temperature      # dernier caractère prédit
            probs = F.softmax(logits, dim=-1)
            next_id = torch.multinomial(probs, num_samples=1)
            idx = torch.cat([idx, next_id], dim=1)
        return idx

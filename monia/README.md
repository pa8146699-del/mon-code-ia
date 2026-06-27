# MonIA — ton réseau de neurones 100 % maison

Une petite IA écrite **entièrement à la main**, sans numpy, sans torch, sans
aucune dépendance : juste la bibliothèque standard de Python. Tu peux lire tout
le code et comprendre chaque ligne. C'est la suite logique de tes premiers
essais dans `~/MonIA` (un neurone unique qui apprend `y = 2x`), mais en mieux :
un **vrai réseau multicouche** entraîné par rétropropagation, capable
d'apprendre des fonctions non-linéaires (comme le XOR).

Tout tourne partout, y compris dans **Termux sur ton téléphone** — aucun
`pip install`.

## Le cœur : `reseau.py`

La classe `Reseau` est un perceptron multicouche (MLP) en Python pur :

```python
from reseau import Reseau

# 2 entrées -> 1 couche cachée de 4 neurones -> 1 sortie
ia = Reseau([2, 4, 1], activation="tanh", sortie="sigmoide", seed=1)

donnees = [([0, 0], [0]), ([0, 1], [1]), ([1, 0], [1]), ([1, 1], [0])]  # XOR
ia.entrainer(donnees, epochs=3000, taux=0.5)

print(ia.predire([1, 0]))   # ~ [0.98]
```

- **Activations** disponibles : `identite` (régression), `sigmoide` (proba 0–1),
  `tanh`, `relu`.
- **`entrainer(donnees, epochs, taux, rappel)`** : descente de gradient par
  rétropropagation ; `rappel(epoch, erreur)` suit la progression.
- **`predire(x)`** : la sortie du réseau pour une entrée.
- **`sauvegarder(chemin)` / `Reseau.charger(chemin)`** : la mémoire de l'IA
  (ses poids) dans un fichier JSON — elle garde son savoir après extinction.

Lancer la démo XOR :

```bash
cd monia && python3 reseau.py
```

## Les leçons (à lire/lancer dans l'ordre)

| Fichier | Leçon |
|---|---|
| `cerveau.py` | **1. Le neurone** : `réponse = entrée × poids + biais`, poids au hasard. |
| `apprentissage.py` | **2. Apprendre** `y = 2x` tout seul (poids → 2, biais → 0). |
| `entrainement.py` | **3. L'entraînement** : voir l'erreur baisser, tester `x=10 → 20`. |
| `memoire.py` | **4. La mémoire** : sauvegarder/recharger les poids en JSON. |

```bash
cd monia
python3 cerveau.py
python3 apprentissage.py
python3 entrainement.py
python3 memoire.py
```

## Tests

```bash
python -m pytest monia/            # si pytest est installé
cd monia && python3 test_monia.py  # runner zéro-dépendance
```

9 tests : formes des poids, reproductibilité de la graine, dérivées des
activations, apprentissage de `y = 2x`, décroissance de l'erreur, apprentissage
du XOR non-linéaire, sauvegarde/rechargement de la mémoire.

## Pourquoi « from scratch » ?

Pour **apprendre comment une IA fonctionne vraiment**, pas juste l'utiliser.
Ici il n'y a pas de boîte noire : un neurone est une multiplication plus une
addition, l'apprentissage est une descente de gradient, et la mémoire est un
fichier de nombres. Tout est à toi, à 100 %.

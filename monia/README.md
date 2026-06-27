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
| `discussion.py` | **5. Discuter** : un chatbot qui apprend des mots pour répondre. |
| `ecrivain.py` | **6. Lire un livre** : apprend tout le vocabulaire d'un texte et écrit. |
| `codeur.py` | **7. Apprendre à coder** : répond à tes questions avec du code Python. |
| `commandes.py` | **8. Le dépanneur** : les bonnes commandes du terminal quand tu bloques. |
| `github.py` | **9. Connaître GitHub** : cloner, envoyer, branches, tokens, pull requests. |

```bash
cd monia
python3 cerveau.py
python3 apprentissage.py
python3 entrainement.py
python3 memoire.py
python3 discussion.py     # discute avec ton IA (tape 'quitter' pour sortir)
python3 ecrivain.py       # lit un texte d'exemple et écrit dans son style
python3 codeur.py         # pose une question, il répond en Python
python3 commandes.py      # bloqué dans le terminal ? il te donne la commande
python3 github.py         # tout ce qu'il faut savoir sur GitHub
```

### Le chatbot — `discussion.py`

⚠️ **Honnêteté d'abord** : une IA 100 % maison en Python pur ne peut pas
« connaître tous les mots » comme ChatGPT (ça demande des milliards de
paramètres et d'énormes données). **Mais** elle apprend très bien à répondre
aux questions que **tu lui enseignes**, même reformulées.

Comment ça marche : chaque phrase est découpée en mots (le vocabulaire), puis
transformée en un vecteur « sac de mots » (1 = mot présent, 0 = absent). Le
réseau de `reseau.py` apprend à associer ce vecteur à la bonne réponse.

**Lui apprendre en parlant (le plus simple, sans toucher au code)** : pendant la
discussion, écris simplement

```
apprends: ta question = ta réponse
```

par exemple `apprends: quelle est la capitale de la France = Paris`. Elle
l'apprend tout de suite **et le retient** : tout est sauvegardé dans `chat.json`
et rechargé automatiquement au prochain lancement. Tape `aide` pour revoir les
commandes.

Lui apprendre dans le code : tu peux aussi ajouter des couples
`("question", "réponse")` dans la liste `CONNAISSANCES` de `discussion.py`, ou
passer ta propre liste (donne plusieurs formulations d'une même question pour
qu'elle généralise mieux) :

```python
from discussion import Discussion

chat = Discussion([
    ("bonjour", "Salut !"),
    ("quelle est la capitale de la France", "Paris."),
    ("c'est quoi la capitale française", "Paris."),
])
chat.entrainer(epochs=3000, taux=0.3)
print(chat.repondre("la capitale de la france ?"))   # -> Paris.
chat.sauvegarder("chat.json")                          # garde ce qu'elle a appris
```

Si aucun mot de ta question n'est connu, elle répond honnêtement
« Je ne sais pas encore répondre à ça. Apprends-le moi ! ».

### Apprendre un livre — `ecrivain.py`

Le chatbot apprend des paires question/réponse ; **un livre n'en contient pas**.
Pour « avaler » un livre entier et en connaître tout le vocabulaire, c'est une
autre technique : un **générateur de texte** (modèle de Markov). Il lit le texte,
retient quels mots suivent quels autres, puis écrit dans le même style.

```bash
python3 ecrivain.py mon_livre.txt   # apprend ton livre
python3 ecrivain.py                 # apprend un texte d'exemple (La Fontaine)
```

Puis donne-lui un ou deux mots de départ et il continue tout seul.

**Où trouver des livres gratuits (.txt)** — le [Projet Gutenberg](https://www.gutenberg.org)
(livres libres de droits). Sur la fiche d'un livre, choisis le format
**« Plain Text UTF-8 »** et enregistre-le en `.txt`. Quelques idées en français :
Jules Verne, Victor Hugo, Alexandre Dumas, les fables de La Fontaine, les contes
de Perrault. Conseil : **commence par un texte court** (un conte, des fables) — il
apprend plus vite et écrit plus joliment qu'avec un énorme roman. Tu peux aussi
coller n'importe quel texte (chanson, article) dans un fichier `.txt`.

Ce n'est **pas** un réseau de neurones (c'est statistique), mais c'est l'outil
adapté pour apprendre beaucoup de mots d'un coup, et ça reste 100 % stdlib.

### Apprendre à coder — `codeur.py`

Le même chatbot (réseau de neurones), mais sa base de connaissances associe une
question en français à un **bout de code Python**. Tu demandes, il répond en
Python :

```bash
python3 codeur.py
```
```
Toi : comment faire une boucle qui répète
MonIA (Python) :
    for i in range(10):
        print(i)
```

Il connaît déjà les recettes de base (afficher, variables, boucles, conditions,
fonctions, listes, hasard, fichiers…) et comprend les reformulations. Tu peux
lui apprendre tes propres recettes en direct — comme le code contient souvent un
`=`, on utilise `>>>` comme séparateur :

```
apprends: comment dire bonjour >>> print("Bonjour le monde")
```

Tout est retenu dans `codeur.json` et rechargé au prochain lancement. Comme le
chatbot, il ne « comprend » pas la programmation : c'est un aide-mémoire Python
de poche qui grandit avec toi.

### Le dépanneur du terminal — `commandes.py`

Bloqué dans le terminal ? Demande-lui en français ce que tu veux faire, il te
donne **la commande exacte** (Termux / Linux / git / Python) avec une petite
explication :

```bash
python3 commandes.py
```
```
Toi : comment récupérer le code
MonIA — la commande :
    $ git pull
    (télécharge les nouveautés du projet)
```

Il connaît : se déplacer dans les dossiers (`ls`, `cd`, `pwd`, `mkdir`), les
fichiers (`nano`, `cat`, `rm`, `cp`, `mv`), `git` (`pull`, `status`, `add`/`commit`/`push`,
`clone`), Python (`python3 fichier.py`, `pip install`, `Ctrl+C`), Termux/Debian
(`apt install`, `apt update`) et comment lancer ton IA. Apprends-lui tes
astuces : `apprends: ce que tu veux faire >>> la commande` (mémoire dans
`commandes.json`).

### Connaître GitHub — `github.py`

Tout ce qu'il faut savoir sur GitHub (où vit ton projet) : il répond soit par une
**commande**, soit par une **explication**.

```bash
python3 github.py
```
```
Toi : comment cloner mon projet
MonIA — la commande :
    $ git clone https://github.com/pa8146699-del/mon-code-ia.git
    (télécharge tout le projet sur ton téléphone)

Toi : c'est quoi une pull request
MonIA : Une pull request propose de fusionner les changements d'une branche
        dans une autre ; on la crée et on la relit sur le site github.com.
```

Il connaît : cloner/récupérer/envoyer (`clone`, `pull`, `add/commit/push`), les
branches (`branch`, `checkout`), l'historique (`log`), les notions (commit, push,
pull, dépôt, pull request, `.gitignore`) et **comment se connecter avec un token**
(GitHub n'accepte plus le mot de passe). Apprends-lui tes astuces avec
`apprends: ta question >>> ta réponse` (mémoire dans `github.json`).

## Tests

```bash
python -m pytest monia/            # si pytest est installé
cd monia && python3 test_monia.py  # runner zéro-dépendance
```

24 tests : formes des poids, reproductibilité de la graine, dérivées des
activations, apprentissage de `y = 2x`, décroissance de l'erreur, apprentissage
du XOR non-linéaire, sauvegarde/rechargement de la mémoire, le chatbot
(découpage en mots, réponse à une question apprise, aveu d'ignorance,
apprentissage en direct, sauvegarde/rechargement), le générateur de texte
(découpage, apprentissage du vocabulaire, génération, sauvegarde/rechargement),
l'assistant de code (base de recettes valide, réponse en Python), le dépanneur
de commandes (base valide, bonne commande renvoyée) et l'assistant GitHub (base
valide, explique le clonage).

## Pourquoi « from scratch » ?

Pour **apprendre comment une IA fonctionne vraiment**, pas juste l'utiliser.
Ici il n'y a pas de boîte noire : un neurone est une multiplication plus une
addition, l'apprentissage est une descente de gradient, et la mémoire est un
fichier de nombres. Tout est à toi, à 100 %.

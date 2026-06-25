# 🚀 Annonce PRÊTE À PUBLIER — ton 1er service payé

> Objectif : décrocher ton 1er client en quelques jours. Service le plus simple
> et sans risque légal : **scan de secrets dans le code** (avec DataGuard).
> Copie-colle tel quel sur Fiverr / Malt / Reddit r/forhire / LinkedIn.

---

## 📌 FIVERR — la fiche complète (copier chaque champ)

**Titre du gig :**
```
I will scan your code for leaked API keys, passwords and secrets
```
*(version FR pour Malt : « Je scanne votre code pour trouver les clés API, mots de passe et secrets oubliés »)*

**Catégorie :** Programming & Tech → Cybersecurity → Security Assessment

**Tags / mots-clés :**
```
security, code review, secrets scan, api key, devsecops
```

**Description du gig :**
```
🔐 Une clé API ou un mot de passe oublié dans ton code = la porte ouverte aux
pirates. C'est l'une des causes n°1 des fuites de données.

Je passe ton code au crible avec un outil de détection professionnel et je te
remets un rapport HTML clair.

✅ Ce que je détecte :
- Clés API (AWS, Google, Stripe, GitHub, OpenAI, SendGrid...)
- Mots de passe en clair, tokens, IBAN, cartes bancaires
- Clés privées (RSA, SSH...)

✅ Ce que tu reçois :
- Un rapport HTML pro (secrets MASQUÉS, jamais exposés en clair)
- Le niveau de gravité de chaque trouvaille
- Les corrections concrètes à appliquer

✅ 100 % confidentiel · Livraison rapide · Outil maison (mon GitHub en preuve)

Envoie-moi ton code (zip ou lien repo) et je m'occupe du reste.
```

**Packages / prix :**
| Package | Prix | Contenu | Délai |
|---|---|---|---|
| Basic | 30 € | Scan jusqu'à ~20 fichiers + rapport HTML | 2 jours |
| Standard | 60 € | Projet complet + rapport + 5 recommandations | 2 jours |
| Premium | 100 € | Projet + rapport + appel de 30 min d'explications | 3 jours |

**FAQ à mettre :**
```
Q : Mes données sont-elles en sécurité ?
R : Oui. 100 % confidentiel, et aucun secret n'apparaît en clair dans le rapport
   (tout est masqué : ab***34). Je supprime ton code après la mission.

Q : Quels langages ?
R : Tous (l'outil scanne le texte : Python, JS, PHP, Java, config, .env...).

Q : Comment je t'envoie le code ?
R : Un .zip ou un lien vers ton dépôt (même privé via accès temporaire).
```

---

## 💬 MESSAGE DIRECT (Reddit r/forhire, Discord, LinkedIn)

```
Salut ! Je propose un scan de secrets sur ton code : je détecte les clés API,
tokens et mots de passe accidentellement laissés dedans (la cause n°1 des
fuites). Tu reçois un rapport HTML clair avec les corrections. 30-60 € selon la
taille, livré en 48h, 100 % confidentiel. Outil maison open-source (je peux te
montrer mon GitHub). Ça t'intéresse ?
```

---

## ✅ Comment LIVRER (quand un client dit oui)

1. Le client t'envoie son code → tu le mets dans un dossier `./code-client`
2. Tu génères le rapport :
   ```bash
   python dataguard/dataguard.py scan ./code-client --html rapport-client.html
   ```
3. Tu ouvres `rapport-client.html` pour vérifier, tu ajoutes 3-5 conseils
   (voir `service/modele-rapport.md`), tu l'envoies.
4. Tu te fais payer (via la plateforme) → tu demandes un AVIS. ⭐

---

## ⚖️ Pour encaisser légalement
Statut le plus simple en France = **micro-entrepreneur** (gratuit, déclaration en
ligne ~15 min sur autoentrepreneur.urssaf.fr). Tu peux décrocher le 1er client
d'abord et faire la démarche en parallèle. C'est ce qui rend le paiement légal.

## 🎯 Objectif réaliste
```
3 premiers clients à 30-40 € (prix d'appel pour récolter des avis)
→ ensuite tu montes à 60-100 €
→ 1 client/semaine = ~240 €/mois pendant que tu montes en skill bug bounty.
```

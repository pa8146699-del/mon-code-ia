# 📓 Hacker101 CTF — journal d'apprentissage

> Le CTF officiel de HackerOne (`ctf.hacker101.com`). Du vrai hacking en mode
> défis. **But concret : atteindre 26 points → débloque des invitations à des
> programmes PRIVÉS** (peu de concurrents = vraie chance de 1er bug payé).

Pseudo : **hackgh0st**

---

## 🏆 Défis résolus

| Défi | Difficulté | Flags | Compétence apprise |
|---|---|---|---|
| A little something to get you started | Trivial | 1/1 ✅ | Flag caché dans une **image** (background.png) |
| Micro-CMS v1 | Easy | 1/4 | **IDOR** : page privée éditable (contrôle d'accès cassé) |

Score : **3/26 points**

---

## 🔑 LA leçon n°1 (à ne jamais oublier)

```
Un flag a la forme :  ^FLAG^....hex....$FLAG$

⚠️ Quand un tuto écrit "^FLAG^.....$FLAG$" avec des points,
   les POINTS ne sont PAS à taper ! C'est juste le FORMAT.

Le VRAI flag = 64 caractères hex réels :
   ^FLAG^d5ea34d7d6e7bc6626a3301f7a9b12bb...$FLAG$

→ On soumet le VRAI (les 64 caractères), pas les points.
→ "you can omit everything but the hex" : on peut coller juste le hex.
```

---

## 🧠 Méthode pour trouver un flag

```
1. Regarder le CODE SOURCE de la page (pas juste l'affichage)
   → curl -s -A "Mozilla/5.0" "URL"
2. Repérer un indice : image de fond, page cachée, commentaire HTML...
3. Extraire le flag :
   curl -s -A "Mozilla/5.0" "URL" | grep -oE '[0-9a-f]{64}'
4. Submit Flag (menu en haut de ctf.hacker101.com) → coller → check
```

---

## Défi 1 — Flag dans une image 🖼️

```
Page "vide" avec : background-image: url("background.png")
→ le flag était DANS l'image (forensics/stégano basique)
→ ouvrir l'image dans Chrome → flag visible dedans
```

---

## Défi 2 — Micro-CMS v1 : l'IDOR 🚪

```
Pages publiques : /page/1 (Testing), /page/2 (Markdown Test)
Pages /page/3,4,5 en VUE → 404 (cachées)

LA FAILLE (Broken Access Control) :
→ La page privée fait 404 en LECTURE (/page/4)
→ MAIS elle est ÉDITABLE sans autorisation (/page/edit/4) !
→ Le contrôle d'accès manque sur l'édition.
→ Le flag est dans le corps de la page privée éditée.

Commande qui l'a trouvé :
  for i in 1 2 3 4 5 6; do echo "--- edit/$i ---"; \
  curl -s -A "Mozilla/5.0" "$B/page/edit/$i" | grep -iE 'FLAG|Private'; done
```

Reste à trouver (même esprit) :
```
🎯 XSS dans le titre d'une page (indice : "scripts are not supported")
🎯 XSS via markdown dans le corps
🎯 SQL injection dans l'ID de page
```

---

## ⚠️ Pièges rencontrés

```
- Les INSTANCES redémarrent (l'URL change : b7ad5ccd → 891d3e93...)
  → à chaque redémarrage, les FLAGS changent.
  → extraire ET soumettre sur la MÊME instance vivante (vite).
- Copier depuis le terminal sur mobile = galère (lignes coupées)
  → préférer la copie dans le NAVIGATEUR, ou coller le hex à part.
- ctf.hacker101.com (la plateforme, avec "Submit Flag")
  ≠ tf.hacker101.com / [hash].ctf... (l'instance à hacker)
```

---

## 🗺️ Plan

```
1. Finir Micro-CMS v1 (les 3 flags restants : XSS x2, SQLi)
2. Enchaîner les défis Web faciles (Postbook = 7 flags !)
3. Atteindre 26 points → invitations à des programmes privés
4. Chasser sur ces programmes privés (peu de concurrence)
```

---

*Journal à compléter à chaque défi. 🚩*

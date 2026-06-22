# 📖 Catalogue OWASP Top 10 — la checklist du hacker

> Le **catalogue de failles** qu'un hacker/pentester teste **méthodiquement** sur
> chaque cible. Trouver une faille = 90 % méthode + 10 % intuition : on connaît
> cette liste et on la passe en revue, une par une, sur chaque point d'entrée.

---

## 🌐 OWASP Top 10 — Web (2021)

| # | Faille | C'est quoi | Comment la chercher |
|---|---|---|---|
| **A01** | **Broken Access Control** ✅ | Accéder à un truc interdit | Changer un ID / une URL / un rôle (IDOR) |
| **A02** | Cryptographic Failures | Données mal/pas chiffrées | HTTP au lieu de HTTPS, mots de passe en clair |
| **A03** | **Injection** | Injecter du code dans une entrée | `' OR 1=1` (SQLi), `<script>` (XSS) |
| **A04** | Insecure Design | Logique métier mal pensée | Détourner un workflow (payer 0 €…) |
| **A05** | Security Misconfiguration | Mauvaise config | Page admin par défaut, erreurs verboses, fichiers exposés |
| **A06** | Vulnerable Components | Vieilles libs à failles connues | Détecter la version → chercher la CVE |
| **A07** | Auth Failures | Authentification faible | Brute-force, sessions mal gérées |
| **A08** | Data Integrity Failures | Données/updates non vérifiés | Manipuler un objet sérialisé, un update |
| **A09** | Logging Failures | Pas de détection | (surtout défensif) |
| **A10** | **SSRF** | Forcer le serveur à appeler une URL | Mettre une URL interne dans un champ |

### Les plus rentables pour débuter 💰
```
🥇 A01 Broken Access Control → déjà maîtrisé (IDOR)
🥇 A03 Injection (surtout XSS) → très courant, payé partout
🥉 A05 Misconfiguration → fichiers exposés, faciles à trouver
→ A01 + A03 = ~70 % des bugs trouvés en bug bounty
```

---

## 📱 OWASP Mobile Top 10 (pour MobSF)

| # | Faille |
|---|---|
| M1 | Mauvais usage des identifiants |
| M2 | Sécurité de la chaîne d'approvisionnement |
| M3 | Auth / autorisation faible |
| M4 | Validation des entrées insuffisante |
| M5 | Communication non sécurisée (cleartext HTTP) |
| M6 | Contrôles de confidentialité insuffisants |
| M7 | Mauvaise protection du binaire |
| M8 | Mauvaise configuration de sécurité (ex : **signature debug**) |
| M9 | Stockage de données non sécurisé |
| M10 | Cryptographie insuffisante |

> MobSF coche automatiquement cette liste sur un APK → toi tu **interprètes**
> (permissions justifiées ? secrets en dur ? trafic cleartext ? signature release ?).

---

## 🧠 La méthode du hacker (à appliquer sur chaque entrée)

```
1. CARTOGRAPHIER les entrées (URLs, paramètres, formulaires, cookies, en-têtes,
   permissions, composants exportés...)
2. Pour CHAQUE entrée, dérouler le catalogue :
     → A01 : et si je change l'ID ?
     → A03 : et si j'injecte ' ou <script> ?
     → A10 : et si je mets une URL interne ?
     ...
3. TESTER → OBSERVER la réaction (réponse différente = piste)
4. CONFIRMER + prouver l'impact
```

---

## ⚖️ Rappel légal (toujours)

```
On teste UNIQUEMENT : ses propres systèmes, des labs (PortSwigger),
ou le SCOPE d'un programme bug bounty.
Le phishing / social engineering = quasi toujours HORS SCOPE → interdit.
La valeur (et l'argent) est côté DÉTECTION/DÉFENSE (cf. DataGuard).
```

---

## 🎯 Plan d'entraînement

PortSwigger a **un module par faille** de ce catalogue :
```
✅ Access Control (A01) — fait (4 labs)
⏭️ XSS (A03) — prochain
   puis SQL injection, Authentication, SSRF...
```

*À compléter au fil des labs. 🚀*

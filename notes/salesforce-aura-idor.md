# 🧨 Salesforce Experience Cloud — exposition Guest User (API Aura)

> Classe de failles très répandue et bien payée en bug bounty. Cible : les sites
> Salesforce "Experience Cloud / Community" (reconnaissables à la CSP avec
> `*.salesforce.com`, `*.force.com`, `/s/sfsites/aura`).
> Référence d'autorité : **Aaron Costello** — site **enumerated.io**
> ("Hacking Salesforce Lightning Communities"). À LIRE avant de tester.

## 🎯 L'idée
Les sites Experience Cloud exposent une API interne **Aura**. Si l'admin a mal
configuré les permissions de l'utilisateur **Guest** (invité, non connecté), un
visiteur anonyme peut **lire des objets/records qui devraient être privés**
(Account, Contact, Case, User, objets custom `__c`...). C'est une
**misconfiguration**, testable **sans compte** (pas besoin d'inscription).

## 🔎 Détection (non destructif)
```bash
# 1. L'endpoint Aura existe ?
curl -s -o /dev/null -w "%{http_code}\n" -A "Mozilla/5.0" \
  -H "X-HackerOne-Researcher: hackgh0st" \
  "https://CIBLE/s/sfsites/aura"
# 200 / 401 / 405 = présent

# 2. Extraire le contexte Aura (fwuid + app descriptor) depuis la page
curl -s -L -A "Mozilla/5.0" -H "X-HackerOne-Researcher: hackgh0st" \
  "https://CIBLE/s/" | grep -oE 'fwuid[^,]*|"app":"[^"]*"|markup://[^"]*' | head
```

## 🧪 Principe de l'énumération (à faire surtout sur PC / avec outillage)
Un POST sur `/s/sfsites/aura` avec un `message` qui appelle une action Aura
permet de lister les objets accessibles et tirer des records. Actions classiques :
- `ApexActionController` (méthodes Apex exposées)
- `RecordUiController.getRecordWithFields` (lire un record précis)
- `ListUiController` / `getItems` (lister des records d'un objet)

Le POST a besoin de `aura.context` (avec `fwuid`, `app`) + `aura.token`
(souvent `null`/`undefined` côté Guest — c'est ça qui rend l'accès possible).

⚠️ Construire ces requêtes à la main est fastidieux. Pour la VRAIE exploitation,
utiliser l'outillage public dédié (chercher : "Salesforce Aura enumeration tool
github", recherche d'Aaron Costello). Sur PC + Burp = beaucoup plus simple.

## ⚖️ LIMITES (respect policy = ne pas se faire bannir / rester légal)
```
✅ Objectif = PROUVER l'exposition avec le MINIMUM (1-2 records suffisent comme PoC)
❌ NE JAMAIS aspirer en masse la base / les PII clients (interdit par la policy)
✅ Header X-HackerOne-Researcher sur TOUTES les requêtes
✅ Dès que l'expo est prouvée → STOP → rédiger le rapport
✅ Ne pas modifier/supprimer de données (lecture seule, et minimale)
```

## 📝 Squelette de rapport (format Coupang)
```
Summary  : Le Guest User du site Salesforce <host> a des permissions trop larges,
           permettant à un utilisateur non authentifié de lire l'objet <X>.
Steps    : 1. GET /s/sfsites/aura (200) 2. extraire fwuid/app
           3. POST aura getItems sur l'objet <X> 4. records renvoyés sans auth
Impact   : Un attaquant anonyme peut lire <type de données> de tous les
           enregistrements <X> → exposition de données / atteinte confidentialité.
PoC      : 1-2 records masqués (PAS de dump massif), capture de la requête/réponse.
Public?  : non
```

## 💡 Pourquoi c'est une compétence rentable
Des MILLIERS d'entreprises utilisent Salesforce Experience Cloud, et la
misconfiguration Guest User est super fréquente. Maîtriser ce test = des bugs
réutilisables sur beaucoup de programmes. C'est un excellent "money skill".

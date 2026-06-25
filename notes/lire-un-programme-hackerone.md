# 📑 Lire un programme HackerOne — le réflexe AVANT de tester

> À faire sur CHAQUE programme, avant de lancer le moindre outil.
> Mal lire le scope/policy = rapport rejeté, voire ban + risque légal.

---

## 1. Les 4 onglets à lire dans l'ordre

| Onglet | Ce que tu cherches |
|---|---|
| **Policy** | Règles, Safe Harbor, interdits, format de rapport |
| **Scope / In scope** | Les actifs que tu as le DROIT de tester (domaines, apps, IP) |
| **Out of scope** | Ce qui est INTERDIT (ne JAMAIS toucher) |
| **Hacktivity** | Les bugs déjà payés → t'inspire des types de failles qui marchent |

## 2. Le SCOPE = ta zone de jeu légale

```
Tu testes UNIQUEMENT ce qui est listé "In scope".
- *.exemple.com  → wildcard : TOUS les sous-domaines (large = bon pour débuter)
- app.exemple.com → un seul host (étroit = plus dur, souvent déjà ratissé)
Hors scope / actifs tiers = ILLÉGAL, même via HackerOne.
```

## 3. Vérifier que le programme est bon (avant d'investir du temps)

```
✅ Bounty (pas juste VDP) si tu veux être payé — VDP = réputation seulement
✅ Safe Harbor présent = protection légale si tu respectes la policy
✅ Response efficiency élevé (90-100%) = ils traitent vraiment
✅ Scope LARGE (wildcard) = surface fraîche = ta chance de 1er bug
✅ Programme récent / peu de hackers = moins de concurrence
```

## 4. Les INTERDITS universels (presque tous les programmes)

```
❌ Brute force / deviner des identifiants
❌ Déni de service (DoS), faire tomber le service
❌ Uploader un shell / backdoor
❌ Ingénierie sociale (employés, clients, support)
❌ Attaques physiques
❌ Accéder / modifier / exfiltrer des données réelles (PII)
❌ Changer le mot de passe d'un compte qui n'est pas le tien
❌ Tester des actifs tiers (hors scope)
❌ Divulguer publiquement sans accord écrit
```
→ Principe : prouver la faille avec le MINIMUM, zéro dégât, et ne plus y toucher.
   Pour tester : utiliser TES propres comptes de test (compte A vs compte B).

## 5. Le FORMAT DE RAPPORT (ce qui fait payer ou rejeter)

```
1. Cible affectée (URL / fonctionnalité précise)
2. Description du problème (clair, court)
3. Impact ← LE PLUS IMPORTANT : "grâce à ça, un attaquant peut FAIRE QUOI ?"
4. Steps to reproduce (étape par étape, reproductible par eux)
5. Proof of Concept (capture, requête curl, vidéo si demandé)
6. Est-ce déjà public ? (oui/non)
```

**Règle d'or du montant :** le paiement suit l'IMPACT (score CVSS), pas la trouvaille.
```
❌ "J'ai trouvé un IDOR sur /user?id=5"
✅ "Via cet IDOR, n'importe quel utilisateur peut lire/modifier les données
    de TOUS les autres comptes (PII : email, adresse) → impact confidentialité élevé"
```

## 6. Pièges à éviter
```
- Doublon : seul le 1ER qui reporte est payé → viser du scope frais, aller vite.
- 0-day public : souvent pas éligible avant 30 j après patch.
- "Théorique" : refusé. Il faut un vrai scénario d'exploitation démontré.
- Rapport hors format : rejeté direct, même si le bug est réel.
```

## 7. Bugs réalistes pour un débutant (bon ratio effort/résultat)
```
🎯 IDOR / Broken Access Control → manipuler des id pour accéder à ce qui n'est pas à toi
🎯 Information disclosure → infos sensibles exposées (config, .git, clés)
🎯 XSS → injection de script dans un champ reflété/stocké
🎯 Misconfigurations → en-têtes manquants, fichiers exposés, CORS large
```

---

> Workflow type après lecture du scope :
> `subfinder` (sous-domaines) → `httpx` (lesquels répondent) → `nmap -sV` (services)
> → explorer les apps web → chercher IDOR/XSS/access control → rapport au format.

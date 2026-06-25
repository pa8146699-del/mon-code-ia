# 🎯 Coupang Taïwan — fiche de chasse (HackerOne)

> Programme : Coupang Taïwan (e-commerce). Prime 50$–6000$. Scope = liste de
> hosts précis (PAS de wildcard) → on teste UNIQUEMENT ces hosts.
> Pseudo H1 : **hackgh0st** · Email de test : **hackgh0st@wearehackerone.com**

## ⚙️ Règles opérationnelles (OBLIGATOIRE sinon rapport rejeté)
- Header sur CHAQUE requête de test : `X-HackerOne-Researcher: hackgh0st`
- Comptes de test créés avec l'alias `hackgh0st@wearehackerone.com`
- IDOR : seulement avec **id PRÉVISIBLES** (1,2,3,42...). UUID aléatoire = refusé.
- Tester UNIQUEMENT sur SES propres comptes (A vs B). Jamais les données d'un vrai client.
- INTERDIT : DoS, infra, brute force, ingénierie sociale, self-XSS, MITM/root,
  CSRF-logout, en-têtes manquants, version/bannière, fuites d'IP interne, failles connues.

## 📋 Scope complet (in scope) — 45 URLs + 2 apps
```
ads-partners.tw.coupang.com
cart-front-api.tw.coupang.com
cart.tw.coupang.com
cash.tw.coupang.com
checkout.tw.coupang.com
cmapi.tw.coupang.com
dco.tw.coupang.com
developers.tw.coupangcorp.com
feed-web.tw.coupang.com
fileupload.tw.coupang.com
fileupload-video.tw.coupang.com
fintech-aml-kyc-tw.coupang.com
go-cms.tw.coupang.com
helpcenter-tw.coupangcorp.com
helpseller.tw.coupangcorp.com
id.tw.coupang.com
influencers.tw.coupang.com
link.tw.coupang.com
ljc-test.tw.coupang.com
ljc.tw.coupang.com
logs-partners.tw.coupang.com
loyalty.tw.coupang.com
marketplace.tw.coupangcorp.com
mauth.tw.coupang.com
mc.tw.coupang.com
member.tw.coupang.com
m.tw.coupang.com
myself.tw.coupang.com
my.tw.coupang.com
notification-front-web.tw.coupang.com
pages.tw.coupang.com
partners.tw.coupang.com
payment.tw.coupang.com
pay.tw.coupang.com
promo.tw.coupang.com
reco.tw.coupang.com
review.tw.coupang.com
rs-open-api.tw.coupang.com
shop.tw.coupang.com
store-display.tw.coupang.com
syndication.tw.coupang.com
tw.coupang.com
tw.coupangcorp.com
tw.coupangls.com
www.tw.coupang.com
SUPERAPP (Android) + SUPERAPP (iOS)
```

## ⭐ Cibles prioritaires pour débuter (IDOR / accès / logique)
```
APIs (id prévisibles fréquents) : cart-front-api, rs-open-api, cmapi, dco
Pages perso (données utilisateur): my, myself, member, mc
Avis / contenu utilisateur       : review (modifier/supprimer l'avis d'un autre ?)
Panier / commande (logique)      : cart, checkout (manipulation de prix/quantité ?)
Support (IDOR sur n° de ticket)  : helpcenter-tw, helpseller
Portails partenaires (+ faibles) : influencers, partners, ads-partners, marketplace
Auth                             : id, mauth (failles login/compte)
À éviter au début (sensible $)   : payment, pay, cash, fintech-aml-kyc
```

## 🔭 Plan de recon
```
1. httpx sur toute la liste → qui est vivant, code HTTP, titre, techno
2. Repérer ceux avec login/app web et ceux qui sont des API (JSON)
3. Sur une app à login : créer compte A + compte B (alias wearehackerone)
4. Chercher l'IDOR : ressource de A (id prévisible) → tenter d'y accéder en B
5. Confirmer l'impact → rapport au format Coupang (Summary/Steps/Impact/PoC)
```

## ⚠️ Hurdle pratique possible
L'inscription Coupang TW peut demander un n° de téléphone taïwanais. Si bloqué :
→ tester les endpoints publics / le comportement des API non authentifiées,
   et les portails partenaires qui ont parfois une inscription ouverte.

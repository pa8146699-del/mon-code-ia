# 📄 Modèle de rapport client

> Structure simple et pro à remettre au client. Pour le Service 1 (scan de
> secrets), DataGuard génère déjà un rapport HTML (`report.py`) — tu peux
> l'envoyer tel quel, ou reprendre cette structure pour un rendu personnalisé.

---

## RAPPORT D'ANALYSE DE SÉCURITÉ

**Client :** _______________
**Prestataire :** _______________
**Date :** __/__/____
**Périmètre analysé :** _______________
**Type d'analyse :** _______________ (scan de secrets / phishing / checkup site)

---

### 1. Résumé pour le décideur (1 paragraphe simple)
> En clair, sans jargon : qu'est-ce qui a été analysé, et le niveau de risque
> global (faible / moyen / élevé). Exemple :
> *« L'analyse de votre code a révélé 2 problèmes de gravité élevée (clés API
> exposées) à corriger en priorité, et 3 points mineurs. Une fois corrigés,
> votre niveau de sécurité sera bon. »*

---

### 2. Résultats détaillés

| # | Problème trouvé | Gravité | Où | Recommandation |
|---|---|---|---|---|
| 1 | Clé API exposée (masquée : ab***34) | 🔴 Élevée | fichier config.py | Révoquer la clé + la sortir du code (variable d'env) |
| 2 | … | 🟠 Moyenne | … | … |
| 3 | … | 🔵 Faible | … | … |

> ⚠️ Ne JAMAIS écrire un secret en clair dans le rapport. Toujours masqué
> (DataGuard le fait automatiquement : 4 premiers + *** + 2 derniers).

---

### 3. Recommandations prioritaires (les 3-5 actions clés)
```
1. _______________
2. _______________
3. _______________
```

---

### 4. Bonnes pratiques générales (valeur ajoutée gratuite)
```
✅ Stocker les secrets dans des variables d'environnement, jamais dans le code
✅ Activer la double authentification (2FA) partout
✅ Utiliser un gestionnaire de mots de passe
✅ Mettre à jour régulièrement les dépendances / le CMS
✅ Forcer HTTPS sur tout le site
```

---

### 5. Conclusion
> Une phrase positive + une proposition de suivi :
> *« Votre [code/site] est sur de bonnes bases. Je reste disponible pour vérifier
> les corrections une fois appliquées (re-scan offert sous 30 jours). »*

---

## 💡 Astuces pour un rapport qui inspire confiance

```
✅ Clair et SANS jargon (le client n'est pas technique)
✅ Toujours des SOLUTIONS, pas juste des problèmes
✅ Masquer tout secret / donnée sensible
✅ Une touche positive à la fin (le client se sent aidé, pas jugé)
✅ Propose un re-scan de vérif → fidélise + nouvelle vente
```

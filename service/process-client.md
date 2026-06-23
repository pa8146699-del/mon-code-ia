# 🔄 Process de livraison + Autorisation

## Checklist de mission (de A à Z)

```
☐ 1. Le client accepte l'offre + le prix
☐ 2. Tu fais signer/valider l'AUTORISATION écrite (voir + bas)
☐ 3. Le client te transmet le périmètre :
       - Service 1 : son code (zip / lien repo)
       - Service 2 : ses mails suspects
       - Service 3 : l'URL exacte du site + accord écrit
☐ 4. Tu lances l'analyse (DataGuard / nuclei)
☐ 5. Tu génères le rapport (modele-rapport.md / report.py HTML)
☐ 6. Tu ajoutes 3-5 recommandations concrètes
☐ 7. Tu envoies le rapport + tu te fais payer
☐ 8. Tu demandes un avis/témoignage
```

---

## Commandes selon le service

### Service 1 — Scan de secrets
```bash
# Le client t'a donné son code (dossier ./code-client)
python dataguard/dataguard.py scan ./code-client --html rapport-client.html
```
→ `rapport-client.html` = un rapport HTML pro à envoyer tel quel.

### Service 2 — Phishing
```bash
# Pour un mail suspect enregistré dans mail.txt
python dataguard/dataguard.py phishing --file mail.txt --json
```
→ score de risque + signaux détectés, que tu reformules pour le client.

### Service 3 — Checkup site (AVEC autorisation écrite)
```bash
# Recon léger + scan poli (jamais agressif)
nuclei -u https://site-du-client.com -severity medium,high,critical -rate-limit 10
```
→ tu interprètes et priorises les résultats dans le rapport.

---

## ⚖️ MODÈLE D'AUTORISATION ÉCRITE (à faire valider AVANT tout test)

> **Autorisation de test de sécurité**
>
> Je soussigné·e _______________ (nom, fonction), représentant légitime de
> _______________ (entreprise / propriétaire du site _______________),
> autorise _______________ (ton nom / pseudo pro) à réaliser une analyse de
> sécurité **non destructive** sur le périmètre suivant :
>
> - Périmètre autorisé : _______________ (ex : https://monsite.com uniquement)
> - Période : du __/__/____ au __/__/____
> - Type de test : analyse passive et scan de vulnérabilités non intrusif
>
> Le prestataire s'engage à : ne pas dégrader le service, ne pas accéder ni
> divulguer de données personnelles, et remettre un rapport confidentiel.
>
> Fait le __/__/____ — Signature : _______________

```
⚠️ PAS d'autorisation = PAS de test. Aucune exception.
   Un email du client qui dit clairement "je t'autorise à tester X" suffit
   pour démarrer, mais le modèle signé est plus solide.
```

---

## Règles de prudence

```
✅ Scan TOUJOURS poli (-rate-limit bas) → ne jamais faire tomber le site
✅ Reste STRICTEMENT dans le périmètre autorisé
✅ Ne touche jamais aux données personnelles / ne les copie pas
✅ Si tu trouves un truc grave → préviens le client, ne l'exploite pas
✅ Garde tout confidentiel (rapport, accès, résultats)
```

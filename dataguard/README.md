# DataGuard

Boîte à outils de sécurité en ligne de commande, sans aucune dépendance
externe (bibliothèque standard de Python 3 uniquement). DataGuard regroupe
trois fonctions :

1. **scan** — détecte les données sensibles (clés API, mots de passe,
   e-mails, cartes bancaires, IBAN…) avant qu'elles ne fuient.
2. **phishing** — évalue le risque d'hameçonnage d'un texte ou d'un e-mail.
3. **install-hook** — installe un hook git qui bloque les commits contenant
   des secrets.

## Sous-commande `scan`

```bash
python dataguard/dataguard.py scan mon_fichier.txt          # rapport terminal
python dataguard/dataguard.py scan mon_projet/              # dossier (récursif)
python dataguard/dataguard.py scan mon_projet/ --json       # sortie JSON
python dataguard/dataguard.py scan mon_projet/ --html rapport.html  # rapport HTML
python dataguard/dataguard.py scan mon_projet/ --strict     # code 1 si fuite (CI)
```

### Ce que `scan` détecte

| Type | Gravité |
|---|---|
| Clé privée (RSA, EC, OpenSSH…) | élevée |
| Clés API AWS, Anthropic, OpenAI, Google, Stripe, SendGrid | élevée |
| Jetons GitHub, Slack, OAuth Google | élevée |
| Mot de passe en clair | élevée |
| IBAN | élevée |
| Numéro de carte bancaire (validé par Luhn) | élevée |
| Jeton JWT, webhook Slack, secret/token générique | moyenne |
| Adresse e-mail, numéro de téléphone (FR), adresse IPv4 | faible |

Les valeurs détectées sont **masquées** dans tous les rapports (ex.
`AKIA***EF`) : le secret n'est jamais réaffiché en entier.

## Sous-commande `phishing`

Analyse un texte et calcule un score de risque (0-100) à partir d'indices :
langage d'urgence, demande d'identifiants, liens suspects, domaines sosies
(`paypa1.com`), liens vers une IP, raccourcisseurs d'URL, pièces jointes
dangereuses…

```bash
python dataguard/dataguard.py phishing --text "URGENT confirmez vos identifiants..."
python dataguard/dataguard.py phishing --file mail.txt
cat mail.txt | python dataguard/dataguard.py phishing        # depuis stdin
python dataguard/dataguard.py phishing --file mail.txt --json --strict
```

## Sous-commande `install-hook`

Installe un hook `pre-commit` dans le dépôt git courant. Tout commit
contenant un secret dans les fichiers indexés sera refusé.

```bash
python dataguard/dataguard.py install-hook            # installe le hook
python dataguard/dataguard.py install-hook --force    # écrase un hook existant
```

## Tests

```bash
python -m pytest dataguard/        # si pytest est installé
python dataguard/test_dataguard.py # exécution sans dépendance
```

## Notes

- Les numéros de carte sont validés par l'algorithme de Luhn pour réduire
  les faux positifs.
- Les dossiers `.git`, `node_modules`, `__pycache__`, `venv`/`.venv` et les
  fichiers binaires courants sont ignorés lors d'un scan de dossier.

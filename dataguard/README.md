# DataGuard

Scanner anti-fuite de données en ligne de commande. DataGuard analyse un
fichier ou un dossier et détecte les données sensibles (clés API, mots de
passe, e-mails, numéros de carte bancaire, etc.) **avant** qu'elles ne
fuient lors d'un partage ou d'un commit.

Aucune dépendance externe : uniquement la bibliothèque standard de Python 3.

## Utilisation

```bash
# Scanner un fichier
python dataguard/dataguard.py mon_fichier.txt

# Scanner un dossier entier (récursif)
python dataguard/dataguard.py mon_projet/

# Résultat au format JSON
python dataguard/dataguard.py mon_projet/ --json

# Mode strict : code de sortie 1 si une fuite est trouvée (utile en CI)
python dataguard/dataguard.py mon_projet/ --strict
```

## Ce que DataGuard détecte

| Type | Gravité |
|---|---|
| Clé privée (RSA, EC, OpenSSH…) | élevée |
| Clé API AWS, Anthropic, OpenAI | élevée |
| Jeton GitHub | élevée |
| Mot de passe en clair | élevée |
| Numéro de carte bancaire (validé par Luhn) | élevée |
| Jeton JWT | moyenne |
| Secret / token générique | moyenne |
| Adresse e-mail | faible |
| Adresse IPv4 | faible |

## Notes

- Les valeurs détectées sont **masquées** dans le rapport pour ne pas
  réafficher le secret en entier.
- Les numéros de carte sont validés par l'algorithme de Luhn afin de
  réduire les faux positifs.
- Les dossiers `.git`, `node_modules`, `__pycache__`, `venv`/`.venv` et les
  fichiers binaires courants sont ignorés.

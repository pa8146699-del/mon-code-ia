# 📱 DataGuard sur Termux

Installe et lance la boîte à outils cybersécurité **DataGuard** (scan de
secrets + analyse de phishing) directement sur ton téléphone Android, dans
[Termux](https://termux.dev). Aucune dépendance pip : DataGuard est en
bibliothèque standard Python 3 pure, donc l'installation est légère et rapide.

## Installation en une ligne

Ouvre Termux et colle :

```bash
curl -fsSL https://raw.githubusercontent.com/pa8146699-del/mon-code-ia/main/termux/install.sh | bash
```

Ça met à jour Termux, installe `python` + `git`, clone le dépôt dans
`~/mon-code-ia` et crée la commande `dataguard`.

## Installation manuelle

```bash
pkg install -y git
git clone https://github.com/pa8146699-del/mon-code-ia
bash mon-code-ia/termux/install.sh
```

## Utilisation

Après l'installation, la commande `dataguard` est disponible partout :

```bash
dataguard                              # menu interactif (idéal au doigt)
dataguard scan ~/storage/downloads     # scanne un dossier
dataguard scan fichier.txt --json      # sortie JSON
dataguard phishing --text "Votre compte expire, cliquez vite"
cat mail.txt | dataguard phishing      # depuis l'entrée standard
```

### Scanner tes propres fichiers

Pour que Termux puisse lire tes dossiers Android (Téléchargements, Documents…) :

```bash
termux-setup-storage      # autorise l'accès, puis :
dataguard scan ~/storage/downloads
```

## Mise à jour

```bash
bash ~/mon-code-ia/termux/update.sh
```

(équivaut à un `git pull` dans le dépôt).

## Que détecte DataGuard ?

- **Secrets / fuites** : clés privées, clés API (AWS, Anthropic, OpenAI,
  Google, Stripe, SendGrid…), tokens (GitHub, Slack, JWT), mots de passe en
  clair, IBAN, numéros de carte (validés par Luhn), e-mails, téléphones, IP.
  Toutes les valeurs sont **masquées** dans les rapports.
- **Phishing** : score 0-100 selon l'urgence, la demande d'identifiants, les
  liens HTTP/IP/raccourcis, les domaines sosies (`paypa1.com` → paypal), les
  pièces jointes dangereuses, etc.

Voir [`../dataguard/README.md`](../dataguard/README.md) pour le détail complet.

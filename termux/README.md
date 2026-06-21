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

---

## 🐧 Environnement à contrôle complet (Debian dans Termux)

⚠️ **N'installe PAS Termux depuis le Play Store** : cette version est gelée et
bridée (paquets bloqués). Installe la vraie version, complète et non
restreinte, depuis :

- **F-Droid** : <https://f-droid.org/packages/com.termux/>
- **GitHub Releases** : <https://github.com/termux/termux-app/releases>

Pour un **contrôle total** (apt complet, n'importe quel paquet, ton propre
`$HOME`, sans root), installe un vrai Linux Debian *à l'intérieur* de Termux
via `proot-distro` :

```bash
curl -fsSL https://raw.githubusercontent.com/pa8146699-del/mon-code-ia/main/termux/setup-distro.sh | bash
```

Le script :
1. installe `proot-distro` ;
2. installe **Debian** (rootfs complet) ;
3. y installe `python3` + `git`, clone le dépôt et pose la commande
   `dataguard` dans `/usr/local/bin` ;
4. crée le raccourci `debian-cyber` côté Termux pour entrer dans ce Linux.

Ensuite :

```bash
debian-cyber                  # entre dans ton Debian (contrôle complet)
# … à l'intérieur :
dataguard                     # la boîte à outils
apt install <ce-que-tu-veux>  # apt complet, rien n'est bridé
```

> **Choix de la distro** : Debian est le défaut recommandé (stable, léger, non
> restreint). `proot-distro` sait aussi installer `ubuntu`, `archlinux` ou
> `kali-linux` — remplace la variable `DISTRO` en haut de `setup-distro.sh`
> pour en changer. N'utilise des outils offensifs que sur des cibles que tu es
> **autorisé** à tester.

## Que détecte DataGuard ?

- **Secrets / fuites** : clés privées, clés API (AWS, Anthropic, OpenAI,
  Google, Stripe, SendGrid…), tokens (GitHub, Slack, JWT), mots de passe en
  clair, IBAN, numéros de carte (validés par Luhn), e-mails, téléphones, IP.
  Toutes les valeurs sont **masquées** dans les rapports.
- **Phishing** : score 0-100 selon l'urgence, la demande d'identifiants, les
  liens HTTP/IP/raccourcis, les domaines sosies (`paypa1.com` → paypal), les
  pièces jointes dangereuses, etc.

Voir [`../dataguard/README.md`](../dataguard/README.md) pour le détail complet.

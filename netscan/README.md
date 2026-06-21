# 📡 NetScan

Une appli Android (Kivy) qui **scanne ton réseau local et les ports** d'une
machine, façon mini-Nmap tactile. **100 % bibliothèque standard** (aucune
dépendance en dehors de Kivy) : elle fait un scan « TCP connect » (`connect()`),
qui ne nécessite **pas** les privilèges root.

## Deux modes

| Bouton | Action |
|---|---|
| 🌐 **Scanner le réseau** | teste les 254 hôtes d'un `/24` (ex: `192.168.1.0/24`) et liste ceux qui ont des ports courants ouverts |
| 🎯 **Scanner un hôte** | teste tous les ports courants d'une IP précise (ex: `192.168.1.10`) |

Au lancement, l'appli **devine automatiquement** ton préfixe réseau (ex:
`192.168.1`). Tu peux le modifier, ou taper une IP complète.

Ports testés : `21 ftp, 22 ssh, 23 telnet, 25 smtp, 53 dns, 80 http, 110 pop3,
139 netbios, 143 imap, 443 https, 445 smb, 3306 mysql, 3389 rdp, 5900 vnc,
8080 http-alt`.

Le scan tourne sur un **thread de fond** (100 hôtes en parallèle) ; l'interface
reste fluide et affiche les hôtes au fur et à mesure.

## ⚖️ Usage légal

À n'utiliser **que sur tes propres réseaux/machines** ou avec une autorisation
explicite. Scanner le réseau d'autrui sans accord est **illégal**.

> 💡 Sur **données mobiles (4G/5G)** ou derrière un **VPN**, il n'y a pas de
> réseau local à scanner → connecte-toi en **Wi-Fi** chez toi pour voir tes
> appareils (box, TV, autres téléphones…).

## Construire l'APK

Comme les autres apps du dépôt, l'APK se construit **en CI, pas en local** :

- Le workflow **`Build APK NetScan`** se déclenche sur **`workflow_dispatch`**
  (bouton « Run workflow » dans l'onglet Actions) ou sur un **push vers `main`**
  touchant `netscan/**` (ou le fichier du workflow).
- L'APK est publié dans les **artéfacts** du run (`netscan-apk`).
- Contrairement à `mobile/`/`monappli/`/`agentmobile/`, **rien n'est copié au
  build** : NetScan est autonome (`main.py` seul).

## Tester l'interface sur ordinateur

```bash
pip install kivy
python netscan/main.py
```

## Équivalent en ligne de commande

La même logique en script pur (pratique sur Termux/Kali) :

```bash
python3 -c "import socket;[print(p) for p in [80,443] ]"   # (voir le tuto)
```

…ou le `netscan.py` que tu as construit pas à pas dans le terminal.

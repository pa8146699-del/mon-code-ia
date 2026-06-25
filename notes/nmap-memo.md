# 🛰️ Nmap — mémo de l'apprenti hacker

> L'outil n°1 pour la recon réseau. Déjà installé dans le Debian/Kali (Termux).
> ⚖️ On ne scanne QUE : `scanme.nmap.org`, ses propres machines (127.0.0.1, son
> réseau), ou un scope HackerOne autorisé. Scanner une IP au hasard = délit.

Cible d'entraînement légale officielle : **`scanme.nmap.org`**

---

## 📋 Les commandes essentielles

```bash
# 1. Scan de base — quels ports sont ouverts ?
nmap scanme.nmap.org

# 2. Versions des services (LE plus utile pour trouver des failles)
nmap -sV scanme.nmap.org

# 3. Combo recon complet (versions + scripts par défaut + rapide)
nmap -sV -sC -T4 scanme.nmap.org

# 4. TOUS les ports (65535, long mais complet — par défaut nmap n'en fait que 1000)
nmap -sV -p- scanme.nmap.org

# 5. Scan d'un seul port précis
nmap -p 80,443 scanme.nmap.org

# 6. Scan d'un réseau /24 (découverte d'hôtes vivants)
nmap -sn 192.168.1.0/24      # -sn = ping scan, pas de scan de ports
```

## 🔑 Les flags à retenir

| Flag | Rôle |
|---|---|
| `-sV` | Détecte la **version** des services (Apache 2.4.7, OpenSSH 6.6…) |
| `-sC` | Lance les **scripts par défaut** (bannières, infos utiles) |
| `-T4` | Vitesse (T0 lent/discret … T5 très rapide/bruyant) |
| `-p-` | **Tous** les ports (1-65535) |
| `-p 80,443` | Ports précis |
| `-sn` | Ping scan : juste savoir qui est **vivant**, sans scanner les ports |
| `-Pn` | Ne pas pinger (utile si la cible bloque le ping) |
| `-A` | Agressif : `-sV -sC` + OS detection + traceroute |
| `-oN fichier` | Sauvegarde le résultat en texte |

## 🧠 Comment LIRE le résultat

```
PORT     STATE  SERVICE  VERSION
22/tcp   open   ssh      OpenSSH 6.6.1    ← version vieille ? → chercher une CVE
80/tcp   open   http     Apache 2.4.7     ← idem : "Apache 2.4.7 CVE"
443/tcp  open   https    nginx 1.18.0
```

**Le réflexe du hacker :**
```
service + version  →  Google / exploit-db : "<logiciel> <version> CVE"
Une version ancienne = faille connue potentielle = piste d'exploitation.
```

- `open` = port ouvert et un service écoute (intéressant)
- `closed` = port joignable mais rien n'écoute
- `filtered` = un firewall bloque (on ne sait pas)

## 🎯 Place dans le bug bounty
1. `subfinder` → liste les sous-domaines du scope
2. `httpx` → garde ceux qui répondent en HTTP/S
3. **`nmap -sV`** → quels services/versions tournent
4. CVE / nuclei → failles connues sur ces versions
5. Tests manuels (IDOR, XSS, etc.) sur les apps web trouvées

## 🐞 Astuces
- Lent sur mobile ? ajoute `-T4` et limite les ports (`-p 1-1000`).
- Cible qui « ne répond pas » alors qu'elle est en ligne → ajoute `-Pn`.
- Toujours garder une trace : `nmap -sV -oN scan.txt scanme.nmap.org`.

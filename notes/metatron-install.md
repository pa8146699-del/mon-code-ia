# 🤖 METATRON — install & lancement (Termux + Debian/Kali proot)

> Assistant de pentest IA (LLM local via Ollama) — dépôt :
> https://github.com/sooryathejas/METATRON
> Tourne en CPU sur le téléphone → **lent** mais fonctionnel avec un petit modèle.
> ⚠️ À utiliser UNIQUEMENT sur des cibles autorisées (labs, scope HackerOne, tes systèmes).

---

## 0. Prérequis (une seule fois)

```bash
cd ~ && git clone https://github.com/sooryathejas/METATRON.git
cd METATRON
apt update && apt install -y nmap whois whatweb curl dnsutils nikto python3-venv git mariadb-server
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 1. Ollama (le moteur IA) — onglet À PART

```bash
curl -fsSL https://ollama.com/install.sh | sh   # une seule fois
ollama serve                                    # laisse tourner dans son onglet
```

## 2. Modèle IA (léger pour le tél) — une seule fois

```bash
ollama pull qwen2.5:3b
sed -i 's|^FROM .*|FROM qwen2.5:3b|' ~/METATRON/Modelfile
ollama create metatron-qwen -f ~/METATRON/Modelfile
ollama list        # doit montrer metatron-qwen:latest
```

> Modèle officiel (plus lourd, 8,4 Go RAM) : `huihui_ai/qwen3.5-abliterated:9b`.

---

## 3. Base MariaDB — Metatron NE la crée PAS tout seul

### a) Démarrer le serveur (à REFAIRE à chaque réouverture du proot)
```bash
mkdir -p /run/mysqld && chown -R mysql:mysql /run/mysqld /var/lib/mysql
mariadb-install-db --user=mysql --datadir=/var/lib/mysql >/dev/null 2>&1   # 1re fois seulement
mariadbd-safe --datadir=/var/lib/mysql &
sleep 5
```

### b) Créer base + user + tables (une seule fois) — coller tout le bloc
```bash
mariadb -u root <<'SQL'
CREATE DATABASE IF NOT EXISTS metatron;
CREATE USER IF NOT EXISTS 'metatron'@'localhost' IDENTIFIED BY '123';
GRANT ALL PRIVILEGES ON metatron.* TO 'metatron'@'localhost';
FLUSH PRIVILEGES;
USE metatron;
CREATE TABLE IF NOT EXISTS history (
  sl_no INT AUTO_INCREMENT PRIMARY KEY,
  target VARCHAR(255) NOT NULL,
  scan_date DATETIME NOT NULL,
  status VARCHAR(50) DEFAULT 'active'
);
CREATE TABLE IF NOT EXISTS vulnerabilities (
  id INT AUTO_INCREMENT PRIMARY KEY,
  sl_no INT, vuln_name TEXT, severity VARCHAR(50),
  port VARCHAR(20), service VARCHAR(100), description TEXT,
  FOREIGN KEY (sl_no) REFERENCES history(sl_no)
);
CREATE TABLE IF NOT EXISTS fixes (
  id INT AUTO_INCREMENT PRIMARY KEY,
  sl_no INT, vuln_id INT, fix_text TEXT, source VARCHAR(50),
  FOREIGN KEY (sl_no) REFERENCES history(sl_no),
  FOREIGN KEY (vuln_id) REFERENCES vulnerabilities(id)
);
CREATE TABLE IF NOT EXISTS exploits_attempted (
  id INT AUTO_INCREMENT PRIMARY KEY,
  sl_no INT, exploit_name TEXT, tool_used TEXT,
  payload LONGTEXT, result TEXT, notes TEXT,
  FOREIGN KEY (sl_no) REFERENCES history(sl_no)
);
CREATE TABLE IF NOT EXISTS summary (
  id INT AUTO_INCREMENT PRIMARY KEY,
  sl_no INT, raw_scan LONGTEXT, ai_analysis LONGTEXT,
  risk_level VARCHAR(50), generated_at DATETIME,
  FOREIGN KEY (sl_no) REFERENCES history(sl_no)
);
SQL
```

### c) Vérifier
```bash
mariadb -u metatron -p123 -e "USE metatron; SHOW TABLES;"
# → history, vulnerabilities, fixes, exploits_attempted, summary
```

---

## 4. Lancer Metatron 🚀
```bash
cd ~/METATRON && source venv/bin/activate
python metatron.py
```

---

## ⚡ Routine de RELANCE (après fermeture du téléphone)
Tout est déjà installé, il suffit de :
```bash
# onglet 1
ollama serve
# onglet 2
mariadbd-safe --datadir=/var/lib/mysql &
sleep 5
cd ~/METATRON && source venv/bin/activate && python metatron.py
```

## 🐞 Pannes connues
- `ollama list` vide → le modèle n'est pas téléchargé (refaire étape 2).
- Metatron affiche son banner puis plante → MariaDB pas démarrée (étape 3a) ou base/tables absentes (3b).
- `Can't connect to local MySQL server` → relancer `mariadbd-safe --datadir=/var/lib/mysql &` puis attendre 5 s.
- `could not connect to ollama` / `Connection refused` → `ollama serve` n'est pas lancé en fond.
  Démarrer en fond : `nohup ollama serve > /tmp/ollama.log 2>&1 &` puis vérifier
  `curl -s http://localhost:11434/api/tags`.
- `bash: cd: /root/metatron` → le dossier est `METATRON` en MAJUSCULES (Linux = sensible à la casse).
- Réponses très lentes → normal en CPU sur mobile ; rester sur `qwen2.5:3b` (ou plus petit).

## 💥 OOM — Termux se ferme tout seul (mémoire)
Le modèle se charge en RAM → Android tue Termux ("out of memory"). Solutions, dans l'ordre :
1. **Modèle plus petit** (le plus efficace) : `qwen2.5:1.5b`, puis `qwen2.5:0.5b` si ça coupe encore.
   ```bash
   ollama pull qwen2.5:0.5b
   sed -i 's|^FROM .*|FROM qwen2.5:0.5b|' ~/METATRON/Modelfile
   ollama create metatron-qwen -f ~/METATRON/Modelfile
   ```
2. **Tester le modèle SEUL** avant Metatron : `ollama run metatron-qwen "dis bonjour"`.
   S'il répond sans tuer Termux → le modèle tient.
3. Fermer toutes les autres applis ; `termux-wake-lock` ; désactiver l'optim. batterie de Termux.
> Bilan : le `0.5b` TIENT sur le tél (stack complète recon→IA→MariaDB validée ✅).

## ⚠️ LEÇON EN OR — une IA de pentest HALLUCINE, on vérifie TOUJOURS
Un scanner IA = un **assistant**, jamais une preuve. Le `0.5b` (et même les gros modèles)
produit des résultats faux qu'il faut confirmer à la main. Exemples RÉELS vus sur ce tél :

- **Contradiction** : `Severity: HIGH` ET « not vulnerable to a known exploit » dans la même
  ligne. Une vraie faille n'est jamais les deux.
- **Fix bidon** : « if the service requires HTTP/2 support, update it with `curl --version` »
  → `curl --version` affiche juste la version de curl, ça n'ajoute aucun support à rien.
- **Hallucination pure** : cible = `127.0.0.1`, mais l'IA suggère `nmap -sV 192.168.1.1`
  → une IP qui n'a JAMAIS existé dans le scan, inventée de zéro.

```
RÈGLE : ne JAMAIS soumettre une "faille" sortie d'une IA sans l'avoir confirmée soi-même.
Reporter une hallucination sur HackerOne = rapport rejeté + réputation grillée.
La valeur d'un hacker = savoir trier le vrai du faux. L'IA va vite, mais se trompe.
```

> Metatron sur mobile = belle démo technique. Pour de l'analyse IA vraiment utile :
> le lancer sur PC avec le modèle `9b`. Sur le tél, le contenu IA reste à ne pas prendre au sérieux.

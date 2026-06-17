# MonAppli

Ta boîte à outils **cybersécurité** perso : une interface tactile (Kivy) qui
réunit tous les outils de [DataGuard](../dataguard/) pour vérifier un texte,
un e-mail, du code ou un mot de passe directement depuis ton téléphone.

Six actions :

- **🔍 Scanner les secrets** — détecte clés API, mots de passe, IBAN, cartes
  bancaires, e-mails… (logique de `dataguard/detectors.py`).
- **🎣 Analyser phishing** — évalue le risque d'hameçonnage d'un message
  (logique de `dataguard/phishing.py`).
- **✅ Tout analyser** — lance secrets + phishing d'un coup.
- **🔑 Force d'un mot de passe** — score, entropie et conseils
  (logique de `dataguard/toolkit.py`).
- **🎲 Générer un mot de passe** — mot de passe aléatoire sûr (module `secrets`).
- **#️⃣ Empreintes (hash)** — SHA-256, SHA-1, MD5 du texte collé.

## Réutilisation de DataGuard (source unique)

`main.py` importe `detectors`, `phishing` et `toolkit` par leur nom simple. Ces
fichiers **vivent dans `dataguard/`** et sont **copiés ici au moment du build**
(par `.github/workflows/build-monappli.yml`). Ils sont volontairement
git-ignorés sous `monappli/` : la source unique reste `dataguard/`, ce qui
évite que deux copies divergent.

## Tester l'interface sur ordinateur

```bash
pip install kivy
cp ../dataguard/detectors.py ../dataguard/phishing.py ../dataguard/toolkit.py .
python main.py
```

## Construire l'APK Android

Les APK sont construits **dans le cloud** (GitHub Actions), car Buildozer a
besoin du SDK/NDK Android :

1. Onglet **Actions** du dépôt GitHub → workflow **Build APK MonAppli**.
2. Bouton **Run workflow** (déclenchement manuel `workflow_dispatch`).
3. Une fois terminé, télécharge l'artéfact **`monappli-apk`**.

Le build se déclenche aussi automatiquement à chaque push sur `main` touchant
`monappli/**` ou le fichier de workflow.

Config Android : voir `buildozer.spec` (`requirements = python3,kivy`, API 34,
minapi 24, arm64-v8a + armeabi-v7a).

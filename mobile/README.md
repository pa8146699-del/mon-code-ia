# DataGuard Mobile (application Android)

Interface tactile de DataGuard construite avec **Kivy**, compilée en **APK**
Android automatiquement par GitHub (aucun PC nécessaire).

L'app réutilise la logique de `dataguard/detectors.py` (détection de secrets)
et `dataguard/phishing.py` (anti-phishing). Ces deux fichiers sont copiés ici
automatiquement au moment du build par le workflow GitHub Actions.

## Obtenir l'APK (build dans le cloud)

1. Sur GitHub, va dans l'onglet **Actions**.
2. Choisis le workflow **« Build APK DataGuard »**.
3. Clique sur **« Run workflow »** et attends la fin (~20-40 min la 1ʳᵉ fois).
4. En bas de la page du build, télécharge l'artéfact **`dataguard-apk`**.
5. Décompresse le `.zip`, transfère le `.apk` sur ton téléphone.
6. Installe-le (autorise « sources inconnues » si Android le demande).

## Tester l'interface sur ordinateur (optionnel)

```bash
pip install kivy
cd mobile
cp ../dataguard/detectors.py ../dataguard/phishing.py .
python main.py
```

## Fonctionnalités de l'app

- **🔍 Scanner les secrets** — colle du texte/code, l'app surligne les fuites.
- **🎣 Analyser phishing** — colle un e-mail/SMS, l'app donne un score de risque.

> Note : la version mobile travaille sur du **texte collé** (pratique au doigt).
> Pour scanner des dossiers entiers, utilise la version terminal `dataguard.py`.

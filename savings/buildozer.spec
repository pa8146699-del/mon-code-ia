[app]

# Nom affiché de l'application
title = Épargne 1M

# Nom du paquet
package.name = epargne1m
package.domain = org.moncodeia

# Sources : ce dossier (main.py + savings.db créé à la première exécution)
source.dir = .
source.include_exts = py,png,jpg,kv,atlas

# Version de l'application
version = 1.0

# Dépendances Python embarquées dans l'APK (stdlib sqlite3 est inclus dans python3)
requirements = python3,kivy

# Orientation portrait uniquement
orientation = portrait

# Pas de plein écran
fullscreen = 0

# Cibles Android
android.api = 34
android.minapi = 24
android.archs = arm64-v8a, armeabi-v7a

# Permissions
android.permissions = WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE

# Accepter automatiquement les licences du SDK Android (indispensable en CI)
android.accept_sdk_license = True

# Autoriser la sauvegarde pour préserver les données entre mises à jour
android.allow_backup = 1

[buildozer]

# Niveau de logs (2 = verbeux, utile pour diagnostiquer un build)
log_level = 2
warn_on_root = 1

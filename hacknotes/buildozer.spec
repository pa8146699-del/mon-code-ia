[app]

# Nom affiché de l'application
title = HackNotes

# Nom du paquet
package.name = hacknotes
package.domain = org.moncodeia

# Sources : ce dossier (main.py seul — appli 100% autonome, rien à copier)
source.dir = .
source.include_exts = py,png,jpg,kv,atlas

# Version de l'application
version = 1.0

# Dépendances Python embarquées dans l'APK (stdlib only + kivy)
requirements = python3,kivy

# Pas de permission spéciale : les notes sont stockées dans le dossier privé
# de l'app (App.user_data_dir), pas besoin d'accès réseau ni stockage externe.
android.permissions =

# Orientation
orientation = portrait

# Pas de plein écran
fullscreen = 0

# Cibles Android
android.api = 34
android.minapi = 24
android.archs = arm64-v8a, armeabi-v7a

# Accepter automatiquement les licences du SDK Android (indispensable en CI)
android.accept_sdk_license = True

# Autoriser la sauvegarde
android.allow_backup = 1

[buildozer]

# Niveau de logs (2 = verbeux, utile pour diagnostiquer un build)
log_level = 2
warn_on_root = 1

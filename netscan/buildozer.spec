[app]

# Nom affiché de l'application
title = NetScan

# Nom du paquet
package.name = netscan
package.domain = org.moncodeia

# Sources : ce dossier (main.py seul — appli 100% autonome, rien à copier)
source.dir = .
source.include_exts = py,png,jpg,kv,atlas

# Version de l'application
version = 1.0

# Dépendances Python embarquées dans l'APK (stdlib only + kivy)
requirements = python3,kivy

# Permissions réseau : INTERNET pour les sockets, ACCESS_*_STATE pour détecter
# l'IP locale et donc deviner le réseau /24 à scanner.
android.permissions = INTERNET, ACCESS_NETWORK_STATE, ACCESS_WIFI_STATE

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

# AgentMobile

AgentOS sur ton **téléphone** : une app Kivy (Android) où Claude **agit** sur
une base SQLite locale (clients, projets, tâches, finances, notes) — ta source
unique de vérité, stockée sur l'appareil.

**100 % gratuit**, sans aucun service tiers payant (ni Notion, ni Make, ni
Zapier). Seul l'usage de l'API Claude se paie au token (pas d'abonnement) :
tu saisis ta clé dans l'app.

## Comment ça marche

Réutilise les modules de `agentos/` (copiés au build, jamais versionnés ici) :

| Module | Rôle |
|---|---|
| `db.py` | Base SQLite locale (source de vérité). |
| `tools.py` | Outils que Claude appelle pour lire/écrire. |
| `llm.py` | Appel API Claude via `urllib` (pas de SDK lourd → APK léger). |
| `notion_sync.py` | Synchro Notion optionnelle (désactivée par défaut). |

L'interface : un champ pour ta clé API, une zone de conversation, un champ de
message. Tu écris en langage naturel ; l'agent enregistre/consulte la base.

## Build de l'APK (gratuit, dans le cloud)

Le workflow `Build APK AgentMobile` (GitHub Actions) construit l'APK :
- soit manuellement (onglet **Actions** → *Run workflow*),
- soit automatiquement sur push vers `main` touchant `agentmobile/**`.

Il copie `agentos/{db,tools,notion_sync,llm}.py` dans `agentmobile/`, lance
`buildozer android debug`, et publie l'APK dans l'artéfact `agentmobile-apk`.
Télécharge-le et installe-le sur ton téléphone.

## Tester sur ordinateur

```bash
pip install kivy
cd agentmobile
cp ../agentos/db.py ../agentos/tools.py ../agentos/notion_sync.py ../agentos/llm.py .
export ANTHROPIC_API_KEY=ta-clé   # pré-remplit le champ (optionnel)
python main.py
```

## Notes

- La base vit dans le dossier privé de l'app (`user_data_dir`), inscriptible
  sur Android. Elle n'est pas synchronisée entre appareils par défaut.
- La permission `INTERNET` est requise (appel à l'API Claude).
- Pour un miroir consultable ailleurs, tu peux activer la synchro Notion via les
  variables `NOTION_*` (voir `agentos/notion_sync.py`) — optionnel.

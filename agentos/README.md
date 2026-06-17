# AgentOS

Un « Agent OS » personnel : une base de données centrale (ta **source unique de
vérité**) sur laquelle un agent IA **travaille vraiment** — il lit, écrit et met
à jour tes données au lieu de simplement discuter.

Contrairement à `jarvis/` (qui ne fait que converser), AgentOS utilise le
**tool use** de Claude : l'IA appelle de vrais outils qui modifient une base
SQLite couvrant cinq domaines — **clients, projets, tâches, finances, notes**.

## Idée

```
        Toi (texte ou voix)
              │
        ┌─────▼─────┐      tool use      ┌──────────────┐
        │  Claude   │ ───────────────▶   │  Outils CRUD │
        │ (agent.py)│ ◀───────────────   │  (tools.py)  │
        └───────────┘     résultats      └──────┬───────┘
                                                │
                                   ┌────────────▼───────────┐
                                   │  SQLite (db.py)         │  ← source de vérité
                                   │  agentos.db             │
                                   └────────────┬───────────┘
                                                │ best-effort
                                   ┌────────────▼───────────┐
                                   │  Notion (notion_sync)   │  ← miroir mobile
                                   └─────────────────────────┘
```

L'interface (toi) sert à **piloter** ; l'IA utilise les données pour **exécuter**.

## Lancer

```bash
pip install -r agentos/requirements.txt
export ANTHROPIC_API_KEY=ta-clé

python agentos/agent.py            # mode texte
python agentos/agent.py --voice    # mode vocal (micro + synthèse)
```

Exemples de phrases :

- « J'ai un nouveau prospect : Dupont SARL, contact@dupont.fr »
- « Note une dépense de 42 € en catégorie repas »
- « Crée une tâche : envoyer le devis à Dupont »
- « Quel est mon solde ce mois-ci ? »
- « Retrouve mes notes sur le budget marketing »

## Modules

| Fichier | Rôle |
|---|---|
| `db.py` | Schéma + CRUD SQLite (5 domaines). Zéro dépendance. La source de vérité. |
| `tools.py` | Définitions d'outils pour Claude + `dispatch()` (exécute + synchro Notion). |
| `agent.py` | Boucle d'agent style Jarvis (texte / `--voice`) avec tool use. |
| `notion_sync.py` | Synchro best-effort vers Notion (stdlib `urllib`). |
| `test_agentos.py` | Tests (base + dispatch), sans appel API. |

## Synchro Notion (optionnelle — la partie « hybride »)

La base SQLite reste la vérité ; Notion est un miroir consultable sur mobile.
Tout est désactivé tant que tu ne configures rien (`sync_row` devient un no-op).

1. Crée une intégration interne sur https://www.notion.so/my-integrations et
   récupère le jeton `secret_…`.
2. Crée tes bases Notion (Clients, Projets, Tâches, Finances, Notes) et partage
   chacune avec l'intégration. Note l'id de chaque base (dans son URL).
3. Exporte les variables d'environnement :

```bash
export NOTION_TOKEN=secret_xxx
export NOTION_DB_CLIENTS=...     # id de la base Clients
export NOTION_DB_PROJETS=...
export NOTION_DB_TACHES=...
export NOTION_DB_FINANCES=...
export NOTION_DB_NOTES=...
# export NOTION_TITLE_PROP="Nom"   # si ta propriété titre ne s'appelle pas "Name"
```

Chaque écriture crée une page Notion : titre = nom/titre/description de la
ligne, et le détail complet (JSON) dans le corps de la page — donc aucune
contrainte de schéma à respecter côté Notion.

## Tests

```bash
python -m pytest agentos/                  # si pytest est installé
cd agentos && python test_agentos.py       # runner zéro-dépendance
```

## Étendre

Ajouter un outil = une fonction dans `db.py`, une entrée dans `TOOLS` et une
branche dans `_HANDLERS` (`tools.py`). Pour synchroniser un nouvel `add_*` vers
Notion, ajoute-le à `_SYNC_TABLE` et `_DB_ENV`.

## Et sur le portable ?

Deux options pour l'usage mobile :

- **Notion** comme miroir consultable (ci-dessus) — le plus simple aujourd'hui.
- Une **app Kivy** dédiée (sur le modèle de `monappli/`) qui parle à la base ou
  à l'agent — étape suivante possible si tu veux une vraie interface tactile.

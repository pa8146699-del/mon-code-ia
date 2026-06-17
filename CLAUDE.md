# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`mon-code-ia` is a personal Python toolkit with these components:

- `jarvis/` — a vocal/text assistant powered by the Claude API (chat only).
- `agentos/` — an "Agent OS": an LLM agent that uses **tool use** to read/write a central SQLite database (the single source of truth) across five domains, with optional Notion mirroring. Stdlib-only (the API call goes through `urllib`, not an SDK); multi-provider — **free default (Gemini)**, plus Groq (free) and Claude (paid).
- `agentmobile/` — a Kivy GUI (Android) front-end for AgentOS: a chat that drives the agent against a local SQLite DB on the phone. Reuses `agentos/`'s modules; its own APK build.
- `dataguard/` — a command-line data-leak / phishing security toolkit (no external dependencies).
- `mobile/` — a Kivy GUI wrapper around DataGuard, built into an Android APK by GitHub Actions.
- `monappli/` — a second, personal Kivy security app reusing DataGuard, with its own combined "Tout analyser" action and its own APK build.

`jarvis/`, `agentos/`, and `dataguard/` share no code with each other. Reuse-via-copy (single source of truth stays in the origin folder, copies are git-ignored & created at build time):
- `mobile/` reuses `dataguard/detectors.py` + `dataguard/phishing.py`.
- `monappli/` reuses those two plus `dataguard/toolkit.py`.
- `agentmobile/` reuses `agentos/db.py`, `tools.py`, `notion_sync.py`, `llm.py`.

## Repository Layout

```
mon-code-ia/
├── .github/workflows/
│   ├── build-apk.yml                 # CI: mobile/ Android APK builder
│   ├── build-monappli.yml            # CI: monappli/ Android APK builder
│   └── build-agentmobile.yml         # CI: agentmobile/ Android APK builder
├── .gitignore
├── CLAUDE.md
├── README.md
├── jarvis/
│   ├── jarvis.py                     # Single-file assistant (~100 lines)
│   └── requirements.txt
├── agentos/
│   ├── db.py                         # SQLite schema + CRUD (single source of truth)
│   ├── tools.py                      # Claude tool-use definitions + dispatch()
│   ├── llm.py                        # Claude API client + agent loop (stdlib urllib)
│   ├── agent.py                      # Jarvis-style terminal/voice front-end
│   ├── notion_sync.py                # Best-effort Notion mirror (stdlib urllib)
│   ├── test_agentos.py               # Tests (db + dispatch, no API calls)
│   ├── requirements.txt
│   └── README.md
├── dataguard/
│   ├── dataguard.py                  # Argparse dispatcher (cmd_* functions)
│   ├── detectors.py                  # Secret-detection engine + Luhn + redact
│   ├── phishing.py                   # Heuristic phishing scorer
│   ├── toolkit.py                    # Password strength/gen + hashing (stdlib)
│   ├── report.py                     # HTML report generator
│   ├── test_dataguard.py             # Test suite (pytest + zero-dep runner)
│   └── README.md
├── mobile/
│   ├── main.py                       # Kivy GUI (touch-friendly)
│   ├── buildozer.spec                # Android build config
│   └── README.md
├── monappli/
│   ├── main.py                       # Personal Kivy GUI (adds "Tout analyser")
│   ├── buildozer.spec                # Android build config
│   └── README.md
└── agentmobile/
    ├── main.py                       # Kivy chat GUI driving the AgentOS agent
    ├── buildozer.spec                # Android build config
    └── README.md
```

Files git-ignored under `mobile/`: `detectors.py`, `phishing.py`, `bin/`, `.buildozer/`, `*.apk`. Under `monappli/`: same plus `toolkit.py`. Under `agentmobile/`: `db.py`, `tools.py`, `notion_sync.py`, `llm.py`, `*.db`, `bin/`, `.buildozer/`.

## Setup

```bash
pip install -r jarvis/requirements.txt
export ANTHROPIC_API_KEY=your-key-here
```

## Running Jarvis

```bash
python jarvis/jarvis.py          # text mode (terminal only)
python jarvis/jarvis.py --voice  # voice mode (microphone + speech synthesis)
```

## Jarvis Architecture

`jarvis/jarvis.py` is a single-file application (~100 lines). Key design points:

- **Voice dependency loading** is conditional at module level (not lazy): if `--voice` is in `sys.argv`, `pyttsx3` and `speech_recognition` are imported immediately on startup. A missing voice dependency crashes at import time, not at first use.
- **Conversation state** (`_history: list[dict]`) is a module-level global. It accumulates the full turn-by-turn exchange and is passed to every Claude API call, giving multi-turn context. Lost when the process exits.
- **Model and limits**: hardcoded to `claude-sonnet-4-6` with `max_tokens=1024`.
- **Language**: the system prompt instructs Claude to reply in French by default, switching to the user's language if they write in another one.
- **Exit keywords**: `"quitter"`, `"stop"`, `"exit"`, `"quit"` (checked case-insensitively) terminate the loop.
- `ANTHROPIC_API_KEY` is read via `os.environ["ANTHROPIC_API_KEY"]` — raises `KeyError` if unset.

## AgentOS Architecture

`agentos/` is an "Agent OS": unlike `jarvis/` (chat only), the agent uses
Claude **tool use** to actually read and write a central database — the single
source of truth — across five domains: **clients, projets, taches, finances,
notes**. Run it like Jarvis:

```bash
# Text mode needs NO pip install (pure stdlib). --voice needs the voice deps:
pip install -r agentos/requirements.txt   # only for --voice
export GEMINI_API_KEY=your-free-gemini-key  # default provider (free). Others:
# AGENTOS_PROVIDER=groq + GROQ_API_KEY  (free)  |  AGENTOS_PROVIDER=anthropic + ANTHROPIC_API_KEY (paid)
python agentos/agent.py            # text mode
python agentos/agent.py --voice    # voice mode (micro + speech)
```

Flat module layout (imported by bare name, `agentos/` is on `sys.path[0]` when run directly):

- `db.py` — **SQLite, stdlib only** (`sqlite3`). The source of truth. Schema in `SCHEMA`; `connect(path)` creates the file + schema (path from `AGENTOS_DB` env, default `agentos/agentos.db`). Tables: `clients`, `projets`, `taches`, `finances`, `notes`. Every write function (`add_*`, `update_*`) returns the created/modified row as a JSON-serializable dict. `finance_summary()` returns revenus/dépenses/solde + dépenses par catégorie.
- `tools.py` — `TOOLS` is the list of tool definitions sent to the Claude API. `dispatch(conn, name, args)` runs the requested tool against the DB via `_HANDLERS`, fires a best-effort Notion sync for write tools (`_SYNC_TABLE`), and returns a JSON string. **All tool errors are caught and returned as `{"erreur": ...}`** so a bad call surfaces to Claude instead of crashing the loop. Add a tool = a `db.py` function + a `TOOLS` entry + a `_HANDLERS` branch (+ `_SYNC_TABLE`/`_DB_ENV` for Notion).
- `llm.py` — **the shared agent loop, stdlib only** (urllib, no SDK — keeps the APK light and the package dependency-free). **Multi-provider**, selected by `AGENTOS_PROVIDER` (`_RUNNERS` dict), default `"gemini"`:
  - `_run_gemini` — Google Gemini `generateContent` (default, free). `_gemini_tools()` maps `TOOLS` to `function_declarations` (omitting `parameters` when properties are empty — Gemini rejects empty param objects). Roles are only `user`/`model`; model `functionCall` parts are answered with a `user` turn of `functionResponse` parts (response coerced to an object). Model from `GEMINI_MODEL` (default `gemini-2.0-flash`); key header `x-goog-api-key`.
  - `_run_openai` — Groq (OpenAI-compatible chat-completions + tool calling, free). `_openai_tools()` converts `TOOLS` to `{"type":"function","function":{…}}`; loops while `message.tool_calls` is present; tool results are `{"role":"tool","tool_call_id",…}`. Model from `GROQ_MODEL` (default `llama-3.3-70b-versatile`).
  - `_run_anthropic` — Claude Messages API (paid). Loops on `stop_reason == "tool_use"`, feeds `tool_result` blocks back. Model `claude-fable-5`.
  - **The message `history` format is provider-specific** (Gemini uses `parts`; the others use `content`) — keep one provider per session/history. `run_turn(conn, history, user_message, api_key=None, on_tool=None)` appends the provider-appropriate user turn, picks the runner, mutates `history` in place, returns the final text. API/network errors are returned as a string, not raised. Key comes from `api_key` or the per-provider env var (`_KEY_VAR`: `GEMINI_API_KEY` / `GROQ_API_KEY` / `ANTHROPIC_API_KEY`). **Both `agent.py` and `agentmobile/` call this** — the one place the agent logic lives.
- `agent.py` — thin terminal/voice front-end, **same conventions as `jarvis/jarvis.py`** (module-level `VOICE_MODE`, conditional voice imports, `_history` global, same exit keywords). It delegates the actual turn to `llm.run_turn`, passing an `on_tool` callback that prints each tool call.
- `notion_sync.py` — the **hybrid** layer. `sync_row(table, row)` mirrors a row to Notion via stdlib `urllib` (no SDK). **Best-effort and never raises**: a no-op returning `False` if `NOTION_TOKEN` or the per-table `NOTION_DB_*` env var is missing; network/API errors are caught and logged. The row's title field becomes the page title; full JSON goes in a code block in the page body (so no Notion schema constraints apply). SQLite stays the source of truth; Notion is just a mobile-readable mirror.

Notion config (all optional env vars): `NOTION_TOKEN`, `NOTION_DB_{CLIENTS,PROJETS,TACHES,FINANCES,NOTES}`, `NOTION_TITLE_PROP` (default `"Name"`).

### AgentOS tests

```bash
python -m pytest agentos/                 # if pytest is installed
cd agentos && python test_agentos.py      # zero-dependency fallback runner
```

11 tests covering DB CRUD round-trips, status filtering, project/task linkage, `finance_summary`, note search, and tool `dispatch` (including unknown-tool and error-propagation paths). **No test calls the Claude API or Notion** — they exercise `db` and `tools.dispatch` directly against a `tmp_path` SQLite file. Same zero-dep runner pattern as `dataguard/test_dataguard.py` (`tmp_path` via `tempfile.TemporaryDirectory`).

The local DB (`agentos/*.db`) is git-ignored.

## DataGuard

`dataguard/` is a self-contained security toolkit (Python 3 standard library only) exposed through subcommands on `dataguard.py`:

```bash
python dataguard/dataguard.py                              # interactive menu (default with no args)
python dataguard/dataguard.py menu                         # same, explicit
python dataguard/dataguard.py scan <file-or-dir> [--json|--html FILE] [--strict]
python dataguard/dataguard.py phishing [--text STR | --file PATH] [--json] [--strict]
python dataguard/dataguard.py install-hook [--force]
python dataguard/dataguard.py scan-staged [--strict]       # used by the git hook
```

`phishing` also reads from stdin when neither `--text` nor `--file` is given:
```bash
cat mail.txt | python dataguard/dataguard.py phishing
```

Module layout (all flat, imported by simple name since `dataguard/` is on `sys.path[0]` when run directly):

- `dataguard.py` — argparse subcommand dispatch (`cmd_*` functions). Each subcommand sets `func` via `set_defaults`. Interactive menu is `cmd_menu` (options 1–4).
- `detectors.py` — the `DETECTORS` list and scanning logic (`scan`, `scan_file`, `scan_line`, `sort_findings`). Extend coverage by adding a `Detector(name, compiled_regex, severity)` entry. Credit-card hits are confirmed with the **Luhn checksum** (`luhn_valid`); all reported values are **redacted** (`redact`: first 4 chars + `***` + last 2 chars).
- `phishing.py` — heuristic phishing scorer. `analyze(text)` returns `(score 0-100, [PhishingSignal])`; lookalike-domain detection normalizes digit-for-letter swaps (`paypa1` → `paypal`) and skips legitimate `brand.tld` hosts.
- `toolkit.py` — extra stdlib-only security utilities (no detection): `password_strength(pw)` → `PasswordReport(score, level, entropy_bits, issues, tips)`; `generate_password(length, use_symbols)` using the `secrets` module (guarantees one char per required class, shuffles with `secrets.randbelow`); `hash_text(text)` → `{SHA-256, SHA-1, MD5}` hexdigests. Consumed by `monappli/`.
- `report.py` — standalone HTML report (`build_html`); never embeds raw secrets.

### What `scan` detects

| Type | Severity |
|---|---|
| Private key (RSA, EC, OpenSSH…) | HIGH |
| AWS access key | HIGH |
| API keys: Anthropic, OpenAI, Google, Stripe, SendGrid | HIGH |
| GitHub token, Slack token, Google OAuth token | HIGH |
| Plaintext password | HIGH |
| IBAN | HIGH |
| Credit card number (Luhn-validated) | HIGH |
| JWT token, Slack webhook, generic secret/api_key/token | MEDIUM |
| Email address, FR phone number, IPv4 address | LOW |

Binary files (`.png`, `.jpg`, `.pdf`, `.pyc`, `.zip`, `.mp4`, `.ttf`, `.so`, etc.) and directories (`.git`, `__pycache__`, `node_modules`, `venv`, `.venv`, `.mypy_cache`) are skipped during directory scans.

### Phishing scoring signals

`analyze(text)` sums weighted signals (capped at 100):

| Signal | Weight |
|---|---|
| Urgency language ("urgent", "immédiatement", "expire", "suspendu"…) | 10 |
| Credentials demand ("password", "code pin", "numéro de carte"…) | 15 |
| Generic greeting ("cher client", "dear customer") | 5 |
| HTTP link (not HTTPS) | 8 |
| Punycode domain (xn--) | 20 |
| IP-based link | 20 |
| URL shortener (bit.ly, tinyurl…) | 12 |
| Suspicious TLD (.xyz, .top, .tk, .ml, .ga, .cf, .gq, .zip, .mov) | 12 |
| Excessive subdomains (4+ dots) | 8 |
| Lookalike domain (paypa1.com → paypal) | 25 |
| Dangerous attachment (.exe, .scr, .zip, .rar, .js, .vbs, .bat, .cmd, .iso, .docm, .xlsm) | 15 |

`risk_level(score)` → `"AUCUN"` (0) / `"FAIBLE"` (1–29) / `"MOYEN"` (30–59) / `"ÉLEVÉ"` (60+).

`--strict` exits with code 1 if score reaches MOYEN or higher.

### Git pre-commit hook

`scan-staged` + `install-hook` implement a pre-commit guard: the hook calls `scan-staged --strict` to block commits whose staged files contain secrets. The hook is written to `$(git rev-parse --git-dir)/hooks/pre-commit`. **Do not run `install-hook` from inside this repo's working tree** — it would install a pre-commit hook into `mon-code-ia/.git` and block your own commits; test it in a throwaway repo instead.

### Tests

```bash
python -m pytest dataguard/                      # if pytest is installed
cd dataguard && python test_dataguard.py         # zero-dependency fallback runner
```

`test_dataguard.py` includes 22 tests: detector coverage (password, AWS key, Stripe key, Google API key, IBAN, email, valid/invalid credit card, clean text), redaction correctness, file scan, phishing scenarios (clean text, urgency+credentials, lookalike domain, IP link, legitimate domain not flagged), toolkit coverage (common-password rejection, strong password, empty password, password generation, hashing), and HTML report correctness. The fallback runner auto-discovers `test_*` functions and supports a `tmp_path` fixture via `tempfile.TemporaryDirectory`.

## Mobile App (`mobile/`)

`mobile/main.py` is a Kivy GUI exposing DataGuard's two text-based features (secret scan + phishing analysis) for touch use. It imports `detectors` and `phishing` by bare name; those files live in `dataguard/` and are **copied into `mobile/` at build time** by `.github/workflows/build-apk.yml` (they are git-ignored under `mobile/` to avoid drift — the single source of truth stays in `dataguard/`).

UI layout (`DataGuardLayout(BoxLayout)`):
1. Title label — "🛡️ DataGuard"
2. Instruction label
3. Multi-line `TextInput` (paste area, 40% screen height)
4. Two buttons side-by-side: "🔍 Scanner les secrets" (blue) and "🎣 Analyser phishing" (orange)
5. `ScrollView` + result `Label` (height binds to `texture_size[1]`, auto-expands; uses Kivy markup for colour coding)

`scan_text()` calls `detectors.scan_line()` per line and colour-codes results with Kivy markup (green = clean, red = HIGH, orange = MEDIUM, blue = LOW). `analyze_phishing()` calls `phishing.analyze()` and colour-codes by risk level.

Build:
- The `Build APK DataGuard` GitHub Actions workflow triggers on **manual `workflow_dispatch`** or **push to `main` touching `mobile/**` or the workflow file itself**.
- Runner: `ubuntu-latest` with `ghcr.io/kivy/buildozer:latest` container (includes Android SDK/NDK).
- Steps: checkout → git safe.directory → copy `detectors.py` + `phishing.py` into `mobile/` → `buildozer android debug` → upload `.apk` as `dataguard-apk` artifact.
- **APKs are built in CI, not locally** (Buildozer requires the Android SDK/NDK).
- Config lives in `mobile/buildozer.spec` (`requirements = python3,kivy`, targets API 34, minapi 24, both arm64-v8a and armeabi-v7a).
- Local UI test: `pip install kivy`, copy the two modules in, then `python mobile/main.py`.

## MonAppli (`monappli/`)

`monappli/main.py` is a personal, full **cybersecurity toolbox** — a Kivy app
that exposes everything DataGuard can do for touch use. It follows the same
conventions as `mobile/` (imports the security modules by bare name; they are
copied in at build time and git-ignored) but reuses **three** modules —
`detectors`, `phishing`, and `toolkit` — instead of two, and is wider in scope.

Six tools, laid out in a 2-column `GridLayout`, all operating on the single
shared `TextInput`:

| Button | Handler | Backed by |
|---|---|---|
| 🔍 Secrets | `scan_text()` | `detectors` |
| 🎣 Phishing | `analyze_phishing()` | `phishing` |
| ✅ Tout analyser | `analyze_all()` (concatenates both) | `detectors` + `phishing` |
| 🔑 Force mot de passe | `check_password()` | `toolkit.password_strength` |
| 🎲 Générer mot de passe | `make_password()` | `toolkit.generate_password` |
| #️⃣ Empreintes (hash) | `hash_report()` | `toolkit.hash_text` |

Conventions specific to `monappli/`:

- Report colours live in module-level `SEVERITY_COLORS` / `RISK_COLORS` /
  `PASSWORD_COLORS` dicts (not inline as in `mobile/main.py`).
- `_esc()` escapes Kivy markup metacharacters (`[`, `]`, `&`) before any
  user-supplied or generated string (e.g. generated passwords, redacted
  excerpts) is rendered with `markup=True`. **Always escape dynamic text shown
  in a markup Label** — generated passwords routinely contain `[`/`]`/`&`.

Build/test mirrors `mobile/`: the `Build APK MonAppli` workflow triggers on
`workflow_dispatch` or pushes to `main` touching `monappli/**` (or its workflow
file), and copies `dataguard/{detectors,phishing,toolkit}.py` in. Local UI test:
`pip install kivy`, copy the three modules in, then `python monappli/main.py`.

When adding further reuse apps, follow this same template: a new folder, a
`buildozer.spec` with a unique `package.name`, a matching workflow that copies
the needed origin `*.py` modules in, and matching `.gitignore` entries.

## AgentMobile (`agentmobile/`)

`agentmobile/main.py` is the **Android front-end for AgentOS**: a Kivy chat UI
that drives the agent against a **local SQLite DB on the phone**. It follows the
`mobile/`/`monappli/` template but reuses **AgentOS** modules (copied at build
time, git-ignored): `agentos/{db,tools,notion_sync,llm}.py`.

Key points specific to `agentmobile/`:

- **Fully free by default** — the default provider is **Gemini** (free key, no card);
  Groq is also free. No paid third-party service. The key field's hint/env-var adapt
  to `llm.PROVIDER` (`GEMINI_API_KEY` / `GROQ_API_KEY` / `ANTHROPIC_API_KEY`);
  pre-filled from env for desktop tests.
- **Calls the model via `llm.run_turn`** (urllib, no SDK), so `requirements` stays
  `python3,kivy` — the APK builds without bundling any HTTP/LLM SDK.
- **DB path is `App.user_data_dir`** (writable on Android), passed to
  `db.connect(...)` — not the repo-relative default.
- **Network call runs on a background `threading.Thread`**; UI updates marshalled
  back via `Clock.schedule_once`. The `on_tool` callback shows each tool fired.
- `_esc()` escapes Kivy markup metacharacters before rendering replies.
- `buildozer.spec` adds `android.permissions = INTERNET`.

Build/test mirrors the others: the `Build APK AgentMobile` workflow triggers on
`workflow_dispatch` or pushes to `main` touching `agentmobile/**` (or its
workflow file), and copies `agentos/{db,tools,notion_sync,llm}.py` in. Local UI
test: `pip install kivy`, copy the four modules in, then `python agentmobile/main.py`.

## Dependencies

| Package | Required for |
|---|---|
| `anthropic>=0.40.0` | Claude API client — required by `jarvis/` only |
| `SpeechRecognition>=3.10.0` | Microphone → text (`--voice` only) |
| `pyttsx3>=2.90` | Text → speech, offline (`--voice` only) |
| `PyAudio>=0.2.14` | Audio I/O backend for SpeechRecognition (`--voice` only) |
| `kivy` | `mobile/`, `monappli/`, `agentmobile/` GUIs (provided by the Buildozer CI image; `pip install kivy` for local UI tests) |

`agentos/` has **zero external dependencies** in text mode — it calls the Claude
API through `urllib` (`llm.py`) and stores data in `sqlite3`; only `--voice` adds
the voice packages. `dataguard/` has **zero external dependencies** (pure Python 3
stdlib: `re`, `pathlib`, `subprocess`, `argparse`, `json`, `dataclasses`, `html`,
`datetime`, `stat`, plus `hashlib`, `secrets`, `math`, `string` for `toolkit.py`).

## Key Architectural Decisions

- **Modular separation + reuse-via-copy**: components are independent; the Kivy apps reuse a core folder by copying its modules at build time (not importing), keeping the core the single source of truth — `mobile/`+`monappli/` from `dataguard/`, `agentmobile/` from `agentos/`.
- **SDK-free, multi-provider agent**: `agentos/llm.py` talks to the LLM HTTP APIs via `urllib` instead of any SDK. This keeps the package stdlib-only and lets `agentmobile/` build an APK with just `python3,kivy`. It supports **free Gemini (default) and Groq**, plus an optional paid Claude path, switched by `AGENTOS_PROVIDER`. `jarvis/` still uses the `anthropic` SDK.
- **Conditional voice loading**: jarvis imports audio libs only when `--voice` is present, avoiding dependency failures for text-only mode.
- **Luhn validation**: credit card regex matches are verified by the Luhn checksum to suppress false positives.
- **Redaction-first**: secrets are masked (`a***34`) before any display or logging; raw values never appear in output.
- **CI-only APK builds**: Buildozer requires Android SDK/NDK; the GitHub Actions container provides both; local builds are not supported.
- **No persistent state in jarvis**: `_history` lives only in memory for the process lifetime; there is no database or file backing. (AgentOS, by contrast, persists everything to SQLite.)
- **AgentOS acts, it doesn't just chat**: where jarvis only converses, agentos gives Claude tools that mutate a SQLite DB — the "single source of truth". The UI is for humans to pilot; the AI uses the data to do real work (categorize an expense, fill a CRM card, track tasks).
- **SQLite as source of truth, Notion as mirror**: the hybrid design keeps the authoritative data local in SQLite; Notion sync is optional, best-effort, and never blocks or crashes the agent if unconfigured or offline.

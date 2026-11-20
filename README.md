# Hirewire

A personal job-search intelligence application that brings together professional profiles, job opportunities and application activity. Hirewire provides a single CLI and keeps provider-specific code independent.

This **0.2.0 consolidation snapshot** combines Hirewire's existing Google Workspace integration, the former SkillMapper HeadHunter API implementation, and an initial offline Telegram Desktop JSON importer inspired by JobMiner.

## What works today

| Source | Implemented | Notes |
| --- | --- | --- |
| Google Workspace | OAuth, Drive, Sheets | Original Hirewire behavior and settings retained |
| HeadHunter official API | Original OAuth, HTTP, resumes and recommendations | **Disabled by default** because access is currently unavailable; opt in only if authorized |
| HeadHunter local account snapshots | Inspect saved `.html`, `.htm`, `.txt`, `.json`; export extracted text/links or original JSON | Offline, no HH network requests |
| HeadHunter browser | Optional Playwright, **manually controlled single-page capture** | Experimental and permission-dependent; no stored password, automatic login or unattended scraping |
| Telegram | Inspect/extract Telegram Desktop `result.json` messages | Offline only; no Telegram login, scraping, vacancy extraction or monitoring |

**Not implemented:** live HeadHunter website scraping or unattended login, Telegram live acquisition, canonical vacancy models, cross-source deduplication, a database, or synchronization. The page parser is generic, not a verified parser for specific authenticated HH.ru pages. Avoid treating it as structured application-history extraction until real page fixtures are available.

## Requirements

- Python **3.14+** and [`uv`](https://docs.astral.sh/uv/).
- Google API OAuth credentials only for Google operations.
- HeadHunter API credentials only if your application is granted API access again.

```bash
uv sync --locked
uv run hirewire --help
uv run hirewire google --help
uv run hirewire hhru --help
uv run hirewire telegram --help
```

### Google Workspace

The original commands remain available:

```bash
uv run hirewire google auth
uv run hirewire google status
uv run hirewire google drive list --all
uv run hirewire google sheets inspect YOUR_SHEET_ID
uv run hirewire google sheets read YOUR_SHEET_ID 'Sheet1!A1:B5'
```

See `.env.example` for environment variables and the existing `config/paths.py` for relative paths. The Google credential paths have **not** been migrated or modified.

### HeadHunter account imports (offline)

Save a page from your own account using your browser, or export an account document you are entitled to possess. No live HeadHunter requests are made by these commands.

```bash
uv run hirewire hhru status
uv run hirewire hhru imports inspect snapshots/my-applications.html
uv run hirewire hhru imports extract snapshots/my-applications.html --output private/my-applications.json
```

- `inspect` shows safe metadata (filename, title, character count and matching vacancy-link count); it intentionally does not print your full account text.
- `extract` creates a new private JSON file with page text (excluding scripts/styles) and normalized vacancy URLs; for `.json`, it preserves the supplied payload rather than inventing a schema.
- Output files are created with restricted permissions where supported, **will not overwrite** existing files, and may contain sensitive personal data.
- For HTML, only vacancy links matching `https://hh.ru/vacancy/<id>` are collected; page text remains largely unstructured.
- Source imports have a 10 MiB size limit; a different parser can be added when actual examples justify it.

### Preserved HeadHunter API

The original SkillMapper client has been placed under `hirewire.integrations.hhru`. The API is deliberately **off** by default:

```bash
uv run hirewire hhru api resumes  # returns a disabled-access message by default
```

**Only if HeadHunter restores or grants the necessary API authorization**, set:

```dotenv
HIREWIRE_HHRU__API_ENABLED=true
HIREWIRE_HHRU__OAUTH__CLIENT_ID=...
HIREWIRE_HHRU__OAUTH__CLIENT_SECRET=...
HIREWIRE_HHRU__TOKEN_STORE__PATH=.state/hhru/tokens.json
```

Then explicitly authorize and request data:

```bash
uv run hirewire hhru api auth
uv run hirewire hhru api resumes
uv run hirewire hhru api recommended --resume-id YOUR_RESUME_ID
uv run hirewire hhru api recommended    # original all-resume behavior
```

The API's original OAuth, token provider, token store, HTTP adapter, and response schemas have been preserved with package-import changes. No silent token migration is performed: to reuse a pre-existing SkillMapper `.state/tokens.json`, explicitly set `HIREWIRE_HHRU__TOKEN_STORE__PATH=.state/tokens.json`. Relative paths continue to use Hirewire's existing project-root resolver.

### Optional Playwright: manually controlled capture

This command opens an ordinary visible browser. **You log in and navigate manually**; the program waits for an explicit Enter key confirmation, then saves only the displayed page. It does not submit your email/password, bypass security challenges, crawl pages, or persist a browser session. HeadHunter may prohibit browser-based automated extraction; obtain suitable authorization before using it against their site.

Playwright is deliberately **not a core or lockfile dependency**. It is installed for one invocation only:

```bash
uv run --with playwright playwright install chromium
uv run --with playwright hirewire hhru browser capture --output private/hh-saved.html
uv run hirewire hhru imports inspect private/hh-saved.html
```

Treat the resulting HTML as confidential: hidden fields and embedded page metadata may contain sensitive material. Do not commit, publish or upload it. Use your browser's built-in Save Page feature instead if you do not have permission to automate capture.

### Telegram export imports (JobMiner first slice)

Export a Telegram channel or chat as machine-readable JSON using Telegram Desktop. Then:

```bash
uv run hirewire telegram imports inspect exports/result.json
uv run hirewire telegram imports extract exports/result.json --output private/telegram-messages.json
```

Only message text, date, message ID and exported channel name are extracted. Rich-text fragment arrays are flattened. **This is not yet vacancy recognition or Telegram scraping.** A live Telegram provider will be considered separately, based on actual acquisition requirements and permitted API methods.

## Configuration and secrets

Copy `.env.example` to `.env` and fill in only the settings needed for an enabled provider. `GoogleSettings` and `config/paths.py` remain the originals. `hhru` settings are nested under `HIREWIRE_HHRU__`, with HeadHunter API credentials entirely optional.

Ignored local data include `.env`, `.state/`, `credentials/`, `snapshots/`, `private/`, `exports/`, and Telegram session files. **Do not place token files, saved account pages or message exports elsewhere in the repository.** JSON source fixtures are no longer globally excluded, so review commits for secrets.

## Tests and environment caveat

```bash
uv run --locked pytest
```

Core source-only tests were exercised in an available Python 3.13 environment, but the project intentionally requires Python 3.14+ and the full Google test suite could not run there due to unavailable Google API libraries. A successful `uv sync --locked`, `uv lock --check`, CLI smoke test and full pytest run on Python 3.14 are required before production use. See `MIGRATION.md` for precise verification limits and rollback instructions.

## Development direction

1. Verify the full merged Python 3.14 baseline and existing Google workflows.
2. Stabilize account snapshot fixtures and structured import rules around real account pages.
3. Consider Telegram live acquisition and vacancy parsing separately.
4. Build domain workflows and SQLite persistence only when provider data demonstrates the need.

## License

MIT License. See the [LICENSE](LICENSE) file for details.

# Hirewire

Hirewire is a personal job-search tracker intended to grow into a small job-search
intelligence system. The first implementation establishes a reliable Google
Workspace integration and command-line interface. It deliberately does **not**
introduce a premature application database or a web backend.

## Current scope

- Reusable Google OAuth credentials for a desktop application.
- Google Drive file discovery, including folder-scoped listing.
- Google Sheets inspection, reading, updating, and appending.
- A CLI that owns terminal interaction; integration modules return data and
  raise errors rather than prompting.
- Unit tests using mocked Google API services.

The intended longer-term direction is to make a local SQLite database the
canonical store and use Google Sheets as a convenient human-facing projection.
That domain layer is not part of this first integration foundation.

## Requirements

- Python 3.14+
- [`uv`](https://docs.astral.sh/uv/)
- A Google Cloud project with the Google Sheets API and Google Drive API enabled.
- A Desktop OAuth client downloaded from Google Cloud Console.

## Setup

```bash
git clone <your-repository-url>
cd hirewire

# Install the project and development dependencies.
uv sync

# Create the local credentials directory.
mkdir -p credentials
```

Place the downloaded Desktop OAuth client JSON at:

```text
credentials/oauth-client.json
```

The OAuth client and generated token are local secrets. They are ignored by Git.
Do not commit them.

Optional: copy `.env.example` to `.env` and set
`HIREWIRE_GOOGLE__FOLDER_ID` to the Drive folder in which you want to keep
Hirewire-related files. The application reads `.env` without an extra dependency.
Alternatively, export the variable in your shell.

## OAuth scopes

The application requests:

- `https://www.googleapis.com/auth/spreadsheets` — read and modify spreadsheet
  content.
- `https://www.googleapis.com/auth/drive.readonly` — discover and inspect Drive
  files without modifying Drive contents.

The first authorization opens a browser. If the OAuth consent screen is in
Testing mode, the Google account must be listed as a test user. The access token
is stored in `credentials/token.json` and refreshed when possible.

To authorize again explicitly:

```bash
uv run hirewire google auth
```

## CLI

Show available commands:

```bash
uv run hirewire --help
uv run hirewire google --help
```

Authorize and check the current Google account:

```bash
uv run hirewire google auth
uv run hirewire google status
```

List Drive files (optionally restricted to the configured folder):

```bash
uv run hirewire google drive list
uv run hirewire google drive list --all
uv run hirewire google drive list --folder-id YOUR_FOLDER_ID
```

Inspect a spreadsheet and its worksheets:

```bash
uv run hirewire google sheets inspect SPREADSHEET_ID
```

Read values:

```bash
uv run hirewire google sheets read SPREADSHEET_ID 'Sheet1!A1:D20'
```

Update a range (values are supplied as JSON):

```bash
uv run hirewire google sheets update SPREADSHEET_ID 'Sheet1!A1:B2'   '[["Company", "Role"], ["Example Ltd", "Python Engineer"]]'
```

Append rows to a worksheet:

```bash
uv run hirewire google sheets append SPREADSHEET_ID Sheet1   '[["Example Ltd", "Python Engineer"], ["Another Ltd", "Data Engineer"]]'
```

All commands print machine-readable JSON where practical. Errors are written to
stderr and produce a non-zero exit status.

## Development

```bash
uv run pytest
```

The tests do not require Google credentials or network access. They exercise
pure configuration/parsing behavior and mock the Google API service boundary.

## Project structure

```text
.
├── .env.example
├── .gitignore
├── README.md
├── pyproject.toml
├── credentials/                 # local only; ignored
├── src/hirewire/
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py
│   ├── config/
│   │   ├── __init__.py
│   │   └── paths.py
│   └── integrations/google/
│       ├── __init__.py
│       ├── auth.py
│       ├── drive.py
│       └── sheets.py
└── tests/
```

## Security notes

- Never commit `credentials/`, OAuth client JSON, token JSON, or service-account
  credentials.
- `.gitignore` prevents future accidental additions but does not remove secrets
  already committed to Git history. If a credential was committed, revoke or
  rotate it in Google Cloud and clean the repository history as appropriate.
- Do not share `token.json`; it contains reusable authorization material.

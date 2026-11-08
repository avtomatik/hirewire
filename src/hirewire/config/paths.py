import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[3]
CREDENTIALS_DIR = BASE_DIR / "credentials"
CREDENTIALS_FILE = CREDENTIALS_DIR / "oauth-client.json"
TOKEN_FILE = CREDENTIALS_DIR / "token.json"
ENV_FILE = BASE_DIR / ".env"


def _load_dotenv_file(path: Path = ENV_FILE) -> None:
    """Load simple KEY=VALUE entries without overriding shell environment.
    This intentionally supports only the small dotenv subset needed here:
    blank lines, comments, optional 'export ', and matching single/double quotes.
    """
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key or key in os.environ:
            continue
        if (
            len(value) >= 2
            and value[0] == value[-1]
            and value[0] in ("'", '"')
        ):
            value = value[1:-1]
        os.environ[key] = value


def get_google_folder_id() -> str | None:
    _load_dotenv_file()
    value = os.getenv("HIREWIRE_GOOGLE__FOLDER_ID", "").strip()
    return value or None

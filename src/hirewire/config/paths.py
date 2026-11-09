from pathlib import Path

# This project uses a src/ layout:
# <project root>/src/hirewire/config/paths.py
BASE_DIR = Path(__file__).resolve().parents[3]
CREDENTIALS_DIR = BASE_DIR / "credentials"


def resolve_project_path(path: Path) -> Path:
    """Resolve an absolute path as-is or a relative path from the project root."""
    path = path.expanduser()
    if path.is_absolute():
        return path
    return BASE_DIR / path

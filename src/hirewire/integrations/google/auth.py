import os
import tempfile
from pathlib import Path

from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from hirewire.config.paths import resolve_project_path
from hirewire.config.settings import Settings, get_settings

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.readonly",
]


def authorize_once(settings: Settings | None = None) -> Credentials:
    """Run a fresh interactive desktop OAuth flow and persist its token."""
    settings = settings or get_settings()
    credentials_file = resolve_project_path(settings.google.oauth_client_file)
    token_file = resolve_project_path(settings.google.token_file)
    if not credentials_file.is_file():
        raise FileNotFoundError(
            f"OAuth client credentials not found: {credentials_file}. "
            "Download a Desktop OAuth client JSON and place it there."
        )
    flow = InstalledAppFlow.from_client_secrets_file(
        str(credentials_file), SCOPES
    )
    credentials = flow.run_local_server(
        host="localhost",
        port=0,
        access_type="offline",
        prompt="consent",
    )
    _save_credentials(credentials, token_file)
    return credentials


def _save_credentials(credentials: Credentials, token_file: Path) -> None:
    """Persist credentials atomically, restricting the token file permissions."""
    token_file.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=token_file.parent,
            prefix=f".{token_file.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)
            temporary_file.write(credentials.to_json())
            temporary_file.flush()
            os.fsync(temporary_file.fileno())
        os.chmod(temporary_path, 0o600)
        os.replace(temporary_path, token_file)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def get_credentials(settings: Settings | None = None) -> Credentials:
    """Return valid credentials, refreshing or starting OAuth when needed.
    A refresh-token rejection starts a new interactive authorization. Network
    and other refresh failures are allowed to propagate rather than opening a
    browser for what may only be a temporary connectivity problem.
    """
    settings = settings or get_settings()
    token_file = resolve_project_path(settings.google.token_file)
    credentials: Credentials | None = None
    if token_file.is_file():
        credentials = Credentials.from_authorized_user_file(
            str(token_file), SCOPES
        )
    if credentials and credentials.valid:
        return credentials
    if credentials and credentials.expired and credentials.refresh_token:
        try:
            credentials.refresh(Request())
        except RefreshError:
            # A rejected/revoked refresh token requires a fresh user grant.
            return authorize_once(settings)
        _save_credentials(credentials, token_file)
        return credentials
    return authorize_once(settings)

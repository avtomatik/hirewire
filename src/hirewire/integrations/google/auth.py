import os

from google.auth.exceptions import GoogleAuthError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from hirewire.config.paths import CREDENTIALS_FILE, TOKEN_FILE

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.readonly",
]


def authorize_once() -> Credentials:
    """Run a fresh interactive desktop OAuth flow and persist its token."""
    if not CREDENTIALS_FILE.is_file():
        raise FileNotFoundError(
            f"OAuth client credentials not found: {CREDENTIALS_FILE}. "
            "Download a Desktop OAuth client JSON and place it there."
        )
    flow = InstalledAppFlow.from_client_secrets_file(
        str(CREDENTIALS_FILE), SCOPES
    )
    credentials = flow.run_local_server(
        host="localhost",
        port=0,
        access_type="offline",
        prompt="consent",
    )
    _save_credentials(credentials)
    return credentials


def _save_credentials(credentials: Credentials) -> None:
    TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = TOKEN_FILE.with_suffix(".tmp")
    temporary_path.write_text(credentials.to_json(), encoding="utf-8")
    os.chmod(temporary_path, 0o600)
    temporary_path.replace(TOKEN_FILE)


def get_credentials() -> Credentials:
    """Return valid credentials, refreshing or starting OAuth when needed."""
    credentials: Credentials | None = None
    if TOKEN_FILE.is_file():
        credentials = Credentials.from_authorized_user_file(
            str(TOKEN_FILE), SCOPES
        )
    if credentials and credentials.valid:
        return credentials
    if credentials and credentials.expired and credentials.refresh_token:
        try:
            credentials.refresh(Request())
            _save_credentials(credentials)
            return credentials
        except GoogleAuthError:
            # A revoked/invalid refresh token needs a new interactive grant.
            pass
    return authorize_once()

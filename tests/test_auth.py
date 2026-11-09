import os
import stat
from pathlib import Path
from unittest.mock import Mock

import pytest
from google.auth.exceptions import RefreshError

from hirewire.config.settings import GoogleSettings, Settings
from hirewire.integrations.google import auth


def make_settings(tmp_path: Path) -> Settings:
    return Settings(
        _env_file=None,
        google=GoogleSettings(
            oauth_client_file=tmp_path / "oauth-client.json",
            token_file=tmp_path / "credentials" / "token.json",
        ),
    )


def test_authorize_once_uses_configured_files_and_saves_token(
    tmp_path, monkeypatch
):
    settings = make_settings(tmp_path)
    settings.google.oauth_client_file.write_text("{}", encoding="utf-8")
    credentials = Mock(valid=True)
    credentials.to_json.return_value = '{"token": "secret"}'
    flow = Mock()
    flow.run_local_server.return_value = credentials
    from_client_secrets_file = Mock(return_value=flow)
    monkeypatch.setattr(
        auth.InstalledAppFlow,
        "from_client_secrets_file",
        from_client_secrets_file,
    )
    result = auth.authorize_once(settings)
    assert result is credentials
    from_client_secrets_file.assert_called_once_with(
        str(settings.google.oauth_client_file), auth.SCOPES
    )
    flow.run_local_server.assert_called_once_with(
        host="localhost",
        port=0,
        access_type="offline",
        prompt="consent",
    )
    assert settings.google.token_file.read_text(encoding="utf-8") == (
        '{"token": "secret"}'
    )


def test_authorize_once_explains_missing_oauth_client(tmp_path):
    settings = make_settings(tmp_path)
    with pytest.raises(
        FileNotFoundError, match="OAuth client credentials not found"
    ):
        auth.authorize_once(settings)


def test_get_credentials_returns_valid_cached_token(tmp_path, monkeypatch):
    settings = make_settings(tmp_path)
    settings.google.token_file.parent.mkdir(parents=True, exist_ok=True)
    settings.google.token_file.touch()
    credentials = Mock(valid=True)
    loader = Mock(return_value=credentials)
    monkeypatch.setattr(auth.Credentials, "from_authorized_user_file", loader)
    result = auth.get_credentials(settings)
    assert result is credentials
    loader.assert_called_once_with(
        str(settings.google.token_file), auth.SCOPES
    )


def test_get_credentials_refreshes_and_saves_to_configured_token_path(
    tmp_path, monkeypatch
):
    settings = make_settings(tmp_path)
    settings.google.token_file.parent.mkdir(parents=True, exist_ok=True)
    settings.google.token_file.touch()
    credentials = Mock(
        valid=False, expired=True, refresh_token="refresh-token"
    )
    monkeypatch.setattr(
        auth.Credentials,
        "from_authorized_user_file",
        Mock(return_value=credentials),
    )
    save = Mock()
    monkeypatch.setattr(auth, "_save_credentials", save)
    monkeypatch.setattr(auth, "Request", Mock(return_value="request"))
    result = auth.get_credentials(settings)
    assert result is credentials
    credentials.refresh.assert_called_once_with("request")
    save.assert_called_once_with(credentials, settings.google.token_file)


def test_get_credentials_reauthorizes_when_refresh_token_is_rejected(
    tmp_path, monkeypatch
):
    settings = make_settings(tmp_path)
    credentials = Mock(valid=False, expired=True, refresh_token="revoked")
    credentials.refresh.side_effect = RefreshError("invalid_grant")
    monkeypatch.setattr(
        auth.Credentials,
        "from_authorized_user_file",
        Mock(return_value=credentials),
    )
    authorize = Mock(return_value=Mock(valid=True))
    monkeypatch.setattr(auth, "authorize_once", authorize)
    result = auth.get_credentials(settings)
    assert result is authorize.return_value
    authorize.assert_called_once_with(settings)


def test_get_credentials_starts_oauth_when_token_is_missing(
    tmp_path, monkeypatch
):
    settings = make_settings(tmp_path)
    authorize = Mock(return_value=Mock(valid=True))
    monkeypatch.setattr(auth, "authorize_once", authorize)
    result = auth.get_credentials(settings)
    assert result is authorize.return_value
    authorize.assert_called_once_with(settings)


def test_save_credentials_creates_private_token_file(tmp_path):
    token_file = tmp_path / "credentials" / "token.json"
    credentials = Mock()
    credentials.to_json.return_value = '{"access_token": "secret"}'
    auth._save_credentials(credentials, token_file)
    assert token_file.read_text(encoding="utf-8") == (
        '{"access_token": "secret"}'
    )
    if os.name == "posix":
        assert stat.S_IMODE(token_file.stat().st_mode) == 0o600


def test_get_credentials_does_not_start_browser_for_temporary_refresh_failure(
    tmp_path, monkeypatch
):
    from google.auth.exceptions import GoogleAuthError

    settings = make_settings(tmp_path)
    settings.google.token_file.parent.mkdir(parents=True, exist_ok=True)
    settings.google.token_file.touch()
    credentials = Mock(
        valid=False, expired=True, refresh_token="refresh-token"
    )
    credentials.refresh.side_effect = GoogleAuthError(
        "temporary transport failure"
    )
    monkeypatch.setattr(
        auth.Credentials,
        "from_authorized_user_file",
        Mock(return_value=credentials),
    )
    authorize = Mock()
    monkeypatch.setattr(auth, "authorize_once", authorize)
    with pytest.raises(GoogleAuthError, match="temporary transport failure"):
        auth.get_credentials(settings)
    authorize.assert_not_called()

import os
from pathlib import Path

import pytest
from pydantic import ValidationError

from hirewire.config.paths import BASE_DIR, resolve_project_path
from hirewire.config.settings import GoogleSettings, Settings, get_settings


@pytest.fixture(autouse=True)
def isolate_hirewire_environment(monkeypatch):
    """Prevent a developer's shell environment from leaking into tests."""
    for name in tuple(os.environ):
        if name.startswith("HIREWIRE_"):
            monkeypatch.delenv(name, raising=False)


def test_default_settings_are_usable_without_google_configuration():
    settings = Settings(_env_file=None)
    assert settings.environment == "development"
    assert settings.debug is False
    assert settings.log_level == "INFO"
    assert settings.google.folder_id is None
    assert settings.google.spreadsheet_id is None
    assert settings.google.oauth_client_file == (
        BASE_DIR / "credentials" / "oauth-client.json"
    )


def test_nested_environment_variables(monkeypatch):
    monkeypatch.setenv("HIREWIRE_GOOGLE__FOLDER_ID", "folder-123")
    monkeypatch.setenv("HIREWIRE_GOOGLE__SPREADSHEET_ID", "sheet-456")
    settings = Settings(_env_file=None)
    assert settings.google.folder_id == "folder-123"
    assert settings.google.spreadsheet_id == "sheet-456"


def test_environment_variable_overrides_default(monkeypatch):
    monkeypatch.setenv("HIREWIRE_DEBUG", "true")
    settings = Settings(_env_file=None)
    assert settings.debug is True


def test_constructor_values_override_environment(monkeypatch):
    monkeypatch.setenv("HIREWIRE_DEBUG", "true")
    settings = Settings(_env_file=None, debug=False)
    assert settings.debug is False


def test_dotenv_file_is_loaded_and_environment_takes_precedence(
    tmp_path: Path, monkeypatch
):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "HIREWIRE_DEBUG=true\nHIREWIRE_LOG_LEVEL=DEBUG\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("HIREWIRE_DEBUG", "false")
    settings = Settings(_env_file=env_file)
    assert settings.debug is False
    assert settings.log_level == "DEBUG"


def test_invalid_environment_is_rejected():
    with pytest.raises(ValidationError):
        Settings(_env_file=None, environment="staging")


def test_google_settings_can_be_overridden_with_constructor_values(tmp_path):
    credentials_file = tmp_path / "oauth.json"
    token_file = tmp_path / "token.json"
    settings = Settings(
        _env_file=None,
        google=GoogleSettings(
            oauth_client_file=credentials_file,
            token_file=token_file,
        ),
    )
    assert settings.google.oauth_client_file == credentials_file
    assert settings.google.token_file == token_file


def test_get_settings_returns_a_cached_instance(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("HIREWIRE_DEBUG", "true")
    try:
        first = get_settings()
        monkeypatch.setenv("HIREWIRE_DEBUG", "false")
        second = get_settings()
        assert first is second
        assert second.debug is True
    finally:
        get_settings.cache_clear()


def test_resolve_project_path_anchors_relative_paths_to_project_root(tmp_path):
    relative = Path("data") / "jobs.json"
    absolute = tmp_path / "jobs.json"
    assert resolve_project_path(relative) == BASE_DIR / relative
    assert resolve_project_path(absolute) == absolute


def test_blank_optional_google_ids_are_treated_as_unset():
    settings = Settings(
        _env_file=None,
        google=GoogleSettings(folder_id="  ", spreadsheet_id=""),
    )
    assert settings.google.folder_id is None
    assert settings.google.spreadsheet_id is None

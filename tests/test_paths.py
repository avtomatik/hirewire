from hirewire.config.paths import get_google_folder_id


def test_get_google_folder_id_returns_none_when_unset(monkeypatch, tmp_path):
    monkeypatch.delenv("HIREWIRE_GOOGLE__FOLDER_ID", raising=False)
    env_file = tmp_path / ".env"
    assert get_google_folder_id.__module__ == "hirewire.config.paths"
    # The public function reads the project .env; shell environment remains authoritative.
    monkeypatch.setenv("HIREWIRE_GOOGLE__FOLDER_ID", "")
    assert get_google_folder_id() is None


def test_get_google_folder_id_reads_environment(monkeypatch):
    monkeypatch.setenv("HIREWIRE_GOOGLE__FOLDER_ID", "folder-123")
    assert get_google_folder_id() == "folder-123"

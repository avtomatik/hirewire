"""Tests exercising the merge boundaries without live credentials or APIs."""

import json
import os

import pytest
from typer.testing import CliRunner

from hirewire.cli_sources import hhru_app, telegram_app
from hirewire.config.settings import Settings
from hirewire.integrations.hhru import api_runtime
from hirewire.integrations.hhru.imports.saved import extract, inspect
from hirewire.integrations.telegram.imports import (import_export,
                                                    inspect_export)

runner = CliRunner()


def test_api_dormant_without_account_credentials():
    settings = Settings(_env_file=None)
    assert settings.hhru.api_enabled is False
    assert settings.hhru.oauth is None
    with pytest.raises(RuntimeError, match="disabled"):
        api_runtime.resumes(settings)


def test_optional_nested_account_credentials(monkeypatch):
    monkeypatch.setenv("HIREWIRE_HHRU__API_ENABLED", "true")
    monkeypatch.setenv("HIREWIRE_HHRU__OAUTH__CLIENT_ID", "test-client")
    monkeypatch.setenv("HIREWIRE_HHRU__OAUTH__CLIENT_SECRET", "test-secret")
    settings = Settings(_env_file=None)
    assert settings.hhru.api_enabled
    assert settings.hhru.oauth.client_id == "test-client"
    assert "test-secret" not in repr(settings)


def test_saved_html_extracts_only_clean_vacancy_urls(tmp_path):
    p = tmp_path / "my-account.html"
    p.write_text(
        """<html><head><title>My applications</title>
    <style>hidden styling</style></head><body><h1>Applications</h1>
    <p>Data scientist</p><script>token = "private"</script>
    <a href="/vacancy/12345?from=tracking">one</a>
    <a href="https://evil.example/vacancy/999">other</a>
    <a href="https://hh.ru/vacancy/12345#related">duplicate</a>
    </body></html>"""
    )
    result = extract(p)
    assert result["title"] == "My applications"
    assert "Data scientist" in result["text"]
    assert "private" not in result["text"]
    assert result["vacancy_urls"] == ["https://hh.ru/vacancy/12345"]
    assert inspect(p)["vacancy_count"] == 1
    assert "Data scientist" not in str(inspect(p))


def test_saved_json_keeps_user_supplied_data(tmp_path):
    p = tmp_path / "account.json"
    p.write_text('{"resumes": [{"id": "r1"}]}')
    assert extract(p)["data"]["resumes"][0]["id"] == "r1"
    assert inspect(p)["top_level_keys"] == ["resumes"]


def test_unsupported_or_oversized_snapshot(tmp_path):
    p = tmp_path / "page.exe"
    p.write_text("not html")
    with pytest.raises(ValueError, match="HTML"):
        extract(p)
    p = tmp_path / "huge.txt"
    p.write_bytes(b"x" * (10 * 1024 * 1024 + 1))
    with pytest.raises(ValueError, match="10 MiB"):
        extract(p)


def test_telegram_export_with_rich_text_and_service_messages(tmp_path):
    path = tmp_path / "result.json"
    path.write_text(
        json.dumps(
            {
                "name": "Jobs",
                "messages": [
                    {
                        "id": 1,
                        "date": "2026-11-01",
                        "type": "message",
                        "text": [
                            "Python ",
                            {"type": "bold", "text": "developer"},
                        ],
                    },
                    {"id": 2, "type": "service", "text": "changed title"},
                    {"id": 3, "type": "message", "text": ""},
                ],
            }
        )
    )
    result = import_export(path)
    assert result == [
        {
            "channel": "Jobs",
            "message_id": 1,
            "date": "2026-11-01",
            "text": "Python developer",
        }
    ]
    assert inspect_export(path)["messages"] == 1


def test_cli_reports_api_disabled_without_network():
    result = runner.invoke(hhru_app, ["api", "resumes"])
    assert result.exit_code == 1
    assert "disabled" in result.output


def test_cli_snapshot_export_is_private_and_no_overwrite(tmp_path):
    snapshot = tmp_path / "personal.txt"
    snapshot.write_text("My private note")
    output = tmp_path / "private" / "record.json"
    result = runner.invoke(
        hhru_app,
        ["imports", "extract", str(snapshot), "--output", str(output)],
    )
    assert result.exit_code == 0, result.output
    assert json.loads(output.read_text())["text"] == "My private note"
    if os.name == "posix":
        assert output.stat().st_mode & 0o777 == 0o600
    result = runner.invoke(
        hhru_app,
        ["imports", "extract", str(snapshot), "--output", str(output)],
    )
    assert result.exit_code == 1
    assert json.loads(output.read_text())["text"] == "My private note"


def test_telegram_cli_extract(tmp_path):
    archive = tmp_path / "result.json"
    archive.write_text(
        '{"name":"Test","messages":[{"type":"message","id":1,"text":"Job"}]}'
    )
    dest = tmp_path / "export.json"
    result = runner.invoke(
        telegram_app,
        ["imports", "extract", str(archive), "--output", str(dest)],
    )
    assert result.exit_code == 0, result.output
    assert json.loads(dest.read_text())[0]["text"] == "Job"


def test_cli_help_exposes_expected_groups():
    result = runner.invoke(hhru_app, ["--help"])
    assert result.exit_code == 0, result.output
    assert (
        "browser" in result.output
        and "imports" in result.output
        and "api" in result.output
    )

"""CLI commands for preserved HH API and user-controlled source imports."""

import json
import os
from pathlib import Path
from typing import Any

import typer

from hirewire.config.paths import resolve_project_path
from hirewire.config.settings import get_settings
from hirewire.integrations.hhru import api_runtime
from hirewire.integrations.hhru.imports import saved
from hirewire.integrations.telegram import imports as telegram_imports

hhru_app = typer.Typer(
    help="HeadHunter personal account: archived API and offline imports."
)
hhru_api = typer.Typer(
    help="Preserved HeadHunter API (disabled unless explicitly enabled)."
)
hhru_imports = typer.Typer(
    help="Inspect and extract locally saved HeadHunter account pages."
)
hhru_browser = typer.Typer(
    help="Optional explicitly directed Playwright browser capture."
)
telegram_app = typer.Typer(
    help="Telegram vacancy sources; offline exports first (JobMiner)."
)
telegram_imports_app = typer.Typer(
    help="Inspect and extract Telegram Desktop JSON exports."
)
hhru_app.add_typer(hhru_api, name="api")
hhru_app.add_typer(hhru_imports, name="imports")
hhru_app.add_typer(hhru_browser, name="browser")
telegram_app.add_typer(telegram_imports_app, name="imports")


def _print(data: Any) -> None:
    typer.echo(json.dumps(data, ensure_ascii=False, indent=2, default=str))


def _run(func):
    from pydantic import ValidationError
    from requests.exceptions import RequestException

    try:
        return func()
    except (
        OSError,
        ValueError,
        RuntimeError,
        RequestException,
        ValidationError,
    ) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from exc


def _write_private_json(target: Path, data: Any) -> dict:
    """Exclusively create a private output; remove partial files after failure."""
    target = target.expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        try:
            os.fchmod(fd, 0o600)
        except OSError:
            pass
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(data, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
    except Exception:
        target.unlink(missing_ok=True)
        raise
    return {"saved": str(target)}


@hhru_app.command("status")
def hhru_status() -> None:
    """Show configured HeadHunter access status; never read or print secrets."""

    def operation():
        hh = get_settings().hhru
        return {
            "api_enabled": hh.api_enabled,
            "api_credentials_configured": hh.oauth is not None,
            "api_token_file_exists": resolve_project_path(
                hh.token_store.path
            ).is_file(),
            "browser_capture": "manual opt-in; optional Playwright dependency",
            "offline_imports": [".html", ".htm", ".txt", ".json"],
        }

    _print(_run(operation))


@hhru_api.command("auth")
def hhru_api_auth() -> None:
    """Explicit HeadHunter OAuth login; only when API access has been restored."""
    _print(_run(lambda: api_runtime.authorize(get_settings())))


@hhru_api.command("resumes")
def hhru_api_resumes() -> None:
    """List resumes through the preserved API (requires authorized access)."""
    _print(_run(lambda: api_runtime.resumes(get_settings())))


@hhru_api.command("recommended")
def hhru_api_recommended(
    resume_id: str | None = typer.Option(
        None, "--resume-id", help="Limit to one resume (default: all)."
    ),
) -> None:
    """Retrieve recommended vacancies through the preserved API."""
    _print(
        _run(lambda: api_runtime.recommendations(get_settings(), resume_id))
    )


@hhru_imports.command("inspect")
def hhru_import_inspect(path: Path) -> None:
    """Inspect a saved account snapshot without printing its private contents."""
    _print(_run(lambda: saved.inspect(path)))


@hhru_imports.command("extract")
def hhru_import_extract(
    path: Path,
    output: Path = typer.Option(
        ..., "--output", help="New private JSON output file."
    ),
) -> None:
    """Extract a saved snapshot locally; contains potentially sensitive account text."""
    _print(_run(lambda: _write_private_json(output, saved.extract(path))))


@hhru_browser.command("capture")
def hhru_browser_capture(
    output: Path = typer.Option(
        ..., "--output", help="New private HTML snapshot file."
    ),
) -> None:
    """Manually sign in and navigate; explicitly confirm a single-page capture."""

    def operation():
        from hirewire.integrations.hhru.browser.capture import capture_manual

        return capture_manual(output)

    _print(_run(operation))


@telegram_imports_app.command("inspect")
def telegram_inspect(path: Path) -> None:
    """Show metadata for a local Telegram Desktop JSON export."""
    _print(_run(lambda: telegram_imports.inspect_export(path)))


@telegram_imports_app.command("extract")
def telegram_extract(
    path: Path,
    output: Path = typer.Option(
        ..., "--output", help="New private JSON output file."
    ),
) -> None:
    """Extract messages from a Telegram Desktop JSON export."""
    _print(
        _run(
            lambda: _write_private_json(
                output, telegram_imports.import_export(path)
            )
        )
    )

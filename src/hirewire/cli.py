import json
from typing import Any

import typer
from googleapiclient.errors import HttpError

from hirewire.config.paths import get_google_folder_id
from hirewire.integrations.google import drive, sheets
from hirewire.integrations.google.auth import authorize_once, get_credentials

app = typer.Typer(help="Hirewire job-search tracker.")
google_app = typer.Typer(help="Google Workspace integration.")
drive_app = typer.Typer(help="Google Drive operations.")
sheets_app = typer.Typer(help="Google Sheets operations.")
app.add_typer(google_app, name="google")
google_app.add_typer(drive_app, name="drive")
google_app.add_typer(sheets_app, name="sheets")


def _print_json(value: Any) -> None:
    typer.echo(json.dumps(value, indent=2, ensure_ascii=False, default=str))


def _run(operation: Any) -> None:
    try:
        _print_json(operation())
    except (HttpError, OSError, ValueError, RuntimeError) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from exc


@google_app.command("auth")
def google_auth() -> None:
    """Perform a fresh interactive OAuth authorization."""
    _run(
        lambda: {
            "authorized": bool(authorize_once().valid),
            "token_file": "credentials/token.json",
        }
    )


@google_app.command("status")
def google_status() -> None:
    """Show the authenticated Google account and configured folder."""

    def operation() -> dict[str, Any]:
        credentials = get_credentials()
        from googleapiclient.discovery import build

        about = (
            build(
                "drive", "v3", credentials=credentials, cache_discovery=False
            )
            .about()
            .get(fields="user(displayName,emailAddress)")
            .execute()
        )
        return {
            "authenticated": credentials.valid,
            "user": about.get("user", {}),
            "configured_folder_id": get_google_folder_id(),
            "credentials_file": "credentials/oauth-client.json",
            "token_file": "credentials/token.json",
        }

    _run(operation)


@drive_app.command("list")
def drive_list(
    all_files: bool = typer.Option(
        False, "--all", help="List all accessible Drive files."
    ),
    folder_id: str | None = typer.Option(
        None, "--folder-id", help="Restrict results to this folder."
    ),
    page_size: int = typer.Option(100, min=1, max=1000),
) -> None:
    """List files in the configured folder, or all Drive files with --all."""
    selected_folder = folder_id
    if not all_files and selected_folder is None:
        selected_folder = get_google_folder_id()
    _run(
        lambda: drive.list_files(
            folder_id=selected_folder, page_size=page_size
        )
    )


@sheets_app.command("inspect")
def sheets_inspect(spreadsheet_id: str) -> None:
    """Show spreadsheet metadata and worksheet names."""
    _run(lambda: sheets.inspect_spreadsheet(spreadsheet_id))


@sheets_app.command("read")
def sheets_read(spreadsheet_id: str, range_name: str) -> None:
    """Read a spreadsheet range."""
    _run(
        lambda: {
            "range": range_name,
            "values": sheets.read_values(spreadsheet_id, range_name),
        }
    )


@sheets_app.command("update")
def sheets_update(
    spreadsheet_id: str,
    range_name: str,
    values_json: str = typer.Argument(
        help="""JSON array of rows, e.g. '[["A","B"]]'"""
    ),
) -> None:
    """Write values to an explicit A1 range."""

    def operation() -> dict[str, Any]:
        values = json.loads(values_json)
        if not isinstance(values, list) or any(
            not isinstance(row, list) for row in values
        ):
            raise ValueError("values_json must be a JSON array of row arrays")
        return sheets.update_values(spreadsheet_id, range_name, values)

    _run(operation)


@sheets_app.command("append")
def sheets_append(
    spreadsheet_id: str,
    worksheet: str,
    values_json: str = typer.Argument(
        help="""JSON array of rows, e.g. '[["A","B"]]'"""
    ),
) -> None:
    """Append rows to a worksheet."""

    def operation() -> dict[str, Any]:
        values = json.loads(values_json)
        if not isinstance(values, list) or any(
            not isinstance(row, list) for row in values
        ):
            raise ValueError("values_json must be a JSON array of row arrays")
        return sheets.append_values(spreadsheet_id, worksheet, values)

    _run(operation)


if __name__ == "__main__":
    app()

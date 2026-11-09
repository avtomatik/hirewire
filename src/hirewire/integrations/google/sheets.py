from typing import Any, Sequence

from googleapiclient.discovery import Resource

from hirewire.integrations.google.auth import get_credentials


def build_sheets_service() -> Resource:
    from googleapiclient.discovery import build

    return build(
        "sheets", "v4", credentials=get_credentials(), cache_discovery=False
    )


def inspect_spreadsheet(
    spreadsheet_id: str, *, service: Resource | None = None
) -> dict[str, Any]:
    _validate_spreadsheet_id(spreadsheet_id)
    service = service or build_sheets_service()
    return (
        service.spreadsheets()
        .get(
            spreadsheetId=spreadsheet_id,
            fields=(
                "spreadsheetId,spreadsheetUrl,properties(title),"
                "sheets(properties("
                "sheetId,title,index,gridProperties(rowCount,columnCount)))"
            ),
        )
        .execute()
    )


def read_values(
    spreadsheet_id: str,
    range_name: str,
    *,
    service: Resource | None = None,
    value_render_option: str = "FORMATTED_VALUE",
) -> list[list[Any]]:
    _validate_spreadsheet_id(spreadsheet_id)
    if not range_name.strip():
        raise ValueError("range_name must not be empty")
    service = service or build_sheets_service()
    response = (
        service.spreadsheets()
        .values()
        .get(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueRenderOption=value_render_option,
        )
        .execute()
    )
    return response.get("values", [])


def update_values(
    spreadsheet_id: str,
    range_name: str,
    values: Sequence[Sequence[Any]],
    *,
    service: Resource | None = None,
    value_input_option: str = "USER_ENTERED",
) -> dict[str, Any]:
    _validate_spreadsheet_id(spreadsheet_id)
    if not range_name.strip():
        raise ValueError("range_name must not be empty")
    service = service or build_sheets_service()
    return (
        service.spreadsheets()
        .values()
        .update(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption=value_input_option,
            body={"values": [list(row) for row in values]},
        )
        .execute()
    )


def append_values(
    spreadsheet_id: str,
    range_name: str,
    values: Sequence[Sequence[Any]],
    *,
    service: Resource | None = None,
    value_input_option: str = "USER_ENTERED",
    insert_data_option: str = "INSERT_ROWS",
) -> dict[str, Any]:
    _validate_spreadsheet_id(spreadsheet_id)
    if not range_name.strip():
        raise ValueError("range_name must not be empty")
    if not values:
        raise ValueError("values must contain at least one row")
    service = service or build_sheets_service()
    return (
        service.spreadsheets()
        .values()
        .append(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption=value_input_option,
            insertDataOption=insert_data_option,
            body={"values": [list(row) for row in values]},
        )
        .execute()
    )


def _validate_spreadsheet_id(spreadsheet_id: str) -> None:
    if not spreadsheet_id or not spreadsheet_id.strip():
        raise ValueError("spreadsheet_id must not be empty")

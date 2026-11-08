from typing import Any

from googleapiclient.discovery import Resource

from hirewire.integrations.google.auth import get_credentials


def build_drive_service() -> Resource:
    from googleapiclient.discovery import build

    return build(
        "drive", "v3", credentials=get_credentials(), cache_discovery=False
    )


def list_files(
    *,
    folder_id: str | None = None,
    page_size: int = 100,
    include_trashed: bool = False,
    service: Resource | None = None,
) -> list[dict[str, Any]]:
    """List Drive files, following every page of results."""
    if not 1 <= page_size <= 1000:
        raise ValueError("page_size must be between 1 and 1000")
    service = service or build_drive_service()
    clauses = []
    if folder_id:
        escaped_id = folder_id.replace("\\", "\\\\").replace("'", "\\'")
        clauses.append(f"'{escaped_id}' in parents")
    if not include_trashed:
        clauses.append("trashed = false")
    query = " and ".join(clauses) if clauses else None
    results: list[dict[str, Any]] = []
    page_token = None
    while True:
        response = (
            service.files()
            .list(
                q=query,
                pageSize=page_size,
                pageToken=page_token,
                orderBy="name",
                fields="nextPageToken, files(id,name,mimeType,modifiedTime,webViewLink,parents)",
            )
            .execute()
        )
        results.extend(response.get("files", []))
        page_token = response.get("nextPageToken")
        if not page_token:
            break
    return results


def get_file(
    file_id: str, *, service: Resource | None = None
) -> dict[str, Any]:
    if not file_id.strip():
        raise ValueError("file_id must not be empty")
    service = service or build_drive_service()
    return (
        service.files()
        .get(
            fileId=file_id,
            fields="id,name,mimeType,modifiedTime,webViewLink,parents",
        )
        .execute()
    )

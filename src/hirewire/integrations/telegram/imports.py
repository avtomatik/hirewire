"""Offline Telegram Desktop JSON export reading (JobMiner's first working slice)."""

import json
from pathlib import Path

MAX_BYTES = 20 * 1024 * 1024


def import_export(path: Path) -> list[dict]:
    path = Path(path)
    if path.suffix.lower() != ".json":
        raise ValueError(
            "Expected Telegram Desktop JSON export (result.json)."
        )
    if path.stat().st_size > MAX_BYTES:
        raise ValueError("Telegram export exceeds 20 MiB limit.")
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict) or not isinstance(
        payload.get("messages"), list
    ):
        raise ValueError("Telegram JSON must contain a messages array.")
    channel = payload.get("name") or "unknown"
    records = []
    for item in payload["messages"]:
        if not isinstance(item, dict) or item.get("type") != "message":
            continue
        body = item.get("text", "")
        if isinstance(body, list):
            body = "".join(
                part if isinstance(part, str) else str(part.get("text", ""))
                for part in body
                if isinstance(part, (str, dict))
            )
        if not isinstance(body, str) or not body.strip():
            continue
        records.append(
            {
                "channel": channel,
                "message_id": item.get("id"),
                "date": item.get("date"),
                "text": body.strip(),
            }
        )
    return records


def inspect_export(path: Path) -> dict:
    records = import_export(path)
    return {
        "filename": Path(path).name,
        "messages": len(records),
        "channel": records[0]["channel"] if records else None,
    }

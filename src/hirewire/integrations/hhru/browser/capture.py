"""Optional, manually directed Playwright HTML snapshot capture.
No automatic login, crawling, hidden endpoints, rate-evasion or credential storage.
Obtain permission before using browser automation against a service.
"""

import os
from pathlib import Path


def capture_manual(output: Path) -> dict:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError(
            "Playwright is optional. Use uv run --with playwright hirewire hhru "
            "browser capture, after installing Chromium with "
            "uv run --with playwright playwright install chromium."
        ) from exc
    output = Path(output).expanduser()
    if output.exists():
        raise FileExistsError(
            f"Refusing to overwrite existing snapshot: {output}"
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)
        try:
            page = browser.new_page()
            page.goto("https://hh.ru/", wait_until="domcontentloaded")
            try:
                input(
                    "Navigate and sign in manually in the open browser. "
                    "Press Enter HERE to save the current page, or Ctrl-C to cancel: "
                )
            except EOFError as exc:
                raise RuntimeError(
                    "An interactive terminal is required for capture."
                ) from exc
            # Only capture the user-selected page after an explicit confirmation.
            html = page.content()
            fd = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                stream.write(html)
            return {"saved": str(output), "bytes": len(html.encode("utf-8"))}
        finally:
            browser.close()

"""Offline inspection and extraction of explicitly supplied personal account snapshots.
No network requests. This is deliberately not a claimed HH.ru page-specific parser:
real account fixtures are needed before reliably normalizing resumes/applications.
"""

import json
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse

MAX_BYTES = 10 * 1024 * 1024
SUPPORTED = {".html", ".htm", ".txt", ".json"}
_VACANCY = re.compile(r"/vacancy/(\d+)(?:/|$)")


class _VisibleHTML(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._ignored = 0
        self._title = False
        self.title_parts: list[str] = []
        self.parts: list[str] = []
        self.vacancy_urls: set[str] = set()

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        if tag in {"script", "style", "noscript", "svg"}:
            self._ignored += 1
        if tag == "title":
            self._title = True
        if tag == "a":
            href = dict(attrs).get("href")
            if not href:
                return
            url = urljoin("https://hh.ru/", href)
            parsed = urlparse(url)
            match = _VACANCY.search(parsed.path)
            if (
                parsed.scheme == "https"
                and parsed.hostname in {"hh.ru", "www.hh.ru"}
                and match
            ):
                # Discard query parameters, tracking IDs and fragments.
                self.vacancy_urls.add(
                    f"https://hh.ru/vacancy/{match.group(1)}"
                )

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript", "svg"} and self._ignored:
            self._ignored -= 1
        if tag == "title":
            self._title = False
        if tag in {"p", "li", "div", "br", "h1", "h2", "h3", "tr", "article"}:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._ignored:
            return
        if self._title:
            self.title_parts.append(data)
        else:
            self.parts.append(data)


def _read(path: Path) -> tuple[str, str]:
    if path.suffix.lower() not in SUPPORTED:
        raise ValueError(
            "Expected an HTML, text or JSON snapshot (.html/.htm/.txt/.json)."
        )
    size = path.stat().st_size
    if size > MAX_BYTES:
        raise ValueError("Snapshot exceeds the 10 MiB size limit.")
    return path.suffix.lower(), path.read_text(encoding="utf-8-sig")


def extract(path: Path) -> dict:
    """Parse a local snapshot; returned data is potentially sensitive."""
    extension, raw = _read(Path(path))
    if extension == ".json":
        parsed = json.loads(raw)
        return {"format": "json", "data": parsed}
    if extension == ".txt":
        return {"format": "text", "text": raw}
    parser = _VisibleHTML()
    parser.feed(raw)
    text = "\n".join(
        " ".join(fragment.split())
        for fragment in "".join(parser.parts).splitlines()
        if fragment.strip()
    )
    return {
        "format": "html",
        "title": " ".join(" ".join(parser.title_parts).split()),
        "text": text,
        "vacancy_urls": sorted(parser.vacancy_urls),
    }


def inspect(path: Path) -> dict:
    """Report only metadata; avoid printing account contents by default."""
    result = extract(path)
    out: dict = {"format": result["format"], "filename": Path(path).name}
    if result["format"] == "html":
        out.update(
            title=result["title"],
            text_chars=len(result["text"]),
            vacancy_count=len(result["vacancy_urls"]),
        )
    elif result["format"] == "text":
        out["text_chars"] = len(result["text"])
    else:
        data = result["data"]
        out["root_type"] = type(data).__name__
        if isinstance(data, dict):
            out["top_level_keys"] = sorted(data.keys())
        elif isinstance(data, list):
            out["items"] = len(data)
    return out

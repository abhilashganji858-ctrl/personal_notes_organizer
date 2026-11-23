"""Import and export (JSON and CSV).

CSV is handled with Python's csv module, so commas, quotes and line breaks
inside notes are written and read correctly (RFC 4180).

Security note: spreadsheet programs run cells that start with = + - or @
as formulas. When exporting we put a ' in front of such cells, and we remove
it again on import so a round trip gives back exactly the same text.
"""

import csv
import io
import json

from .errors import ImportExportError

CSV_COLUMNS = ["title", "content", "tags", "pinned", "created_at"]
_FORMULA_STARTERS = "=+-@"
MAX_IMPORT_BYTES = 5 * 1024 * 1024  # refuse files bigger than 5 MB


def _needs_protection(text: str) -> bool:
    """True if the text, ignoring leading apostrophes, starts like a formula."""
    stripped = text.lstrip("'")
    return bool(stripped) and stripped[0] in _FORMULA_STARTERS


def _protect_cell(text: str) -> str:
    return "'" + text if _needs_protection(text) else text


def _unprotect_cell(text: str) -> str:
    if text[:1] == "'" and _needs_protection(text[1:]):
        return text[1:]
    return text


def notes_to_json(notes) -> str:
    return json.dumps([n.to_dict() for n in notes], indent=2, ensure_ascii=False)


def notes_to_csv(notes) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\r\n")
    writer.writerow(CSV_COLUMNS)
    for n in notes:
        writer.writerow([
            _protect_cell(n.title),
            _protect_cell(n.content),
            ";".join(n.tags),
            "yes" if n.pinned else "no",
            n.created_at,
        ])
    return buffer.getvalue()


def _check_size(text: str) -> None:
    if len(text.encode("utf-8")) > MAX_IMPORT_BYTES:
        raise ImportExportError("Import file is too large (limit is 5 MB).")


def parse_json(text: str) -> list:
    _check_size(text)
    try:
        data = json.loads(text)
    except json.JSONDecodeError as err:
        raise ImportExportError(f"Not valid JSON: {err}") from err
    if isinstance(data, dict):
        data = data.get("notes", [])
    if not isinstance(data, list):
        raise ImportExportError("JSON must be a list of notes.")
    return [item for item in data if isinstance(item, dict)]


def parse_csv(text: str) -> list:
    _check_size(text)
    reader = csv.DictReader(io.StringIO(text, newline=""))
    if not reader.fieldnames or "title" not in reader.fieldnames:
        raise ImportExportError("CSV needs a header row with at least a 'title' column.")
    items = []
    try:
        for row in reader:
            items.append({
                "title": _unprotect_cell(row.get("title") or ""),
                "content": _unprotect_cell(row.get("content") or ""),
                "tags": [t for t in (row.get("tags") or "").split(";") if t.strip()],
                "pinned": (row.get("pinned") or "").strip().lower() in ("yes", "true", "1"),
            })
    except csv.Error as err:
        raise ImportExportError(f"Could not read CSV: {err}") from err
    return items


def parse_file_text(text: str, filename: str) -> list:
    """Pick the right parser from the file extension."""
    name = filename.lower()
    if name.endswith(".json"):
        return parse_json(text)
    if name.endswith(".csv"):
        return parse_csv(text)
    raise ImportExportError("Only .json and .csv files can be imported.")

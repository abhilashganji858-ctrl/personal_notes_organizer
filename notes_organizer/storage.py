"""JSON file storage.

Writes are atomic: we write to a temp file and then swap it in with
os.replace, so a crash half way through can never leave a broken notes file.
"""

import json
import os
import shutil
import tempfile
from pathlib import Path

from .errors import StorageError
from .models import Note

SCHEMA_VERSION = 1


class JsonStorage:
    def __init__(self, path):
        self.path = Path(path)

    def load(self) -> list:
        if not self.path.exists():
            return []
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as err:
            backup = self._backup_corrupt_file()
            raise StorageError(
                f"{self.path.name} is corrupted ({err}). "
                f"A copy was saved as {backup.name}."
            ) from err
        except OSError as err:
            raise StorageError(f"Could not read {self.path}: {err}") from err

        items = raw.get("notes", []) if isinstance(raw, dict) else raw
        notes = []
        for item in items:
            try:
                notes.append(Note.from_dict(item))
            except (KeyError, TypeError, ValueError):
                continue  # skip a damaged record instead of losing everything
        return notes

    def save(self, notes: list) -> None:
        payload = {
            "version": SCHEMA_VERSION,
            "notes": [n.to_dict() for n in notes],
        }
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            fd, tmp_name = tempfile.mkstemp(
                dir=self.path.parent, prefix=".notes_", suffix=".tmp"
            )
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as tmp:
                    json.dump(payload, tmp, indent=2, ensure_ascii=False)
                os.replace(tmp_name, self.path)
            except Exception:
                if os.path.exists(tmp_name):
                    os.remove(tmp_name)
                raise
        except OSError as err:
            raise StorageError(f"Could not save notes to {self.path}: {err}") from err

    def _backup_corrupt_file(self) -> Path:
        backup = self.path.with_suffix(".corrupt.json")
        try:
            shutil.copy2(self.path, backup)
        except OSError:
            pass
        return backup

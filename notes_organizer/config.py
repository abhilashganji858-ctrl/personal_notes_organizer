"""Where the data lives. Shared by the CLI and the GUI."""

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"


def default_notes_path() -> Path:
    """NOTES_FILE environment variable wins, otherwise data/notes.json."""
    env_value = os.environ.get("NOTES_FILE")
    return Path(env_value) if env_value else DATA_DIR / "notes.json"


def build_service(path=None):
    """Create a NoteService for the given file (or the default one)."""
    from .logger import get_logger
    from .service import NoteService
    from .storage import JsonStorage

    path = Path(path) if path else default_notes_path()
    return NoteService(JsonStorage(path), get_logger(path.parent / "logs"))

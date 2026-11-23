# Personal Notes Organizer

StudentLife Hack - Project #102

Keep short notes, tag them, and find them again quickly. It is a **Python command line tool** (the required format) with an optional **Streamlit web interface** for easy demos.

- Storage: one JSON file (`data/notes.json`), written safely
- Import / export: CSV and JSON
- No third-party packages needed for the CLI, the tests or the core code
- Python 3.9 or newer

## Quick start (VS Code terminal)

```bash
# 1. open the folder in VS Code, then open a terminal

# 2. command line version - nothing to install
python main.py --help
python main.py add "Physics revision" -c "Chapter 4 formulas" -t exam,physics --pin
python main.py list
python main.py search physics
python main.py menu          # interactive menu, easiest for a live demo

# 3. optional: the Streamlit interface
python -m venv .venv
.venv\Scripts\activate       # Windows   (Mac/Linux: source .venv/bin/activate)
pip install -r requirements.txt
streamlit run app.py
```

In the web interface, press **Load sample notes** in the sidebar to get demo data in one click.

## Features

| Feature | CLI command | Streamlit page |
|---|---|---|
| Add a note (title, content, tags, pin) | `add` | Add Note |
| List with sorting (pinned first) | `list --sort title` | My Notes |
| View one note | `view 3` | My Notes (expander) |
| Edit, delete (with confirmation) | `edit`, `delete` | My Notes |
| Search by keyword | `search python` | My Notes |
| Filter by tag (any / all), date range, pinned | `search --tag a,b --all-tags --since 2026-01-01` | My Notes |
| Tag tools: list counts, add, remove, rename | `tags`, `tag-add`, `tag-remove`, `tag-rename` | My Notes / Dashboard |
| Statistics and charts | `stats` (text charts) | Dashboard |
| Export / import CSV and JSON | `export file.csv`, `import file.json` | Import / Export |
| Interactive menu | `menu` | - |

Use a different notes file with `--file other.json` or the `NOTES_FILE` environment variable.

## Project layout

```
main.py                 CLI entry point
app.py                  Streamlit interface
notes_organizer/
    models.py           Note dataclass
    validation.py       all input checks
    storage.py          JSON file storage (atomic writes)
    service.py          business logic - used by both CLI and GUI
    dataio.py           CSV / JSON import and export
    stats.py            summaries and text charts
    cli.py              argparse commands and the menu
    config.py, logger.py, errors.py, samples.py
tests/                  78 unit tests (standard library unittest)
docs/EVALUATION_FIXES.md   how this version answers the evaluation report
```

The CLI and the GUI only talk to `NoteService`, so both behave the same and the rules are tested once.

## Running the tests

```bash
python -m unittest discover -s tests -t . -v
```

(`pytest` also works if you have it installed.)

## Design notes

- **Validation** - titles 1-100 chars, content up to 10,000, up to 10 tags (letters, digits, `-`, `_`). Control characters are stripped. Failed edits never half-update a note.
- **Safe saving** - the file is written to a temp file and swapped in, so a crash cannot corrupt your notes. A corrupted file is backed up as `notes.corrupt.json` and reported clearly.
- **Safe CSV** - uses the `csv` module (commas, quotes and line breaks inside notes are fine). Cells starting with `= + - @` are prefixed with `'` on export so Excel cannot run them as formulas; import reverses this exactly.
- **Import limits** - files over 5 MB are refused; bad rows are skipped and reported, not fatal.
- **Logging** - actions are written to `data/logs/notes.log`.
- **Privacy** - everything stays on your computer. There is no network access and no login, because there is no server.

## Possible next steps

Note encryption, a trash/undo for deleted notes, markdown preview, reminders.

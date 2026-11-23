"""Command line interface.

Examples:
    python main.py add "Physics revision" -c "Chapter 4 formulas" -t exam,physics
    python main.py list
    python main.py search python --tag coding
    python main.py menu            # interactive menu
"""

import argparse
import sys
from pathlib import Path

from . import __version__, dataio, stats
from .config import build_service
from .errors import NotesError
from .service import SORT_OPTIONS


# ---------- printing helpers ----------

def format_note_line(note) -> str:
    star = "*" if note.pinned else " "
    tags = ",".join(note.tags) if note.tags else "-"
    return f"{star} [{note.id:>3}] {note.title[:35]:<35} {tags[:25]:<25} {note.created_at[:10]}"


def print_notes_table(notes) -> None:
    if not notes:
        print("No notes found.")
        return
    print(f"  {'ID':>5} {'Title':<35} {'Tags':<25} Created")
    print("  " + "-" * 76)
    for note in notes:
        print(format_note_line(note))
    print(f"\n{len(notes)} note(s). (* = pinned)")


def print_full_note(note) -> None:
    print("=" * 60)
    print(f"#{note.id}  {note.title}" + ("   [PINNED]" if note.pinned else ""))
    print(f"Tags:    {', '.join(note.tags) if note.tags else '-'}")
    print(f"Created: {note.created_at}    Updated: {note.updated_at}")
    print("-" * 60)
    print(note.content or "(no content)")
    print("=" * 60)


# ---------- command handlers ----------

def cmd_add(svc, args):
    note = svc.add(args.title, args.content, args.tags, args.pin)
    print(f"Added note #{note.id}: {note.title}")


def cmd_list(svc, args):
    print_notes_table(svc.list_notes(args.sort))


def cmd_view(svc, args):
    print_full_note(svc.get(args.id))


def cmd_edit(svc, args):
    svc.update(args.id, title=args.title, content=args.content, tags=args.tags)
    print(f"Updated note #{args.id}")


def cmd_delete(svc, args):
    note = svc.get(args.id)
    if not args.yes:
        answer = input(f"Delete '{note.title}'? (y/N): ").strip().lower()
        if answer != "y":
            print("Cancelled.")
            return
    svc.delete(args.id)
    print(f"Deleted note #{args.id}")


def cmd_search(svc, args):
    results = svc.search(
        keyword=args.keyword, tags=args.tag, match_all_tags=args.all_tags,
        since=args.since, until=args.until, pinned_only=args.pinned, sort_by=args.sort,
    )
    print_notes_table(results)


def cmd_pin(svc, args):
    note = svc.toggle_pin(args.id)
    print(f"Note #{note.id} is now {'pinned' if note.pinned else 'unpinned'}")


def cmd_tags(svc, args):
    counts = svc.tag_counts()
    if not counts:
        print("No tags yet.")
        return
    print(stats.text_bar_chart(counts))


def cmd_tag_add(svc, args):
    note = svc.add_tags(args.id, args.tags)
    print(f"Note #{note.id} tags: {', '.join(note.tags)}")


def cmd_tag_remove(svc, args):
    note = svc.remove_tags(args.id, args.tags)
    print(f"Note #{note.id} tags: {', '.join(note.tags) or '-'}")


def cmd_tag_rename(svc, args):
    changed = svc.rename_tag(args.old, args.new)
    print(f"Renamed '{args.old}' to '{args.new}' on {changed} note(s)")


def cmd_stats(svc, args):
    info = stats.summary(svc.list_notes())
    print("Summary")
    print("-------")
    for key, value in info.items():
        print(f"{key.replace('_', ' ').capitalize():<18}: {value}")
    print("\nNotes per tag")
    print(stats.text_bar_chart(svc.tag_counts()))
    print("\nNotes created in the last 7 days")
    print(stats.text_bar_chart(stats.notes_per_day(svc.list_notes())))


def cmd_export(svc, args):
    notes = svc.list_notes("oldest")
    out = Path(args.output)
    text = dataio.notes_to_csv(notes) if out.suffix.lower() == ".csv" else dataio.notes_to_json(notes)
    if out.suffix.lower() not in (".csv", ".json"):
        raise NotesError("Output file must end with .csv or .json")
    out.write_text(text, encoding="utf-8", newline="")
    print(f"Exported {len(notes)} note(s) to {out}")


def cmd_import(svc, args):
    path = Path(args.input)
    if not path.is_file():
        raise NotesError(f"File not found: {path}")
    text = path.read_text(encoding="utf-8-sig")
    items = dataio.parse_file_text(text, path.name)
    added, skipped = svc.add_many(items)
    print(f"Imported {added} note(s), skipped {len(skipped)}.")
    for message in skipped[:10]:
        print("  skipped", message)


def cmd_menu(svc, args):
    run_menu(svc)


# ---------- interactive menu ----------

MENU_TEXT = """
==== Personal Notes Organizer ====
 1. Add a note          6. Pin / unpin
 2. List notes          7. Show tag counts
 3. View a note         8. Statistics
 4. Edit a note         9. Export notes
 5. Delete a note      10. Import notes
11. Search               0. Exit
"""


def _ask_id(prompt="Note id: ") -> int:
    try:
        return int(input(prompt).strip())
    except ValueError:
        raise NotesError("Please type a number.") from None


def run_menu(svc) -> None:
    while True:
        print(MENU_TEXT)
        choice = input("Choose: ").strip()
        try:
            if choice == "0":
                print("Goodbye!")
                return
            elif choice == "1":
                title = input("Title: ")
                content = input("Content: ")
                tags = input("Tags (comma separated): ")
                note = svc.add(title, content, tags)
                print(f"Added note #{note.id}")
            elif choice == "2":
                print_notes_table(svc.list_notes())
            elif choice == "3":
                print_full_note(svc.get(_ask_id()))
            elif choice == "4":
                note = svc.get(_ask_id())
                print("Leave a field empty to keep it as it is.")
                title = input(f"Title [{note.title}]: ") or None
                content = input("New content: ") or None
                tags = input(f"Tags [{','.join(note.tags)}]: ") or None
                svc.update(note.id, title=title, content=content, tags=tags)
                print("Updated.")
            elif choice == "5":
                note = svc.get(_ask_id())
                if input(f"Delete '{note.title}'? (y/N): ").strip().lower() == "y":
                    svc.delete(note.id)
                    print("Deleted.")
            elif choice == "6":
                note = svc.toggle_pin(_ask_id())
                print("Pinned." if note.pinned else "Unpinned.")
            elif choice == "7":
                cmd_tags(svc, None)
            elif choice == "8":
                cmd_stats(svc, None)
            elif choice == "9":
                args = argparse.Namespace(output=input("Output file (.csv or .json): ").strip())
                cmd_export(svc, args)
            elif choice == "10":
                args = argparse.Namespace(input=input("Input file (.csv or .json): ").strip())
                cmd_import(svc, args)
            elif choice == "11":
                keyword = input("Keyword (optional): ")
                tag = input("Tag(s) (optional): ")
                print_notes_table(svc.search(keyword=keyword, tags=tag or None))
            else:
                print("Please pick a number from the menu.")
        except NotesError as err:
            print(f"Error: {err}")
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            return


# ---------- argument parser ----------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="notes", description="Personal Notes Organizer - keep, tag and search your notes."
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--file", help="notes file to use (default: data/notes.json)")
    sub = parser.add_subparsers(dest="command")

    p = sub.add_parser("add", help="add a new note")
    p.add_argument("title")
    p.add_argument("-c", "--content", default="")
    p.add_argument("-t", "--tags", default="", help="comma separated tags")
    p.add_argument("--pin", action="store_true", help="pin the note")
    p.set_defaults(func=cmd_add)

    p = sub.add_parser("list", help="list all notes")
    p.add_argument("--sort", choices=SORT_OPTIONS, default="newest")
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("view", help="show one note in full")
    p.add_argument("id", type=int)
    p.set_defaults(func=cmd_view)

    p = sub.add_parser("edit", help="edit a note (only the given fields change)")
    p.add_argument("id", type=int)
    p.add_argument("--title")
    p.add_argument("-c", "--content")
    p.add_argument("-t", "--tags", help="replaces all tags")
    p.set_defaults(func=cmd_edit)

    p = sub.add_parser("delete", help="delete a note")
    p.add_argument("id", type=int)
    p.add_argument("-y", "--yes", action="store_true", help="skip the confirmation")
    p.set_defaults(func=cmd_delete)

    p = sub.add_parser("search", help="search by keyword, tag and date")
    p.add_argument("keyword", nargs="?", default="")
    p.add_argument("--tag", help="comma separated tags")
    p.add_argument("--all-tags", action="store_true", help="note must have every tag")
    p.add_argument("--since", help="created on/after YYYY-MM-DD")
    p.add_argument("--until", help="created on/before YYYY-MM-DD")
    p.add_argument("--pinned", action="store_true", help="only pinned notes")
    p.add_argument("--sort", choices=SORT_OPTIONS, default="newest")
    p.set_defaults(func=cmd_search)

    p = sub.add_parser("pin", help="pin or unpin a note")
    p.add_argument("id", type=int)
    p.set_defaults(func=cmd_pin)

    p = sub.add_parser("tags", help="show every tag with a count chart")
    p.set_defaults(func=cmd_tags)

    p = sub.add_parser("tag-add", help="add tags to a note")
    p.add_argument("id", type=int)
    p.add_argument("tags", help="comma separated")
    p.set_defaults(func=cmd_tag_add)

    p = sub.add_parser("tag-remove", help="remove tags from a note")
    p.add_argument("id", type=int)
    p.add_argument("tags", help="comma separated")
    p.set_defaults(func=cmd_tag_remove)

    p = sub.add_parser("tag-rename", help="rename a tag on all notes")
    p.add_argument("old")
    p.add_argument("new")
    p.set_defaults(func=cmd_tag_rename)

    p = sub.add_parser("stats", help="summary numbers and text charts")
    p.set_defaults(func=cmd_stats)

    p = sub.add_parser("export", help="export notes to .csv or .json")
    p.add_argument("output")
    p.set_defaults(func=cmd_export)

    p = sub.add_parser("import", help="import notes from .csv or .json")
    p.add_argument("input")
    p.set_defaults(func=cmd_import)

    p = sub.add_parser("menu", help="interactive menu")
    p.set_defaults(func=cmd_menu)

    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return 0
    try:
        svc = build_service(args.file)
        args.func(svc, args)
        return 0
    except NotesError as err:
        print(f"Error: {err}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nCancelled.")
        return 130


if __name__ == "__main__":
    sys.exit(main())

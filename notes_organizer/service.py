"""Business logic: add, edit, delete, search and organise notes.

Both the CLI and the Streamlit app talk to this class only, so the rules
live in one place and are easy to test.
"""

from collections import Counter

from .errors import NoteNotFoundError, ValidationError
from .logger import get_logger
from .models import Note, now_string
from .validation import (
    validate_content,
    validate_date,
    validate_tags,
    validate_title,
    normalize_tag,
)

SORT_OPTIONS = ("newest", "oldest", "title", "updated")


class NoteService:
    def __init__(self, storage, logger=None):
        self.storage = storage
        self.log = logger or get_logger()
        self._notes = self.storage.load()

    # ---------- basic CRUD ----------

    def _next_id(self) -> int:
        return max((n.id for n in self._notes), default=0) + 1

    def _save(self) -> None:
        self.storage.save(self._notes)

    def add(self, title, content="", tags=None, pinned=False) -> Note:
        note = Note(
            id=self._next_id(),
            title=validate_title(title),
            content=validate_content(content),
            tags=validate_tags(tags),
            pinned=bool(pinned),
        )
        self._notes.append(note)
        self._save()
        self.log.info("added note %s", note.id)
        return note

    def get(self, note_id: int) -> Note:
        for note in self._notes:
            if note.id == note_id:
                return note
        raise NoteNotFoundError(f"No note with id {note_id}.")

    def update(self, note_id, title=None, content=None, tags=None, pinned=None) -> Note:
        note = self.get(note_id)
        # validate everything first so a bad field cannot half-update the note
        new_title = validate_title(title) if title is not None else note.title
        new_content = validate_content(content) if content is not None else note.content
        new_tags = validate_tags(tags) if tags is not None else note.tags

        note.title, note.content, note.tags = new_title, new_content, new_tags
        if pinned is not None:
            note.pinned = bool(pinned)
        note.updated_at = now_string()
        self._save()
        self.log.info("updated note %s", note_id)
        return note

    def delete(self, note_id: int) -> Note:
        note = self.get(note_id)
        self._notes.remove(note)
        self._save()
        self.log.info("deleted note %s", note_id)
        return note

    def toggle_pin(self, note_id: int) -> Note:
        note = self.get(note_id)
        return self.update(note_id, pinned=not note.pinned)

    # ---------- listing and searching ----------

    @staticmethod
    def _sort(notes, sort_by):
        if sort_by not in SORT_OPTIONS:
            raise ValidationError(f"Sort must be one of: {', '.join(SORT_OPTIONS)}.")
        if sort_by == "title":
            ordered = sorted(notes, key=lambda n: n.title.lower())
        elif sort_by == "oldest":
            ordered = sorted(notes, key=lambda n: (n.created_at, n.id))
        elif sort_by == "updated":
            ordered = sorted(notes, key=lambda n: n.updated_at, reverse=True)
        else:  # newest
            ordered = sorted(notes, key=lambda n: (n.created_at, n.id), reverse=True)
        # pinned notes always float to the top (sort is stable)
        return sorted(ordered, key=lambda n: not n.pinned)

    def list_notes(self, sort_by="newest") -> list:
        return self._sort(self._notes, sort_by)

    def search(self, keyword="", tags=None, match_all_tags=False,
               since=None, until=None, pinned_only=False, sort_by="newest") -> list:
        """Filter notes. Every filter is optional and they combine with AND."""
        results = list(self._notes)

        keyword = (keyword or "").strip().lower()
        if keyword:
            results = [
                n for n in results
                if keyword in n.title.lower()
                or keyword in n.content.lower()
                or any(keyword in t for t in n.tags)
            ]

        wanted = validate_tags(tags) if tags else []
        if wanted:
            if match_all_tags:
                results = [n for n in results if set(wanted) <= set(n.tags)]
            else:
                results = [n for n in results if set(wanted) & set(n.tags)]

        if since:
            start = validate_date(since)
            results = [n for n in results if n.created_at[:10] >= start]
        if until:
            end = validate_date(until)
            results = [n for n in results if n.created_at[:10] <= end]

        if pinned_only:
            results = [n for n in results if n.pinned]

        return self._sort(results, sort_by)

    # ---------- tags ----------

    def tag_counts(self) -> dict:
        counter = Counter(tag for n in self._notes for tag in n.tags)
        return dict(sorted(counter.items(), key=lambda kv: (-kv[1], kv[0])))

    def add_tags(self, note_id, tags) -> Note:
        note = self.get(note_id)
        return self.update(note_id, tags=note.tags + validate_tags(tags))

    def remove_tags(self, note_id, tags) -> Note:
        note = self.get(note_id)
        to_remove = set(validate_tags(tags))
        return self.update(note_id, tags=[t for t in note.tags if t not in to_remove])

    def rename_tag(self, old, new) -> int:
        """Rename a tag everywhere. Returns how many notes changed."""
        old, new = normalize_tag(old), normalize_tag(new)
        changed = 0
        for note in self._notes:
            if old in note.tags:
                note.tags = sorted({new if t == old else t for t in note.tags})
                note.updated_at = now_string()
                changed += 1
        if changed:
            self._save()
            self.log.info("renamed tag %s -> %s on %d notes", old, new, changed)
        return changed

    # ---------- bulk helpers used by import ----------

    def add_many(self, items) -> tuple:
        """Add many notes (dicts). Returns (added, skipped_messages)."""
        added, skipped = 0, []
        for position, item in enumerate(items, start=1):
            try:
                note = Note(
                    id=self._next_id(),
                    title=validate_title(item.get("title")),
                    content=validate_content(item.get("content", "")),
                    tags=validate_tags(item.get("tags")),
                    pinned=bool(item.get("pinned", False)),
                )
            except ValidationError as err:
                skipped.append(f"row {position}: {err}")
                continue
            self._notes.append(note)
            added += 1
        if added:
            self._save()
            self.log.info("imported %d notes (%d skipped)", added, len(skipped))
        return added, skipped

    def __len__(self):
        return len(self._notes)

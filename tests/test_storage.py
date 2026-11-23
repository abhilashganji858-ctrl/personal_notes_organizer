import json
import tempfile
import unittest
from pathlib import Path

from notes_organizer.errors import StorageError
from notes_organizer.models import Note
from notes_organizer.storage import JsonStorage


class StorageTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.path = Path(self._tmp.name) / "sub" / "notes.json"
        self.storage = JsonStorage(self.path)

    def test_missing_file_gives_empty_list(self):
        self.assertEqual(self.storage.load(), [])

    def test_save_then_load_round_trip(self):
        notes = [Note(1, "A", "body", ["x"], True), Note(2, "B", "", [])]
        self.storage.save(notes)
        loaded = self.storage.load()
        self.assertEqual([n.to_dict() for n in loaded], [n.to_dict() for n in notes])

    def test_unicode_survives(self):
        self.storage.save([Note(1, "Café ☕", "नमस्ते")])
        self.assertEqual(self.storage.load()[0].content, "नमस्ते")

    def test_corrupt_file_raises_and_keeps_a_backup(self):
        self.path.parent.mkdir(parents=True)
        self.path.write_text("{ not json", encoding="utf-8")
        with self.assertRaises(StorageError):
            self.storage.load()
        self.assertTrue(self.path.with_suffix(".corrupt.json").exists())

    def test_damaged_record_is_skipped(self):
        self.path.parent.mkdir(parents=True)
        data = {"notes": [{"id": 1, "title": "ok"}, {"title": "no id"}]}
        self.path.write_text(json.dumps(data), encoding="utf-8")
        self.assertEqual([n.title for n in self.storage.load()], ["ok"])

    def test_no_temp_files_left_behind(self):
        self.storage.save([Note(1, "A", "")])
        leftovers = [p.name for p in self.path.parent.iterdir() if p.name.endswith(".tmp")]
        self.assertEqual(leftovers, [])


if __name__ == "__main__":
    unittest.main()

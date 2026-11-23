import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from notes_organizer.cli import main


class CliTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dir = Path(self._tmp.name)
        self.file = str(self.dir / "notes.json")

    def run_cli(self, *args, user_input=None):
        out, err = io.StringIO(), io.StringIO()
        argv = ["--file", self.file, *args]
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            if user_input is None:
                code = main(argv)
            else:
                with mock.patch("builtins.input", side_effect=user_input):
                    code = main(argv)
        return code, out.getvalue(), err.getvalue()

    def test_add_then_list(self):
        code, out, _ = self.run_cli("add", "Study plan", "-c", "maths", "-t", "exam")
        self.assertEqual(code, 0)
        self.assertIn("Added note #1", out)
        _, out, _ = self.run_cli("list")
        self.assertIn("Study plan", out)

    def test_invalid_input_gives_error_and_exit_code_1(self):
        code, _, err = self.run_cli("add", "   ")
        self.assertEqual(code, 1)
        self.assertIn("Title cannot be empty", err)

    def test_view_missing_note(self):
        code, _, err = self.run_cli("view", "7")
        self.assertEqual(code, 1)
        self.assertIn("No note with id 7", err)

    def test_search_by_tag(self):
        self.run_cli("add", "A", "-t", "x")
        self.run_cli("add", "B", "-t", "y")
        _, out, _ = self.run_cli("search", "--tag", "y")
        self.assertIn("B", out)
        self.assertNotIn(" A ", out)

    def test_edit_and_pin(self):
        self.run_cli("add", "Old")
        self.run_cli("edit", "1", "--title", "New")
        self.run_cli("pin", "1")
        _, out, _ = self.run_cli("view", "1")
        self.assertIn("New", out)
        self.assertIn("PINNED", out)

    def test_delete_asks_for_confirmation(self):
        self.run_cli("add", "Keep me")
        _, out, _ = self.run_cli("delete", "1", user_input=["n"])
        self.assertIn("Cancelled", out)
        _, out, _ = self.run_cli("delete", "1", "--yes")
        self.assertIn("Deleted", out)

    def test_tag_commands(self):
        self.run_cli("add", "A", "-t", "x")
        self.run_cli("tag-add", "1", "y")
        self.run_cli("tag-rename", "x", "z")
        _, out, _ = self.run_cli("tags")
        self.assertIn("z", out)
        self.assertIn("y", out)

    def test_export_and_import(self):
        self.run_cli("add", "Move me", "-c", "hello, world", "-t", "t1")
        target = str(self.dir / "backup.csv")
        code, _, _ = self.run_cli("export", target)
        self.assertEqual(code, 0)

        self.file = str(self.dir / "second.json")
        code, out, _ = self.run_cli("import", target)
        self.assertEqual(code, 0)
        self.assertIn("Imported 1", out)

    def test_export_rejects_unknown_extension(self):
        code, _, err = self.run_cli("export", str(self.dir / "notes.txt"))
        self.assertEqual(code, 1)
        self.assertIn(".csv or .json", err)

    def test_import_missing_file(self):
        code, _, err = self.run_cli("import", str(self.dir / "nope.csv"))
        self.assertEqual(code, 1)
        self.assertIn("File not found", err)

    def test_stats_runs_on_empty_store(self):
        code, out, _ = self.run_cli("stats")
        self.assertEqual(code, 0)
        self.assertIn("Total notes", out)

    def test_menu_add_list_exit(self):
        inputs = ["1", "Menu note", "from the menu", "demo", "2", "0"]
        code, out, _ = self.run_cli("menu", user_input=inputs)
        self.assertEqual(code, 0)
        self.assertIn("Menu note", out)
        self.assertIn("Goodbye", out)

    def test_menu_survives_bad_input(self):
        code, out, _ = self.run_cli("menu", user_input=["3", "abc", "99", "0"])
        self.assertEqual(code, 0)
        self.assertIn("Please type a number", out)

    def test_corrupt_file_reports_error(self):
        Path(self.file).write_text("{broken", encoding="utf-8")
        code, _, err = self.run_cli("list")
        self.assertEqual(code, 1)
        self.assertIn("corrupted", err)


if __name__ == "__main__":
    unittest.main()

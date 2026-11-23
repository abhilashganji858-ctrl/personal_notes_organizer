import unittest

from notes_organizer import dataio
from notes_organizer.errors import ImportExportError
from tests.helpers import TempServiceTestCase


class CsvTests(TempServiceTestCase):
    def test_round_trip_with_awkward_text(self):
        self.svc.add('Quote "test"', 'line one\nline two, with comma and "quotes"', "a,b", True)
        csv_text = dataio.notes_to_csv(self.svc.list_notes())
        items = dataio.parse_csv(csv_text)
        self.assertEqual(items[0]["title"], 'Quote "test"')
        self.assertEqual(items[0]["content"], 'line one\nline two, with comma and "quotes"')
        self.assertEqual(items[0]["tags"], ["a", "b"])
        self.assertTrue(items[0]["pinned"])

    def test_formula_cells_are_neutralised_on_export(self):
        self.svc.add("=HYPERLINK(\"http://evil\")", "+1+1")
        csv_text = dataio.notes_to_csv(self.svc.list_notes())
        self.assertIn("'=HYPERLINK", csv_text)
        self.assertIn("'+1+1", csv_text)

    def test_formula_protection_round_trips_exactly(self):
        for title in ["=SUM(A1)", "@cmd", "-5", "'=already quoted", "''-x", "normal", "'quote only", ""]:
            self.assertEqual(dataio._unprotect_cell(dataio._protect_cell(title)), title)

    def test_missing_title_column(self):
        with self.assertRaises(ImportExportError):
            dataio.parse_csv("name,content\nx,y\n")

    def test_empty_csv(self):
        with self.assertRaises(ImportExportError):
            dataio.parse_csv("")

    def test_size_limit(self):
        with self.assertRaises(ImportExportError):
            dataio.parse_csv("title\n" + "x" * (dataio.MAX_IMPORT_BYTES + 1))


class JsonTests(TempServiceTestCase):
    def test_round_trip(self):
        self.svc.add("A", "body", "x")
        items = dataio.parse_json(dataio.notes_to_json(self.svc.list_notes()))
        self.assertEqual(items[0]["title"], "A")

    def test_accepts_wrapper_object(self):
        self.assertEqual(len(dataio.parse_json('{"notes": [{"title": "a"}]}')), 1)

    def test_invalid_json(self):
        with self.assertRaises(ImportExportError):
            dataio.parse_json("{oops")

    def test_wrong_shape(self):
        with self.assertRaises(ImportExportError):
            dataio.parse_json('"just a string"')

    def test_non_dict_items_ignored(self):
        self.assertEqual(dataio.parse_json('[1, "x", {"title": "ok"}]'), [{"title": "ok"}])


class DispatchTests(unittest.TestCase):
    def test_unknown_extension(self):
        with self.assertRaises(ImportExportError):
            dataio.parse_file_text("x", "notes.txt")


class ImportIntoServiceTests(TempServiceTestCase):
    def test_full_export_import_cycle(self):
        self.svc.add("One", "first", "a", True)
        self.svc.add("Two", "second\nline", "b")
        csv_text = dataio.notes_to_csv(self.svc.list_notes("oldest"))

        fresh = type(self.svc)(type(self.svc.storage)(self.path.parent / "other.json"))
        added, skipped = fresh.add_many(dataio.parse_csv(csv_text))
        self.assertEqual((added, skipped), (2, []))
        self.assertEqual(fresh.get(2).content, "second\nline")


if __name__ == "__main__":
    unittest.main()

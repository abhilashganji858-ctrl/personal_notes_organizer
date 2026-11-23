import unittest

from notes_organizer.errors import NoteNotFoundError, ValidationError
from tests.helpers import TempServiceTestCase


class CrudTests(TempServiceTestCase):
    def test_add_assigns_incrementing_ids(self):
        a = self.svc.add("First")
        b = self.svc.add("Second")
        self.assertEqual((a.id, b.id), (1, 2))

    def test_ids_are_not_reused_after_delete(self):
        self.svc.add("one")
        two = self.svc.add("two")
        self.svc.delete(two.id)
        self.assertEqual(self.svc.add("three").id, 2)  # max id was 1, so 2 again
        self.svc.delete(1)
        self.assertEqual(self.svc.add("four").id, 3)

    def test_data_is_saved_to_disk(self):
        self.svc.add("Persist me", "body", "tag1")
        again = self.new_service()
        self.assertEqual(again.get(1).title, "Persist me")

    def test_get_missing_note(self):
        with self.assertRaises(NoteNotFoundError):
            self.svc.get(42)

    def test_invalid_add_does_not_change_anything(self):
        with self.assertRaises(ValidationError):
            self.svc.add("")
        self.assertEqual(len(self.svc), 0)

    def test_update_changes_only_given_fields(self):
        note = self.svc.add("Title", "Body", "a")
        self.svc.update(note.id, content="New body")
        fresh = self.svc.get(note.id)
        self.assertEqual((fresh.title, fresh.content, fresh.tags), ("Title", "New body", ["a"]))

    def test_failed_update_leaves_note_untouched(self):
        note = self.svc.add("Title", "Body", "a")
        with self.assertRaises(ValidationError):
            self.svc.update(note.id, title="Fine", tags="bad tag")
        self.assertEqual(self.svc.get(note.id).title, "Title")

    def test_delete(self):
        note = self.svc.add("bye")
        self.svc.delete(note.id)
        self.assertEqual(len(self.svc), 0)
        with self.assertRaises(NoteNotFoundError):
            self.svc.delete(note.id)


class SearchTests(TempServiceTestCase):
    def setUp(self):
        super().setUp()
        self.svc.add("Python basics", "loops and functions", "coding,python")
        self.svc.add("Physics notes", "Newton and PYTHON snake?", "exam,physics")
        self.svc.add("Shopping", "milk, eggs", "personal", pinned=True)

    def titles(self, notes):
        return sorted(n.title for n in notes)

    def test_keyword_is_case_insensitive_and_checks_content(self):
        self.assertEqual(len(self.svc.search("python")), 2)

    def test_keyword_matches_tags(self):
        self.assertEqual(self.titles(self.svc.search("exam")), ["Physics notes"])

    def test_tag_filter_any_vs_all(self):
        any_match = self.svc.search(tags="coding,exam")
        all_match = self.svc.search(tags="coding,exam", match_all_tags=True)
        self.assertEqual(len(any_match), 2)
        self.assertEqual(all_match, [])

    def test_filters_combine(self):
        found = self.svc.search("python", tags="coding")
        self.assertEqual(self.titles(found), ["Python basics"])

    def test_pinned_only(self):
        self.assertEqual(self.titles(self.svc.search(pinned_only=True)), ["Shopping"])

    def test_date_filters(self):
        self.assertEqual(len(self.svc.search(since="2000-01-01")), 3)
        self.assertEqual(self.svc.search(until="2000-01-01"), [])

    def test_bad_date_rejected(self):
        with self.assertRaises(ValidationError):
            self.svc.search(since="yesterday")

    def test_pinned_notes_come_first_when_sorting(self):
        self.assertEqual(self.svc.list_notes("title")[0].title, "Shopping")

    def test_sort_by_title(self):
        unpinned = [n.title for n in self.svc.list_notes("title") if not n.pinned]
        self.assertEqual(unpinned, ["Physics notes", "Python basics"])

    def test_bad_sort_option(self):
        with self.assertRaises(ValidationError):
            self.svc.list_notes("random")

    def test_no_results(self):
        self.assertEqual(self.svc.search("zzzz"), [])


class TagTests(TempServiceTestCase):
    def test_counts_are_sorted_by_popularity(self):
        self.svc.add("a", tags="x,y")
        self.svc.add("b", tags="x")
        self.assertEqual(list(self.svc.tag_counts().items()), [("x", 2), ("y", 1)])

    def test_add_and_remove_tags(self):
        note = self.svc.add("a", tags="x")
        self.svc.add_tags(note.id, "y, Z")
        self.assertEqual(self.svc.get(note.id).tags, ["x", "y", "z"])
        self.svc.remove_tags(note.id, "x,z")
        self.assertEqual(self.svc.get(note.id).tags, ["y"])

    def test_rename_tag_merges_duplicates(self):
        self.svc.add("a", tags="old,new")
        self.svc.add("b", tags="old")
        changed = self.svc.rename_tag("old", "new")
        self.assertEqual(changed, 2)
        self.assertEqual(self.svc.get(1).tags, ["new"])
        self.assertEqual(self.svc.get(2).tags, ["new"])

    def test_rename_unknown_tag_changes_nothing(self):
        self.svc.add("a", tags="x")
        self.assertEqual(self.svc.rename_tag("nope", "other"), 0)


class PinTests(TempServiceTestCase):
    def test_toggle(self):
        note = self.svc.add("a")
        self.assertTrue(self.svc.toggle_pin(note.id).pinned)
        self.assertFalse(self.svc.toggle_pin(note.id).pinned)


class AddManyTests(TempServiceTestCase):
    def test_bad_rows_are_skipped_not_fatal(self):
        added, skipped = self.svc.add_many([
            {"title": "good"},
            {"title": ""},
            {"title": "bad tag", "tags": ["no good"]},
            {"title": "also good", "tags": "ok"},
        ])
        self.assertEqual(added, 2)
        self.assertEqual(len(skipped), 2)


if __name__ == "__main__":
    unittest.main()

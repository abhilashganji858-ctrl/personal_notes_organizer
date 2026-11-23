import unittest

from notes_organizer import validation as v
from notes_organizer.errors import ValidationError


class TitleTests(unittest.TestCase):
    def test_valid_title_is_trimmed(self):
        self.assertEqual(v.validate_title("  Hello  "), "Hello")

    def test_empty_title_rejected(self):
        for bad in ("", "   "):
            with self.assertRaises(ValidationError):
                v.validate_title(bad)

    def test_non_text_title_rejected(self):
        with self.assertRaises(ValidationError):
            v.validate_title(123)

    def test_multiline_title_rejected(self):
        with self.assertRaises(ValidationError):
            v.validate_title("a\nb")

    def test_too_long_title_rejected(self):
        with self.assertRaises(ValidationError):
            v.validate_title("x" * (v.MAX_TITLE + 1))

    def test_control_characters_removed(self):
        self.assertEqual(v.validate_title("Hi\x00there"), "Hithere")


class ContentTests(unittest.TestCase):
    def test_none_becomes_empty(self):
        self.assertEqual(v.validate_content(None), "")

    def test_newlines_are_kept(self):
        self.assertEqual(v.validate_content("a\nb"), "a\nb")

    def test_too_long_rejected(self):
        with self.assertRaises(ValidationError):
            v.validate_content("x" * (v.MAX_CONTENT + 1))


class TagTests(unittest.TestCase):
    def test_normalise(self):
        self.assertEqual(v.normalize_tag("  #Exam "), "exam")

    def test_comma_string_is_split_deduped_and_sorted(self):
        self.assertEqual(v.validate_tags("Zoo, apple, ZOO"), ["apple", "zoo"])

    def test_invalid_characters_rejected(self):
        for bad in ("has space", "semi;colon", "<b>", "-start"):
            with self.assertRaises(ValidationError, msg=bad):
                v.normalize_tag(bad)

    def test_too_many_tags_rejected(self):
        with self.assertRaises(ValidationError):
            v.validate_tags([f"t{i}" for i in range(v.MAX_TAGS + 1)])

    def test_empty_inputs(self):
        self.assertEqual(v.validate_tags(None), [])
        self.assertEqual(v.validate_tags(""), [])


class DateTests(unittest.TestCase):
    def test_good_and_bad_dates(self):
        self.assertEqual(v.validate_date("2025-05-22"), "2025-05-22")
        for bad in ("22-05-2025", "2025-13-01", "tomorrow", None):
            with self.assertRaises(ValidationError, msg=str(bad)):
                v.validate_date(bad)


if __name__ == "__main__":
    unittest.main()

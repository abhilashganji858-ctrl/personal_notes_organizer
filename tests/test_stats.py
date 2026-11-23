import unittest

from notes_organizer import stats
from tests.helpers import TempServiceTestCase


class ChartTests(unittest.TestCase):
    def test_empty_chart(self):
        self.assertIn("nothing", stats.text_bar_chart({}))

    def test_longest_bar_matches_width(self):
        chart = stats.text_bar_chart({"a": 10, "b": 5}, width=20)
        lines = chart.splitlines()
        self.assertEqual(lines[0].count("#"), 20)
        self.assertEqual(lines[1].count("#"), 10)

    def test_zero_value_has_no_bar(self):
        chart = stats.text_bar_chart({"a": 3, "b": 0})
        self.assertEqual(chart.splitlines()[1].count("#"), 0)


class SummaryTests(TempServiceTestCase):
    def test_summary_numbers(self):
        self.svc.add("a", "one two three", "x", pinned=True)
        self.svc.add("b", "four", "")
        info = stats.summary(self.svc.list_notes())
        self.assertEqual(info["total_notes"], 2)
        self.assertEqual(info["pinned_notes"], 1)
        self.assertEqual(info["total_words"], 4)
        self.assertEqual(info["untagged_notes"], 1)

    def test_notes_per_day_has_seven_days_and_counts_today(self):
        self.svc.add("a")
        per_day = stats.notes_per_day(self.svc.list_notes())
        self.assertEqual(len(per_day), 7)
        self.assertEqual(list(per_day.values())[-1], 1)


if __name__ == "__main__":
    unittest.main()

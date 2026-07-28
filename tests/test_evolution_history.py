import os
import tempfile
import unittest

from evolution_history import EvolutionHistory
try:
    from tests.test_helpers import safe_remove
except ImportError:
    from test_helpers import safe_remove


class EvolutionHistoryTests(unittest.TestCase):
    def setUp(self):
        handle = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        handle.close()
        self.db_path = handle.name
        self.hist = EvolutionHistory(self.db_path)

    def tearDown(self):
        safe_remove(self.db_path)

    def test_records_and_lists_oldest_first(self):
        self.hist.record(3)
        self.hist.record(7)
        series = self.hist.list()
        self.assertEqual([p["records_total"] for p in series], [3, 7])

    def test_record_if_changed_dedupes_identical_totals(self):
        self.assertIsNotNone(self.hist.record_if_changed(5))
        # same total again -> no new row
        self.assertIsNone(self.hist.record_if_changed(5))
        # a different total -> recorded
        self.assertIsNotNone(self.hist.record_if_changed(9))
        self.assertEqual(len(self.hist.list()), 2)

    def test_growth_summary(self):
        # empty until the first point
        empty = self.hist.growth()
        self.assertEqual(empty["points"], 0)
        self.assertIsNone(empty["first"])
        for total in (2, 5, 11):
            self.hist.record_if_changed(total)
        g = self.hist.growth()
        self.assertEqual(g["points"], 3)
        self.assertEqual(g["first"], 2)
        self.assertEqual(g["latest"], 11)
        self.assertEqual(g["gain"], 9)

    def test_limit_returns_the_latest_points_oldest_first(self):
        for total in (1, 2, 3, 4):
            self.hist.record_if_changed(total)
        recent = self.hist.list(limit=2)
        self.assertEqual([p["records_total"] for p in recent], [3, 4])


if __name__ == "__main__":
    unittest.main()

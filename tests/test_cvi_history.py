"""Tests for cvi_history.py — CVI trend points persistence.

Covers:
  - record() and list() in oldest-first chronological order
  - list(limit=N) returns most recent points in chronological order
  - record_if_changed() suppresses duplicate identical snapshots
  - Series scoping by actor (actor-specific vs platform default)
  - list() on empty history returns empty list
  - record() returns dictionary with timestamp and record ID
"""
import os
import tempfile
import unittest

from cvi_history import CviHistory
try:
    from tests.test_helpers import safe_remove
except ImportError:
    from test_helpers import safe_remove


def snap(cvi, samples, mean=0.8, held=0.0):
    return {"cvi": cvi, "mean_confidence": mean, "held_ratio": held, "samples": samples}


class CviHistoryTests(unittest.TestCase):

    def setUp(self):
        handle = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        handle.close()
        self.db_path = handle.name
        self.history = CviHistory(self.db_path)

    def tearDown(self):
        safe_remove(self.db_path)

    def test_record_and_list_oldest_first(self):
        self.history.record(snap(0.5, 1))
        self.history.record(snap(0.7, 2))
        series = self.history.list()
        self.assertEqual([p["cvi"] for p in series], [0.5, 0.7])

    def test_limit_returns_most_recent_in_order(self):
        for i in range(5):
            self.history.record(snap(0.1 * i, i))
        recent = self.history.list(limit=2)
        self.assertEqual([p["samples"] for p in recent], [3, 4])

    def test_record_if_changed_skips_identical(self):
        self.assertIsNotNone(self.history.record_if_changed(snap(0.5, 1)))
        self.assertIsNone(self.history.record_if_changed(snap(0.5, 1)))  # unchanged
        self.assertIsNotNone(self.history.record_if_changed(snap(0.6, 2)))  # moved
        self.assertEqual(len(self.history.list()), 2)

    def test_series_are_scoped_by_actor(self):
        self.history.record(snap(0.9, 1), actor="alice")
        self.history.record(snap(0.4, 1), actor="bob")
        self.assertEqual(len(self.history.list(actor="alice")), 1)
        self.assertEqual(self.history.list(actor="alice")[0]["cvi"], 0.9)
        self.assertEqual(self.history.list()[:], [])  # platform series empty

    def test_empty_history_list(self):
        self.assertEqual(self.history.list(), [])

    def test_record_if_changed_scoped_by_actor(self):
        self.assertIsNotNone(self.history.record_if_changed(snap(0.5, 1), actor="alice"))
        self.assertIsNone(self.history.record_if_changed(snap(0.5, 1), actor="alice"))
        self.assertIsNotNone(self.history.record_if_changed(snap(0.5, 1), actor="bob"))
        self.assertEqual(len(self.history.list(actor="alice")), 1)
        self.assertEqual(len(self.history.list(actor="bob")), 1)

    def test_record_returns_dict_with_id_and_created_at(self):
        rec = self.history.record(snap(0.85, 10))
        self.assertIn("id", rec)
        self.assertIn("created_at", rec)
        self.assertEqual(rec["cvi"], 0.85)


if __name__ == "__main__":
    unittest.main()



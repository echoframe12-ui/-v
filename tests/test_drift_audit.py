"""Tests for DriftAuditLog — persistent, append-only drift audit history.

Covers:
  - Record intact and broken reports
  - list() is newest-first with optional limit
  - latest() returns most recent or None on empty
  - Empty log returns empty list
  - id is autoincremented
  - checked_at is a non-empty ISO timestamp string
  - broken_at=None stored and returned as None
  - record() returns all required keys
  - Persistence across two connections to the same db path
"""
import os
import tempfile
import unittest

from drift_audit import DriftAuditLog
try:
    from tests.test_helpers import safe_remove
except ImportError:
    from test_helpers import safe_remove


class DriftAuditLogTests(unittest.TestCase):
    def setUp(self):
        handle = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        handle.close()
        self.db_path = handle.name
        self.log = DriftAuditLog(self.db_path)

    def tearDown(self):
        safe_remove(self.db_path)

    def test_records_an_intact_report(self):
        entry = self.log.record({"intact": True, "trustworthy": True, "length": 3, "broken_at": None})
        self.assertEqual(entry["id"], 1)
        self.assertTrue(entry["intact"])
        self.assertTrue(entry["trustworthy"])
        self.assertEqual(entry["length"], 3)

    def test_records_a_broken_report(self):
        entry = self.log.record({"intact": False, "length": 5, "broken_at": 2})
        self.assertFalse(entry["intact"])
        self.assertFalse(entry["trustworthy"])  # absent → false
        self.assertEqual(entry["broken_at"], 2)

    def test_list_is_newest_first_with_limit(self):
        for i in range(3):
            self.log.record({"intact": True, "length": i})
        history = self.log.list()
        self.assertEqual([h["length"] for h in history], [2, 1, 0])  # newest first
        self.assertEqual(len(self.log.list(limit=2)), 2)

    def test_latest_returns_the_most_recent(self):
        self.assertIsNone(self.log.latest())
        self.log.record({"intact": True, "length": 1})
        self.log.record({"intact": False, "length": 1, "broken_at": 1})
        self.assertFalse(self.log.latest()["intact"])

    def test_empty_log_returns_empty_list(self):
        self.assertEqual(self.log.list(), [])

    def test_id_is_autoincremented(self):
        e1 = self.log.record({"intact": True, "length": 1})
        e2 = self.log.record({"intact": True, "length": 2})
        e3 = self.log.record({"intact": False, "length": 3, "broken_at": 1})
        self.assertEqual(e1["id"], 1)
        self.assertEqual(e2["id"], 2)
        self.assertEqual(e3["id"], 3)

    def test_checked_at_is_nonempty_iso_timestamp(self):
        entry = self.log.record({"intact": True, "length": 0})
        self.assertTrue(entry["checked_at"])
        self.assertIn("T", entry["checked_at"])  # ISO 8601

    def test_broken_at_none_stored_as_none(self):
        self.log.record({"intact": True, "trustworthy": True, "length": 5, "broken_at": None})
        entry = self.log.list()[0]
        self.assertIsNone(entry["broken_at"])

    def test_record_returns_all_required_keys(self):
        entry = self.log.record({"intact": True, "trustworthy": True, "length": 7})
        for key in ("id", "intact", "trustworthy", "length", "broken_at", "checked_at"):
            self.assertIn(key, entry)

    def test_persistence_across_two_connections(self):
        """Data written through one DriftAuditLog instance is visible to another."""
        self.log.record({"intact": True, "length": 42})
        second_log = DriftAuditLog(self.db_path)
        entries = second_log.list()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["length"], 42)


if __name__ == "__main__":
    unittest.main()


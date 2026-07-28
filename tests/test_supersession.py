"""Tests for supersession.py — append-only supersession links.

Covers:
  - record() and lineage() for simple supersession
  - Chain of versions (v1 → v2 → v3)
  - exists() idempotence guard
  - Unlinked attestation is current
  - list() returns records in creation order
  - record() returns dict with all fields
  - Multiple supersessions of same old_id
  - lineage() dict has all required keys
"""
import os
import tempfile
import unittest

from supersession import SupersessionLog
try:
    from tests.test_helpers import safe_remove
except ImportError:
    from test_helpers import safe_remove


class SupersessionLogTests(unittest.TestCase):

    def setUp(self):
        handle = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        handle.close()
        self.db_path = handle.name
        self.log = SupersessionLog(self.db_path)

    def tearDown(self):
        safe_remove(self.db_path)

    def test_record_and_lineage(self):
        self.log.record(1, 2, "alice", "re-verified the revised charter")
        # #1 is superseded by #2; #2 supersedes #1
        old = self.log.lineage(1)
        self.assertEqual(old["superseded_by"], [2])
        self.assertFalse(old["is_current"])
        new = self.log.lineage(2)
        self.assertEqual(new["supersedes"], [1])
        self.assertTrue(new["is_current"])

    def test_chain_of_versions(self):
        self.log.record(1, 2, "a", "v2")
        self.log.record(2, 3, "a", "v3")
        # #2 both supersedes #1 and is superseded by #3 -> not current
        mid = self.log.lineage(2)
        self.assertEqual(mid["supersedes"], [1])
        self.assertEqual(mid["superseded_by"], [3])
        self.assertFalse(mid["is_current"])
        # #3 is the current version
        self.assertTrue(self.log.lineage(3)["is_current"])

    def test_exists_guard(self):
        self.assertFalse(self.log.exists(1, 2))
        self.log.record(1, 2, "a", "r")
        self.assertTrue(self.log.exists(1, 2))

    def test_unlinked_attestation_is_current(self):
        line = self.log.lineage(99)
        self.assertEqual(line["supersedes"], [])
        self.assertEqual(line["superseded_by"], [])
        self.assertTrue(line["is_current"])

    def test_list_returns_creation_order(self):
        self.log.record(1, 2, "a", "first")
        self.log.record(2, 3, "b", "second")
        records = self.log.list()
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]["old_id"], 1)
        self.assertEqual(records[1]["old_id"], 2)
        self.assertLessEqual(records[0]["created_at"], records[1]["created_at"])

    def test_record_returns_dict_with_all_fields(self):
        rec = self.log.record(10, 20, "alice", "upgrade")
        self.assertIn("id", rec)
        self.assertEqual(rec["old_id"], 10)
        self.assertEqual(rec["new_id"], 20)
        self.assertEqual(rec["actor"], "alice")
        self.assertEqual(rec["reason"], "upgrade")
        self.assertIn("created_at", rec)

    def test_multiple_supersessions_of_same_old_id(self):
        self.log.record(1, 2, "a", "fork-a")
        self.log.record(1, 3, "b", "fork-b")
        line = self.log.lineage(1)
        self.assertEqual(sorted(line["superseded_by"]), [2, 3])
        self.assertFalse(line["is_current"])

    def test_lineage_dict_keys(self):
        line = self.log.lineage(1)
        self.assertEqual(set(line.keys()), {"id", "supersedes", "superseded_by", "is_current"})


if __name__ == "__main__":
    unittest.main()


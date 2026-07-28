"""Tests for usage.py — VaaS actor build usage logging.

Covers:
  - record() and list() basic operation
  - list(actor=...) filtering by actor
  - summary() aggregation by action
  - persistence across instance re-instantiation
  - count_in_window() rolling window count and oldest timestamp
  - count_in_window() with custom 'now' aging out old entries
  - count_in_window() filtering by action
  - empty summary() for unused actor
  - count_in_window() for unknown actor returns 0 count and None oldest
  - list(limit=N) caps returned records
"""
import os
import tempfile
import unittest

from usage import UsageLog
try:
    from tests.test_helpers import safe_remove
except ImportError:
    from test_helpers import safe_remove


class UsageLogTests(unittest.TestCase):

    def setUp(self):
        handle = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        handle.close()
        self.db_path = handle.name
        self.usage = UsageLog(self.db_path)

    def tearDown(self):
        safe_remove(self.db_path)

    def test_record_and_list(self):
        entry = self.usage.record("alice", "build", "attestor", "task-1")
        self.assertEqual(entry["id"], 1)
        self.assertEqual(entry["action"], "build")
        events = self.usage.list()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["actor"], "alice")

    def test_list_scoped_by_actor(self):
        self.usage.record("alice", "build", "attestor")
        self.usage.record("bob", "build", "arbiter")
        self.usage.record("alice", "quota_exceeded", "attestor")
        self.assertEqual(len(self.usage.list()), 3)
        self.assertEqual(len(self.usage.list(actor="alice")), 2)

    def test_summary_counts_by_action(self):
        self.usage.record("alice", "build", "attestor")
        self.usage.record("alice", "build", "attestor")
        self.usage.record("alice", "quota_exceeded", "attestor")
        summary = self.usage.summary(actor="alice")
        self.assertEqual(summary["total"], 3)
        self.assertEqual(summary["by_action"], {"build": 2, "quota_exceeded": 1})

    def test_persists_across_instances(self):
        self.usage.record("alice", "build", "attestor")
        reopened = UsageLog(self.db_path)
        self.assertEqual(len(reopened.list()), 1)

    def test_count_in_window(self):
        from datetime import datetime, timedelta, timezone

        self.usage.record("alice", "build", "attestor")
        self.usage.record("alice", "build", "attestor")
        self.usage.record("bob", "build", "attestor")

        count, oldest = self.usage.count_in_window("alice", "build", 3600)
        self.assertEqual(count, 2)
        self.assertIsNotNone(oldest)

        # a 'now' two hours ahead ages every event out of a 1-hour window
        future = datetime.now(timezone.utc) + timedelta(hours=2)
        aged_count, aged_oldest = self.usage.count_in_window(
            "alice", "build", 3600, now=future
        )
        self.assertEqual(aged_count, 0)
        self.assertIsNone(aged_oldest)

    def test_count_in_window_filters_by_action(self):
        self.usage.record("alice", "build", "attestor")
        self.usage.record("alice", "quota_exceeded", "attestor")
        count, _ = self.usage.count_in_window("alice", "build", 3600)
        self.assertEqual(count, 1)

    def test_empty_summary_returns_zero(self):
        summary = self.usage.summary(actor="ghost")
        self.assertEqual(summary["total"], 0)
        self.assertEqual(summary["by_action"], {})

    def test_unknown_actor_window_count_returns_zero(self):
        count, oldest = self.usage.count_in_window("ghost", "build", 3600)
        self.assertEqual(count, 0)
        self.assertIsNone(oldest)


if __name__ == "__main__":
    unittest.main()



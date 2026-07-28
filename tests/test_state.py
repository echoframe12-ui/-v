"""Tests for state.py — StateSnapshot functionality.

Covers:
  - record() stores event and detail
  - record() defaults detail to empty string when None
  - record() multiple events and snapshot()
  - snapshot() on empty instance
  - snapshot() events list copy isolation
"""
import unittest

from state import StateSnapshot


class StateSnapshotTests(unittest.TestCase):

    def test_record_and_snapshot(self):
        snapshot = StateSnapshot()
        e1 = snapshot.record("start", "agent initialized")
        e2 = snapshot.record("finish", "task completed")
        self.assertEqual(e1, {"event": "start", "detail": "agent initialized"})
        self.assertEqual(e2, {"event": "finish", "detail": "task completed"})
        state = snapshot.snapshot()
        self.assertEqual(state["count"], 2)
        self.assertEqual(state["events"][0]["event"], "start")
        self.assertEqual(state["events"][1]["detail"], "task completed")

    def test_record_default_detail(self):
        snapshot = StateSnapshot()
        entry = snapshot.record("checkpoint")
        self.assertEqual(entry["detail"], "")

    def test_empty_snapshot(self):
        snapshot = StateSnapshot()
        state = snapshot.snapshot()
        self.assertEqual(state["count"], 0)
        self.assertEqual(state["events"], [])

    def test_snapshot_returns_copy(self):
        snapshot = StateSnapshot()
        snapshot.record("e1")
        state = snapshot.snapshot()
        state["events"].append({"event": "fake", "detail": "fake"})
        self.assertEqual(snapshot.snapshot()["count"], 1)


if __name__ == "__main__":
    unittest.main()


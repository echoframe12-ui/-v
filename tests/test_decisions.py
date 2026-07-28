"""Tests for decisions.py — DecisionRegistry functionality.

Covers:
  - record() stores title, context, and decision
  - record() multiple decisions and list()
  - list() on empty registry returns empty list
  - list() returns copy of internal decisions list
"""
import unittest

from decisions import DecisionRegistry


class DecisionRegistryTests(unittest.TestCase):

    def test_record_and_list(self):
        registry = DecisionRegistry()
        entry = registry.record("Use SQLite", "Need simple persistence", "Store memory in SQLite")
        self.assertEqual(entry["title"], "Use SQLite")
        self.assertEqual(entry["context"], "Need simple persistence")
        self.assertEqual(entry["decision"], "Store memory in SQLite")
        decisions = registry.list()
        self.assertEqual(len(decisions), 1)

    def test_record_multiple(self):
        registry = DecisionRegistry()
        registry.record("t1", "c1", "d1")
        registry.record("t2", "c2", "d2")
        decisions = registry.list()
        self.assertEqual(len(decisions), 2)
        self.assertEqual(decisions[0]["title"], "t1")
        self.assertEqual(decisions[1]["decision"], "d2")

    def test_empty_registry_list(self):
        registry = DecisionRegistry()
        self.assertEqual(registry.list(), [])

    def test_list_returns_copy(self):
        registry = DecisionRegistry()
        registry.record("t1", "c1", "d1")
        decisions = registry.list()
        decisions.append({"title": "fake", "context": "fake", "decision": "fake"})
        self.assertEqual(len(registry.list()), 1)


if __name__ == "__main__":
    unittest.main()


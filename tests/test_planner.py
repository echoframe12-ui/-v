"""Tests for planner.py — Planner functionality.

Covers:
  - plan() returns task, 4 steps, trace_length
  - plan() uses custom context in step 2
  - plan() defaults context to 'general context'
  - plan() accumulates trace across multiple plans
  - get_trace() returns full trace history
"""
import unittest

from planner import Planner


class PlannerTests(unittest.TestCase):

    def setUp(self):
        self.planner = Planner()

    def test_plan_records_trace(self):
        result = self.planner.plan("Draft the charter", "This is a governance update")
        self.assertEqual(result["task"], "Draft the charter")
        self.assertEqual(len(result["steps"]), 4)
        self.assertEqual(result["trace_length"], 1)
        self.assertEqual(len(self.planner.get_trace()), 1)
        self.assertEqual(result["steps"][1]["description"], "Gather context: This is a governance update")

    def test_plan_default_context(self):
        result = self.planner.plan("Task without context")
        self.assertEqual(result["steps"][1]["description"], "Gather context: general context")

    def test_multiple_plans_accumulate_trace(self):
        self.planner.plan("P1")
        r2 = self.planner.plan("P2")
        self.assertEqual(r2["trace_length"], 2)
        self.assertEqual(len(self.planner.get_trace()), 2)
        self.assertEqual(self.planner.get_trace()[0]["task"], "P1")
        self.assertEqual(self.planner.get_trace()[1]["task"], "P2")

    def test_get_trace_initial_empty(self):
        self.assertEqual(self.planner.get_trace(), [])


if __name__ == "__main__":
    unittest.main()


"""Tests for agent.py — AgentLoop functionality.

Covers:
  - run() emits start, plan, finish event sequence
  - run() uses custom context when provided
  - run() defaults context to 'general' when None
  - run() accumulates events across multiple executions
  - events() returns full history of emitted events
"""
import unittest

from agent import AgentLoop


class AgentLoopTests(unittest.TestCase):

    def test_run_emits_events(self):
        loop = AgentLoop()
        result = loop.run("Review the charter", "Governance")
        self.assertEqual(result["task"], "Review the charter")
        self.assertEqual(len(result["events"]), 3)
        self.assertEqual(loop.events()[0], {"event": "start", "task": "Review the charter"})
        self.assertEqual(loop.events()[1], {"event": "plan", "context": "Governance"})
        self.assertEqual(loop.events()[2], {"event": "finish", "task": "Review the charter"})

    def test_run_default_context(self):
        loop = AgentLoop()
        loop.run("Task without context")
        self.assertEqual(loop.events()[1]["context"], "general")

    def test_multiple_runs_accumulate(self):
        loop = AgentLoop()
        loop.run("Task 1")
        loop.run("Task 2")
        self.assertEqual(len(loop.events()), 6)
        self.assertEqual(loop.events()[0]["task"], "Task 1")
        self.assertEqual(loop.events()[3]["task"], "Task 2")

    def test_events_empty_initial(self):
        loop = AgentLoop()
        self.assertEqual(loop.events(), [])


if __name__ == "__main__":
    unittest.main()


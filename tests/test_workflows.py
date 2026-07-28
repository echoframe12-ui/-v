"""Tests for workflows.py — WorkflowEngine functionality.

Covers:
  - create_workflow() returns created status dict
  - get_workflow() retrieves created workflow steps
  - get_workflow() on unknown workflow raises KeyError
  - execute_workflow() executes and returns step details
  - execute_workflow() on unknown workflow raises KeyError
"""
import unittest

from workflows import WorkflowEngine


class WorkflowEngineTests(unittest.TestCase):

    def setUp(self):
        self.engine = WorkflowEngine()

    def test_create_and_execute_workflow(self):
        res = self.engine.create_workflow(
            "review",
            [
                {"name": "collect", "type": "tool"},
                {"name": "summarize", "type": "reason"},
            ],
        )
        self.assertEqual(res, {"created": True, "name": "review", "steps": 2})
        workflow = self.engine.get_workflow("review")
        self.assertEqual(workflow["name"], "review")
        self.assertEqual(len(workflow["steps"]), 2)
        executed = self.engine.execute_workflow("review")
        self.assertTrue(executed["executed"])
        self.assertEqual(executed["name"], "review")
        self.assertEqual(len(executed["steps"]), 2)

    def test_get_unknown_workflow_raises_keyerror(self):
        with self.assertRaises(KeyError):
            self.engine.get_workflow("nonexistent")

    def test_execute_unknown_workflow_raises_keyerror(self):
        with self.assertRaises(KeyError):
            self.engine.execute_workflow("nonexistent")

    def test_multiple_workflows(self):
        self.engine.create_workflow("wf1", [{"name": "s1"}])
        self.engine.create_workflow("wf2", [{"name": "s1"}, {"name": "s2"}])
        self.assertEqual(len(self.engine.get_workflow("wf1")["steps"]), 1)
        self.assertEqual(len(self.engine.get_workflow("wf2")["steps"]), 2)


if __name__ == "__main__":
    unittest.main()


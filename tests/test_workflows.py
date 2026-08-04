import unittest

from workflows import WorkflowEngine


class WorkflowEngineTests(unittest.TestCase):
    def setUp(self):
        self.engine = WorkflowEngine()

    def test_create_and_execute_workflow(self):
        self.engine.create_workflow(
            "review",
            [
                {"name": "collect", "type": "tool"},
                {"name": "summarize", "type": "reason"},
            ],
        )
        workflow = self.engine.get_workflow("review")
        self.assertEqual(workflow["name"], "review")
        self.assertEqual(len(workflow["steps"]), 2)
        executed = self.engine.execute_workflow("review")
        self.assertTrue(executed["executed"])

    def test_get_unknown_workflow_raises(self):
        with self.assertRaises(KeyError):
            self.engine.get_workflow("nonexistent")

    def test_execute_unknown_workflow_raises(self):
        with self.assertRaises(KeyError):
            self.engine.execute_workflow("nonexistent")

    def test_list_workflows_empty(self):
        self.assertEqual(self.engine.list_workflows(), [])

    def test_list_workflows_after_create(self):
        self.engine.create_workflow("alpha", [{"name": "a", "type": "tool"}])
        self.engine.create_workflow("beta", [{"name": "b", "type": "reason"}])
        listing = self.engine.list_workflows()
        self.assertEqual(len(listing), 2)
        names = {w["name"] for w in listing}
        self.assertEqual(names, {"alpha", "beta"})

    def test_workflow_status_lifecycle(self):
        self.engine.create_workflow("deploy", [{"name": "build", "type": "tool"}])
        self.assertEqual(self.engine.get_workflow("deploy")["status"], "created")
        self.engine.execute_workflow("deploy")
        self.assertEqual(self.engine.get_workflow("deploy")["status"], "completed")

    def test_execute_with_tool_runner(self):
        outputs = []

        def runner(name, params):
            outputs.append(name)
            return {"ran": name}

        self.engine.create_workflow(
            "pipeline",
            [
                {"name": "fetch", "type": "tool"},
                {"name": "analyze", "type": "reason"},
                {"name": "store", "type": "tool"},
            ],
        )
        result = self.engine.execute_workflow("pipeline", tool_runner=runner)
        self.assertTrue(result["executed"])
        self.assertEqual(result["status"], "completed")
        # tool_runner only called for type=tool steps
        self.assertEqual(outputs, ["fetch", "store"])
        # step results carry output
        self.assertEqual(result["steps"][0]["output"], {"ran": "fetch"})
        self.assertIsNone(result["steps"][1]["output"])  # reason step
        self.assertEqual(result["steps"][2]["output"], {"ran": "store"})

    def test_execute_with_tool_runner_failure_stops_pipeline(self):
        def failing_runner(name, params):
            if name == "fail-step":
                raise RuntimeError("step exploded")
            return {"ok": True}

        self.engine.create_workflow(
            "fragile",
            [
                {"name": "ok-step", "type": "tool"},
                {"name": "fail-step", "type": "tool"},
                {"name": "never-reached", "type": "tool"},
            ],
        )
        result = self.engine.execute_workflow("fragile", tool_runner=failing_runner)
        self.assertFalse(result["executed"])
        self.assertEqual(result["status"], "failed")
        self.assertEqual(len(result["steps"]), 2)  # stopped after failure
        self.assertEqual(result["steps"][0]["status"], "completed")
        self.assertEqual(result["steps"][1]["status"], "failed")
        self.assertIn("exploded", result["steps"][1]["error"])
        # workflow status reflects failure
        self.assertEqual(self.engine.get_workflow("fragile")["status"], "failed")

    def test_run_history_accumulates(self):
        self.engine.create_workflow("repeatable", [{"name": "a", "type": "reason"}])
        self.engine.execute_workflow("repeatable")
        self.engine.execute_workflow("repeatable")
        wf = self.engine.get_workflow("repeatable")
        self.assertEqual(wf["runs"], 2)

    def test_reset_workflow(self):
        self.engine.create_workflow("resettable", [{"name": "a", "type": "tool"}])
        self.engine.execute_workflow("resettable")
        self.assertEqual(self.engine.get_workflow("resettable")["status"], "completed")
        result = self.engine.reset_workflow("resettable")
        self.assertEqual(result["status"], "created")
        self.assertEqual(self.engine.get_workflow("resettable")["status"], "created")

    def test_reset_unknown_workflow_raises(self):
        with self.assertRaises(KeyError):
            self.engine.reset_workflow("ghost")

    def test_step_params_passed_to_runner(self):
        received = {}

        def runner(name, params):
            received[name] = params
            return {}

        self.engine.create_workflow(
            "parameterized",
            [{"name": "deploy", "type": "tool", "params": {"env": "staging", "replicas": 3}}],
        )
        self.engine.execute_workflow("parameterized", tool_runner=runner)
        self.assertEqual(received["deploy"], {"env": "staging", "replicas": 3})


if __name__ == "__main__":
    unittest.main()

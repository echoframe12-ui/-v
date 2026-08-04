import json
import unittest
from io import StringIO
from unittest.mock import patch

from cli import build_parser, main


class CLITests(unittest.TestCase):
    def test_parser_builds(self):
        parser = build_parser()
        self.assertIsNotNone(parser)

    def test_health_command(self):
        buf = StringIO()
        with patch("sys.stdout", buf):
            code = main(["health"])
        self.assertEqual(code, 0)
        output = json.loads(buf.getvalue())
        self.assertEqual(output["status"], "ok")

    def test_plan_command(self):
        buf = StringIO()
        with patch("sys.stdout", buf):
            code = main(["plan", "Draft charter"])
        self.assertEqual(code, 0)
        output = json.loads(buf.getvalue())
        self.assertEqual(output["task"], "Draft charter")

    def test_run_command(self):
        buf = StringIO()
        with patch("sys.stdout", buf):
            code = main(["run", "Build platform", "--context", "orchestration"])
        self.assertEqual(code, 0)
        output = json.loads(buf.getvalue())
        self.assertEqual(output["task"], "Build platform")
        self.assertIn("plan", output)

    def test_tool_command(self):
        buf = StringIO()
        with patch("sys.stdout", buf):
            code = main(["tool", "echo", '{"message": "hi"}'])
        self.assertEqual(code, 0)
        output = json.loads(buf.getvalue())
        self.assertEqual(output["output"], "hi")

    def test_tool_invalid_json(self):
        buf = StringIO()
        with patch("sys.stderr", buf):
            code = main(["tool", "echo", "invalid-json"])
        self.assertEqual(code, 1)

    def test_tool_unknown(self):
        buf = StringIO()
        with patch("sys.stderr", buf):
            code = main(["tool", "nonexistent"])
        self.assertEqual(code, 1)

    def test_plugins_command(self):
        buf = StringIO()
        with patch("sys.stdout", buf):
            code = main(["plugins"])
        self.assertEqual(code, 0)
        output = json.loads(buf.getvalue())
        self.assertIsInstance(output, list)

    def test_workflow_commands(self):
        # create
        buf = StringIO()
        with patch("sys.stdout", buf):
            code = main(["workflow", "create", "wf1", '[{"name":"echo","type":"tool"}]'])
        self.assertEqual(code, 0)

        # list
        buf = StringIO()
        with patch("sys.stdout", buf):
            code = main(["workflow", "list"])
        self.assertEqual(code, 0)

        # run
        buf = StringIO()
        with patch("sys.stdout", buf):
            code = main(["workflow", "run", "wf1"])
        self.assertEqual(code, 0)
    def test_verify_command(self):
        buf = StringIO()
        with patch("sys.stdout", buf):
            code = main(["verify"])
        output = json.loads(buf.getvalue())
        self.assertIn(output["mood"], ("clear", "dissent"))
        self.assertIn("contract_stack", output)
        self.assertIn("route", output)
        # If clear, exit 0; if dissent, exit 1
        if output["mood"] == "clear":
            self.assertEqual(code, 0)
        else:
            self.assertEqual(code, 1)

    def test_gate_command(self):
        buf = StringIO()
        with patch("sys.stdout", buf):
            code = main(["gate"])
        output = json.loads(buf.getvalue())
        self.assertIn("ok", output)
        self.assertIn("modules", output)
        if output["ok"]:
            self.assertEqual(code, 0)
        else:
            self.assertEqual(code, 1)

    def test_workflow_mood_gate_step(self):
        from workflows import WorkflowEngine
        import tempfile, os

        db = os.path.join(tempfile.mkdtemp(), "test_mood.db")
        engine = WorkflowEngine(db_path=db)
        engine.create_workflow("gated", [
            {"name": "mood_check", "type": "mood_gate"},
            {"name": "echo", "type": "tool"},
        ])
        result = engine.execute_workflow("gated")
        # mood_gate step should have mood output
        mood_step = result["steps"][0]
        self.assertIn("mood", mood_step["output"])
        self.assertIn("route", mood_step["output"])
        # If the gate passed, second step runs
        if mood_step["output"]["mood"] == "clear":
            self.assertTrue(result["executed"])
            self.assertEqual(len(result["steps"]), 2)
        else:
            # If dissent, workflow halts at first step
            self.assertFalse(result["executed"])
            self.assertEqual(mood_step["status"], "failed")


if __name__ == "__main__":
    unittest.main()

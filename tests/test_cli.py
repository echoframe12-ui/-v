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


if __name__ == "__main__":
    unittest.main()

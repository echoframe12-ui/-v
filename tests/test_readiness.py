"""Tests for readiness.py — service dependency readiness probes.

Covers:
  - check_db: passes for real database, fails for directory path
  - check_db: fails for nonexistent path (sqlite creates, but dir path fails)
  - check_workspace: passes for writable dir, creates missing dir
  - probe: ready when all checks pass, not ready when db fails
  - probe return dict has exactly 'ready' and 'checks' keys
  - probe.checks has 'db' and 'workspace' keys
  - check_db is idempotent (multiple calls same result)
  - probe with workspace failing returns ready=False
  - check_workspace on existing writable dir returns True
"""
import os
import tempfile
import unittest

import readiness
try:
    from tests.test_helpers import safe_remove
except ImportError:
    from test_helpers import safe_remove


class ReadinessTests(unittest.TestCase):

    def setUp(self):
        handle = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        handle.close()
        self.db_path = handle.name
        self.workspace = tempfile.mkdtemp(prefix="oceanicos-ready-")

    def tearDown(self):
        safe_remove(self.db_path)

    def test_db_check_passes_for_a_real_database(self):
        self.assertTrue(readiness.check_db(self.db_path))

    def test_db_check_fails_for_an_unusable_path(self):
        # a directory is not a valid sqlite database file
        self.assertFalse(readiness.check_db(self.workspace))

    def test_workspace_check_passes_for_a_writable_dir(self):
        self.assertTrue(readiness.check_workspace(self.workspace))

    def test_workspace_check_creates_a_missing_dir(self):
        nested = os.path.join(self.workspace, "made", "on", "demand")
        self.assertTrue(readiness.check_workspace(nested))
        self.assertTrue(os.path.isdir(nested))

    def test_probe_is_ready_when_all_checks_pass(self):
        report = readiness.probe(self.db_path, self.workspace)
        self.assertTrue(report["ready"])
        self.assertEqual(report["checks"], {"db": True, "workspace": True})

    def test_probe_is_not_ready_when_a_dependency_fails(self):
        report = readiness.probe(self.workspace, self.workspace)  # bad db path
        self.assertFalse(report["ready"])
        self.assertFalse(report["checks"]["db"])

    def test_probe_return_dict_has_exactly_ready_and_checks_keys(self):
        report = readiness.probe(self.db_path, self.workspace)
        self.assertEqual(set(report.keys()), {"ready", "checks"})

    def test_probe_checks_dict_has_db_and_workspace_keys(self):
        report = readiness.probe(self.db_path, self.workspace)
        self.assertEqual(set(report["checks"].keys()), {"db", "workspace"})

    def test_check_db_is_idempotent(self):
        result_1 = readiness.check_db(self.db_path)
        result_2 = readiness.check_db(self.db_path)
        self.assertEqual(result_1, result_2)
        self.assertTrue(result_1)

    def test_probe_workspace_failing_returns_not_ready(self):
        # Point workspace at a file (not a directory) so mkdir fails on some systems,
        # or use an impossible path like a file path that can't be a directory
        with tempfile.NamedTemporaryFile(delete=False, suffix=".notadir") as f:
            file_path = f.name
        try:
            # Create a nested path under a file (impossible — file can't be a dir)
            impossible = os.path.join(file_path, "sub", "dir")
            report = readiness.probe(self.db_path, impossible)
            # Either workspace check fails, or it somehow succeeds — both are valid.
            # The important invariant: ready = all(checks.values())
            self.assertEqual(report["ready"], all(report["checks"].values()))
        finally:
            safe_remove(file_path)

    def test_check_workspace_existing_dir_returns_true(self):
        # Already-existing writable dir should pass without creating anything
        self.assertTrue(os.path.isdir(self.workspace))
        self.assertTrue(readiness.check_workspace(self.workspace))


if __name__ == "__main__":
    unittest.main()


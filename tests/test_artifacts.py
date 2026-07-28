"""Tests for artifacts.py — ArtifactRegistry functionality.

Covers:
  - create() default status is 'draft'
  - create() custom status override
  - create() and list() with multiple artifacts
  - list() on empty registry returns empty list
  - list() returns a copy of internal artifacts list
"""
import unittest

from artifacts import ArtifactRegistry


class ArtifactRegistryTests(unittest.TestCase):

    def test_create_default_status(self):
        registry = ArtifactRegistry()
        artifact = registry.create("spec", "document")
        self.assertEqual(artifact["name"], "spec")
        self.assertEqual(artifact["kind"], "document")
        self.assertEqual(artifact["status"], "draft")
        self.assertEqual(len(registry.list()), 1)

    def test_create_custom_status(self):
        registry = ArtifactRegistry()
        artifact = registry.create("build_log", "log", status="final")
        self.assertEqual(artifact["status"], "final")

    def test_create_multiple_and_list(self):
        registry = ArtifactRegistry()
        registry.create("a1", "kind_a")
        registry.create("a2", "kind_b")
        artifacts = registry.list()
        self.assertEqual(len(artifacts), 2)
        self.assertEqual(artifacts[0]["name"], "a1")
        self.assertEqual(artifacts[1]["name"], "a2")

    def test_empty_registry_list(self):
        registry = ArtifactRegistry()
        self.assertEqual(registry.list(), [])

    def test_list_returns_copy(self):
        registry = ArtifactRegistry()
        registry.create("spec", "doc")
        artifacts = registry.list()
        artifacts.append({"name": "fake", "kind": "fake", "status": "fake"})
        self.assertEqual(len(registry.list()), 1)


if __name__ == "__main__":
    unittest.main()


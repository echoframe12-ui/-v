"""Tests for plugins.py — PluginRegistry functionality.

Covers:
  - register() adds plugin with name and capabilities
  - register() multiple plugins and list()
  - list() on empty registry returns empty list
  - list() returns copy of internal plugins list
"""
import unittest

from plugins import PluginRegistry


class PluginRegistryTests(unittest.TestCase):

    def test_register_and_list(self):
        registry = PluginRegistry()
        plugin = registry.register("github", ["tool", "sync"])
        self.assertEqual(plugin["name"], "github")
        self.assertEqual(plugin["capabilities"], ["tool", "sync"])
        self.assertEqual(len(registry.list()), 1)

    def test_register_multiple(self):
        registry = PluginRegistry()
        registry.register("p1", ["cap1"])
        registry.register("p2", ["cap2", "cap3"])
        plugins = registry.list()
        self.assertEqual(len(plugins), 2)
        self.assertEqual(plugins[0]["name"], "p1")
        self.assertEqual(plugins[1]["capabilities"], ["cap2", "cap3"])

    def test_empty_registry_list(self):
        registry = PluginRegistry()
        self.assertEqual(registry.list(), [])

    def test_list_returns_copy(self):
        registry = PluginRegistry()
        registry.register("p1", [])
        plugins = registry.list()
        plugins.append({"name": "fake", "capabilities": []})
        self.assertEqual(len(registry.list()), 1)


if __name__ == "__main__":
    unittest.main()


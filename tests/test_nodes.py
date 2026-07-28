"""Tests for nodes.py — charter-agnostic mountable high-flux nodes.

Covers:
  - mount() strips name, lowercases, normalises leading slash
  - mount() sets agnostic=True, flux='high' default, stripped=STRIPPED_ATTRIBUTES
  - empty name (after stripping) raises ValueError
  - remount replaces existing node; list returns all unique
  - list on empty registry returns empty list
  - mounted_at is non-empty ISO timestamp
  - flux can be overridden
  - node dict has all required keys
  - STRIPPED_ATTRIBUTES contains expected attribute names
"""
import unittest

from nodes import STRIPPED_ATTRIBUTES, NodeRegistry


class NodeRegistryTests(unittest.TestCase):

    def test_mount_strips_to_agnostic_form(self):
        registry = NodeRegistry()
        node = registry.mount("/Nigeria")
        self.assertEqual(node["name"], "nigeria")
        self.assertEqual(node["mount"], "/nigeria")
        self.assertEqual(node["flux"], "high")
        self.assertTrue(node["agnostic"])
        self.assertEqual(node["stripped"], STRIPPED_ATTRIBUTES)

    def test_stripping_is_uniform_for_every_node(self):
        registry = NodeRegistry()
        first = registry.mount("alpha")
        second = registry.mount("omega")
        self.assertEqual(first["stripped"], second["stripped"])

    def test_remount_replaces_and_list_returns_all(self):
        registry = NodeRegistry()
        registry.mount("alpha")
        registry.mount("alpha", flux="low")
        registry.mount("omega")
        nodes = registry.list()
        self.assertEqual(len(nodes), 2)
        self.assertEqual(nodes[0]["flux"], "low")

    def test_empty_name_raises(self):
        registry = NodeRegistry()
        with self.assertRaises(ValueError):
            registry.mount("  / ")

    def test_mounted_at_is_iso_timestamp(self):
        registry = NodeRegistry()
        node = registry.mount("delta")
        self.assertTrue(node["mounted_at"])
        self.assertIn("T", node["mounted_at"])  # ISO 8601

    def test_empty_registry_list_returns_empty(self):
        registry = NodeRegistry()
        self.assertEqual(registry.list(), [])

    def test_flux_low_is_persisted(self):
        registry = NodeRegistry()
        node = registry.mount("low-flux-node", flux="low")
        self.assertEqual(node["flux"], "low")
        self.assertEqual(registry.list()[0]["flux"], "low")

    def test_agnostic_is_always_true(self):
        registry = NodeRegistry()
        node = registry.mount("any-node", flux="medium")
        self.assertTrue(node["agnostic"])

    def test_node_dict_has_all_required_keys(self):
        registry = NodeRegistry()
        node = registry.mount("test-node")
        for key in ("name", "mount", "flux", "agnostic", "stripped", "mounted_at"):
            self.assertIn(key, node)

    def test_mount_normalises_uppercase_and_leading_slash(self):
        registry = NodeRegistry()
        node = registry.mount("/UPPER/CASE")
        # Only the first path component is used (strip removes leading slash, then lower)
        self.assertEqual(node["name"], "upper/case")
        self.assertEqual(node["mount"], "/upper/case")

    def test_stripped_attributes_contains_expected_names(self):
        for attr in ("terrain", "currency", "affiliation"):
            self.assertIn(attr, STRIPPED_ATTRIBUTES)


if __name__ == "__main__":
    unittest.main()


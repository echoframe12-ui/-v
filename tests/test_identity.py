"""Tests for identity.py — stack self-description.

Covers:
  - render() returns exact lineage tree string
  - as_list() returns exact 4 plain names in root-first order
  - Every level in TREE has non-empty name and gloss
  - TREE contains exactly 4 elements
  - as_list() matches first elements of TREE
  - render() output contains all names in TREE
"""
import unittest

import identity

EXPECTED_TREE = "/\n└── Ω∞v Compiler\n    └── OceanicOS\n        └── Living Agnostic Charter"


class IdentityTests(unittest.TestCase):

    def test_render_is_the_exact_lineage_tree(self):
        self.assertEqual(identity.render(), EXPECTED_TREE)

    def test_as_list_is_the_four_names_root_first(self):
        self.assertEqual(
            identity.as_list(),
            ["/", "Ω∞v Compiler", "OceanicOS", "Living Agnostic Charter"],
        )

    def test_every_level_has_a_gloss(self):
        for name, gloss in identity.TREE:
            self.assertTrue(name)
            self.assertTrue(gloss.strip())

    def test_tree_has_four_levels(self):
        self.assertEqual(len(identity.TREE), 4)

    def test_as_list_matches_tree_names(self):
        names = [n for n, _ in identity.TREE]
        self.assertEqual(identity.as_list(), names)

    def test_render_contains_all_tree_names(self):
        rendered = identity.render()
        for name in identity.as_list():
            self.assertIn(name, rendered)


if __name__ == "__main__":
    unittest.main()


import unittest

from context_assembly import ContextAssembler, ContextSource


class ContextAssemblyTests(unittest.TestCase):
    def test_assembly_preserves_provenance_and_hashes(self):
        source = ContextSource(ref="doctrine", content="Reality before assumption.", authority="charter")
        result = ContextAssembler().assemble([source])

        self.assertEqual(result.included_refs, ("doctrine",))
        self.assertEqual(result.omitted_refs, ())
        self.assertFalse(result.truncated)
        self.assertIn("content_hash", result.sources[0])
        self.assertEqual(result.sources[0]["authority"], "charter")
        self.assertTrue(result.content_hash)

    def test_budget_makes_omission_explicit(self):
        sources = [
            ContextSource(ref="first", content="12345"),
            ContextSource(ref="second", content="67890"),
        ]
        result = ContextAssembler(max_chars=15).assemble(sources)

        self.assertEqual(result.included_refs, ("first",))
        self.assertEqual(result.omitted_refs, ("second",))
        self.assertTrue(result.truncated)

    def test_empty_context_is_valid_and_hashable(self):
        result = ContextAssembler().assemble([])

        self.assertEqual(result.content, "")
        self.assertEqual(result.included_refs, ())
        self.assertEqual(result.omitted_refs, ())
        self.assertFalse(result.truncated)
        self.assertTrue(result.content_hash)

    def test_invalid_budget_is_rejected(self):
        with self.assertRaises(ValueError):
            ContextAssembler(max_chars=0)


if __name__ == "__main__":
    unittest.main()

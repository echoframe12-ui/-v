import unittest

from context_assembly import ContextAssembler, ContextSource
from perspectives import compare_perspectives, make_perspective


class PerspectiveTests(unittest.TestCase):
    def setUp(self):
        self.context = ContextAssembler().assemble(
            [ContextSource(ref="source-a", content="Evidence A", authority="test")]
        )

    def test_perspective_preserves_context_lineage(self):
        perspective = make_perspective(
            perspective_id="p1",
            provider="local",
            model="demo",
            response="answer",
            context=self.context,
            confidence=0.8,
        )

        self.assertEqual(perspective.context_hash, self.context.content_hash)
        self.assertEqual(perspective.source_refs, ("source-a",))
        self.assertEqual(perspective.provider, "local")
        self.assertEqual(perspective.model, "demo")

    def test_invalid_confidence_is_rejected(self):
        with self.assertRaises(ValueError):
            make_perspective(
                perspective_id="p1",
                provider="local",
                model="demo",
                response="answer",
                context=self.context,
                confidence=1.1,
            )

    def test_comparison_surfaces_dissent_without_winner(self):
        first = make_perspective(
            perspective_id="p1",
            provider="local",
            model="one",
            response="approve",
            context=self.context,
        )
        second = make_perspective(
            perspective_id="p2",
            provider="open",
            model="two",
            response="revise",
            context=self.context,
        )

        comparison = compare_perspectives([first, second])

        self.assertTrue(comparison["dissent"])
        self.assertEqual(comparison["preferred_interpretation"], None)
        self.assertEqual(comparison["context_hashes"], [self.context.content_hash])
        self.assertEqual(comparison["source_refs"], ["source-a"])

    def test_empty_comparison_is_explicit(self):
        comparison = compare_perspectives([])

        self.assertFalse(comparison["dissent"])
        self.assertEqual(comparison["preferred_interpretation"], None)


if __name__ == "__main__":
    unittest.main()

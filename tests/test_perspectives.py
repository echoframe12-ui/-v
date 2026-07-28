"""Tests for perspectives.py — provider-neutral perspective contracts.

Covers:
  - make_perspective: context lineage, invalid confidence, confidence boundaries,
    None confidence, metadata, source_refs from multi-source context, timestamp
  - compare_perspectives: dissent on different responses, no dissent on same responses,
    single perspective, empty list, deduplication of context_hashes, source_refs union,
    providers/models lists, preferred_interpretation always None
"""
import unittest

from context_assembly import ContextAssembler, ContextSource
from perspectives import compare_perspectives, make_perspective


def _ctx(*refs_contents):
    """Build a ContextAssembly from (ref, content) pairs."""
    sources = [ContextSource(ref=r, content=c) for r, c in refs_contents]
    return ContextAssembler().assemble(sources)


class MakePerspectiveTests(unittest.TestCase):

    def setUp(self):
        self.context = _ctx(("source-a", "Evidence A"))

    def test_perspective_preserves_context_lineage(self):
        p = make_perspective(
            perspective_id="p1", provider="local", model="demo",
            response="answer", context=self.context, confidence=0.8,
        )
        self.assertEqual(p.context_hash, self.context.content_hash)
        self.assertEqual(p.source_refs, ("source-a",))
        self.assertEqual(p.provider, "local")
        self.assertEqual(p.model, "demo")

    def test_invalid_confidence_above_one_is_rejected(self):
        with self.assertRaises(ValueError):
            make_perspective(
                perspective_id="p1", provider="local", model="demo",
                response="answer", context=self.context, confidence=1.1,
            )

    def test_invalid_confidence_below_zero_is_rejected(self):
        with self.assertRaises(ValueError):
            make_perspective(
                perspective_id="p1", provider="local", model="demo",
                response="answer", context=self.context, confidence=-0.01,
            )

    def test_confidence_zero_is_valid(self):
        p = make_perspective(
            perspective_id="p1", provider="local", model="demo",
            response="reject", context=self.context, confidence=0.0,
        )
        self.assertEqual(p.confidence, 0.0)

    def test_confidence_one_is_valid(self):
        p = make_perspective(
            perspective_id="p1", provider="local", model="demo",
            response="approve", context=self.context, confidence=1.0,
        )
        self.assertEqual(p.confidence, 1.0)

    def test_none_confidence_is_allowed(self):
        p = make_perspective(
            perspective_id="p1", provider="local", model="demo",
            response="answer", context=self.context,
        )
        self.assertIsNone(p.confidence)

    def test_metadata_is_preserved(self):
        p = make_perspective(
            perspective_id="p1", provider="local", model="demo",
            response="answer", context=self.context,
            metadata={"contract_id": "x.v1", "run": "42"},
        )
        self.assertEqual(p.metadata["contract_id"], "x.v1")
        self.assertEqual(p.metadata["run"], "42")

    def test_source_refs_from_multi_source_context(self):
        ctx = _ctx(("ref-1", "Content 1"), ("ref-2", "Content 2"))
        p = make_perspective(
            perspective_id="p1", provider="local", model="demo",
            response="answer", context=ctx,
        )
        self.assertEqual(set(p.source_refs), {"ref-1", "ref-2"})

    def test_timestamp_is_nonempty_iso_string(self):
        p = make_perspective(
            perspective_id="p1", provider="local", model="demo",
            response="answer", context=self.context,
        )
        self.assertTrue(p.timestamp)
        self.assertIn("T", p.timestamp)  # ISO 8601 format contains 'T'

    def test_perspective_id_propagated(self):
        p = make_perspective(
            perspective_id="unique-id-99", provider="local", model="demo",
            response="answer", context=self.context,
        )
        self.assertEqual(p.id, "unique-id-99")


class ComparePerspectivesTests(unittest.TestCase):

    def setUp(self):
        self.context = _ctx(("source-a", "Evidence A"))

    def _make(self, pid, response, model="m", provider="p", confidence=None):
        return make_perspective(
            perspective_id=pid, provider=provider, model=model,
            response=response, context=self.context, confidence=confidence,
        )

    def test_comparison_surfaces_dissent_without_winner(self):
        first = self._make("p1", "approve", model="one", provider="local")
        second = self._make("p2", "revise", model="two", provider="open")
        result = compare_perspectives([first, second])
        self.assertTrue(result["dissent"])
        self.assertIsNone(result["preferred_interpretation"])
        self.assertEqual(result["context_hashes"], [self.context.content_hash])
        self.assertEqual(result["source_refs"], ["source-a"])

    def test_identical_responses_produce_no_dissent(self):
        first = self._make("p1", "approve")
        second = self._make("p2", "approve")
        result = compare_perspectives([first, second])
        self.assertFalse(result["dissent"])
        self.assertIsNone(result["preferred_interpretation"])

    def test_single_perspective_has_no_dissent(self):
        result = compare_perspectives([self._make("p1", "approve")])
        self.assertFalse(result["dissent"])

    def test_empty_comparison_is_explicit(self):
        result = compare_perspectives([])
        self.assertFalse(result["dissent"])
        self.assertIsNone(result["preferred_interpretation"])
        self.assertEqual(result["context_hashes"], [])

    def test_providers_and_models_lists_in_comparison(self):
        first = self._make("p1", "approve", model="m1", provider="prov-a")
        second = self._make("p2", "revise", model="m2", provider="prov-b")
        result = compare_perspectives([first, second])
        self.assertIn("prov-a", result["providers"])
        self.assertIn("prov-b", result["providers"])
        self.assertIn("m1", result["models"])
        self.assertIn("m2", result["models"])

    def test_context_hashes_are_deduplicated(self):
        # Both perspectives share the same context
        first = self._make("p1", "approve")
        second = self._make("p2", "revise")
        result = compare_perspectives([first, second])
        self.assertEqual(len(result["context_hashes"]), 1)

    def test_source_refs_are_union_across_perspectives(self):
        ctx2 = _ctx(("ref-b", "Content B"))
        p1 = make_perspective(
            perspective_id="p1", provider="local", model="m1",
            response="approve", context=self.context,
        )
        p2 = make_perspective(
            perspective_id="p2", provider="open", model="m2",
            response="revise", context=ctx2,
        )
        result = compare_perspectives([p1, p2])
        self.assertIn("source-a", result["source_refs"])
        self.assertIn("ref-b", result["source_refs"])

    def test_preferred_interpretation_is_always_none(self):
        # Even with full agreement, no winner is declared
        perspectives = [self._make(f"p{i}", "approve", confidence=1.0) for i in range(5)]
        result = compare_perspectives(perspectives)
        self.assertIsNone(result["preferred_interpretation"])


if __name__ == "__main__":
    unittest.main()


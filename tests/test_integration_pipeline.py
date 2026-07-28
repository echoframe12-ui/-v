"""Tests for integration_pipeline.py — multi-adapter integration pipeline.

Covers:
  - Pipeline connects context, perspectives, and dissent comparison
  - Pipeline without adapters produces empty perspectives, no dissent
  - Single adapter produces no dissent (unanimous)
  - Context hash matches across comparison
  - Result structure has all expected fields
"""
import unittest

from context_assembly import ContextSource
from integration_pipeline import IntegrationPipeline
from perspectives import make_perspective


class StubAdapter:
    def __init__(self, provider, model, response):
        self.provider = provider
        self.model = model
        self.response = response

    def generate(self, context):
        return make_perspective(
            perspective_id=f"{self.provider}:{self.model}",
            provider=self.provider,
            model=self.model,
            response=self.response,
            context=context,
        )


class IntegrationPipelineTests(unittest.TestCase):

    def test_pipeline_connects_context_perspectives_and_dissent(self):
        pipeline = IntegrationPipeline(
            adapters=[
                StubAdapter("local", "model-a", "approve"),
                StubAdapter("open", "model-b", "revise"),
                StubAdapter("hosted", "model-c", "approve"),
            ]
        )

        result = pipeline.run(
            [ContextSource(ref="source", content="Evidence", authority="test")]
        )

        self.assertEqual(result.context.included_refs, ("source",))
        self.assertEqual(len(result.perspectives), 3)
        self.assertTrue(result.comparison["dissent"])
        self.assertEqual(result.comparison["preferred_interpretation"], None)
        self.assertEqual(
            result.comparison["context_hashes"],
            [result.context.content_hash],
        )

    def test_pipeline_without_adapters_is_explicit(self):
        result = IntegrationPipeline([]).run(
            [ContextSource(ref="source", content="Evidence")]
        )

        self.assertEqual(result.perspectives, ())
        self.assertFalse(result.comparison["dissent"])
        self.assertIsNone(result.comparison["preferred_interpretation"])

    def test_single_adapter_no_dissent(self):
        pipeline = IntegrationPipeline(
            adapters=[StubAdapter("local", "model-a", "approve")]
        )
        result = pipeline.run(
            [ContextSource(ref="s1", content="data")]
        )
        self.assertEqual(len(result.perspectives), 1)
        self.assertFalse(result.comparison["dissent"])

    def test_context_hash_matches(self):
        pipeline = IntegrationPipeline(
            adapters=[StubAdapter("local", "model-a", "ok")]
        )
        result = pipeline.run(
            [ContextSource(ref="s1", content="data")]
        )
        self.assertTrue(result.context.content_hash)
        self.assertEqual(
            result.comparison["context_hashes"][0],
            result.context.content_hash,
        )

    def test_result_has_context_perspectives_comparison(self):
        pipeline = IntegrationPipeline(
            adapters=[StubAdapter("local", "model-a", "ok")]
        )
        result = pipeline.run(
            [ContextSource(ref="s1", content="data")]
        )
        self.assertTrue(hasattr(result, "context"))
        self.assertTrue(hasattr(result, "perspectives"))
        self.assertTrue(hasattr(result, "comparison"))


if __name__ == "__main__":
    unittest.main()


"""Tests for stack_runner.py — OceanicStack end-to-end integration runner.

Covers:
  - Full verified run produces attested Attestation and ACT authorization
  - Verified run authorizes proposals
  - Dissent routes authorization to HUMAN_REVIEW with requires_human=True
  - Empty pipeline run produces held verification and HOLD authorization
  - Proposal routing under HOLD status yields 'held' status
"""
import unittest

from authorization import ActionLevel
from context_assembly import ContextSource
from integration_pipeline import IntegrationPipeline
from perspectives import make_perspective
from proactive import Proposal
from stack_runner import OceanicStack


class Adapter:
    def __init__(self, provider, model, response, confidence):
        self.provider = provider
        self.model = model
        self.response = response
        self.confidence = confidence

    def generate(self, context):
        return make_perspective(
            perspective_id=f"{self.provider}:{self.model}",
            provider=self.provider,
            model=self.model,
            response=self.response,
            context=context,
            confidence=self.confidence,
        )


class OceanicStackTests(unittest.TestCase):

    def test_stack_runner_produces_attested_and_authorized_run(self):
        stack = OceanicStack(
            IntegrationPipeline(
                [
                    Adapter("local", "a", "same", 0.95),
                    Adapter("open", "b", "same", 0.95),
                    Adapter("hosted", "c", "same", 0.95),
                ]
            )
        )

        run = stack.run([
            ContextSource(ref="source", content="Observed evidence", authority="test")
        ])

        self.assertEqual(run.verification.status, "verified")
        self.assertIsNotNone(run.attestation)
        self.assertEqual(run.authorization.level, ActionLevel.ACT)
        self.assertEqual(run.attestation.provenance, ("source",))

        proposal = Proposal(
            id="proposal-1",
            trigger="observation-1",
            hypothesis="take next step",
            evidence_refs=run.attestation.provenance,
        )
        routed = stack.route_proposal(run, proposal)
        self.assertEqual(routed.status, "authorized")

    def test_stack_runner_routes_dissent_to_human_review(self):
        stack = OceanicStack(
            IntegrationPipeline(
                [
                    Adapter("local", "a", "approve", 0.95),
                    Adapter("open", "b", "revise", 0.95),
                    Adapter("hosted", "c", "approve", 0.95),
                ]
            )
        )

        run = stack.run([
            ContextSource(ref="source", content="Observed evidence", authority="test")
        ])

        self.assertTrue(run.verification.dissent)
        self.assertEqual(run.authorization.level, ActionLevel.HUMAN_REVIEW)
        self.assertTrue(run.authorization.requires_human)

    def test_empty_pipeline_produces_held_and_no_attestation(self):
        stack = OceanicStack(IntegrationPipeline([]))
        run = stack.run([])
        self.assertEqual(run.verification.status, "held")
        self.assertIsNone(run.attestation)
        self.assertEqual(run.authorization.level, ActionLevel.HOLD)

    def test_proposal_routed_under_hold_is_held(self):
        stack = OceanicStack(IntegrationPipeline([]))
        run = stack.run([])
        proposal = Proposal(id="p1", trigger="t1", hypothesis="h1", evidence_refs=())
        routed = stack.route_proposal(run, proposal)
        self.assertEqual(routed.status, "held")


if __name__ == "__main__":
    unittest.main()


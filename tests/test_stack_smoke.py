"""Tests for full end-to-end stack smoke tests.

Covers:
  - Source to proactive authorized state (unanimous agreement)
  - Dissent stops autonomous action and routes to human review
  - Empty context produces held status and stops action
  - Failed check produces held status and prevents attestation
  - Dissent proposal routing yields human_review status
"""
import unittest

from authorization import ActionLevel, AuthorizationGate
from context_assembly import ContextSource
from integration_pipeline import IntegrationPipeline
from perspectives import make_perspective
from proactive import Proposal, ProactiveEngine
from verification_pipeline import VerificationCheck, VerificationPipeline


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


class FullStackSmokeTest(unittest.TestCase):

    def test_source_to_proactive_authorized_state(self):
        integration = IntegrationPipeline(
            [
                Adapter("local", "a", "same", 0.95),
                Adapter("open", "b", "same", 0.95),
                Adapter("hosted", "c", "same", 0.95),
            ]
        ).run([
            ContextSource(ref="source", content="Observed evidence", authority="test")
        ])

        verification = VerificationPipeline().verify(integration)
        self.assertEqual(verification.status, "verified")

        attestation = VerificationPipeline().attest(verification)
        self.assertEqual(attestation.status, "attested")

        authorization = AuthorizationGate().decide(verification)
        self.assertEqual(authorization.level, ActionLevel.ACT)

        proposal = Proposal(
            id="proposal-1",
            trigger="observation-1",
            hypothesis="take the next bounded step",
            evidence_refs=attestation.provenance,
        )
        routed = ProactiveEngine.route(proposal, authorization)
        self.assertEqual(routed.status, "authorized")
        self.assertEqual(routed.authorization.verification_hash, verification.result_hash)

    def test_dissent_stops_autonomous_action_and_routes_to_review(self):
        integration = IntegrationPipeline(
            [
                Adapter("local", "a", "approve", 0.95),
                Adapter("open", "b", "revise", 0.95),
                Adapter("hosted", "c", "approve", 0.95),
            ]
        ).run([
            ContextSource(ref="source", content="Observed evidence", authority="test")
        ])

        verification = VerificationPipeline().verify(integration)
        authorization = AuthorizationGate().decide(verification)

        self.assertTrue(verification.dissent)
        self.assertEqual(authorization.level, ActionLevel.HUMAN_REVIEW)
        self.assertTrue(authorization.requires_human)

    def test_empty_context_fails_verification(self):
        integration = IntegrationPipeline([]).run([])
        verification = VerificationPipeline().verify(integration)
        self.assertEqual(verification.status, "held")
        self.assertIsNone(verification.confidence)
        authorization = AuthorizationGate().decide(verification)
        self.assertEqual(authorization.level, ActionLevel.HOLD)

    def test_failed_custom_check_holds_entire_stack(self):
        integration = IntegrationPipeline(
            [Adapter("local", "a", "same", 0.95)]
        ).run([ContextSource(ref="source", content="Evidence")])

        verification = VerificationPipeline(
            checks=[lambda _: VerificationCheck("gatekeeper", False, "failed")]
        ).verify(integration)

        self.assertEqual(verification.status, "held")
        authorization = AuthorizationGate().decide(verification)
        self.assertEqual(authorization.level, ActionLevel.HOLD)

    def test_dissent_proposal_routes_to_human_review(self):
        integration = IntegrationPipeline(
            [
                Adapter("local", "a", "approve", 0.95),
                Adapter("open", "b", "revise", 0.95),
            ]
        ).run([ContextSource(ref="src", content="ev")])

        verification = VerificationPipeline().verify(integration)
        authorization = AuthorizationGate().decide(verification)
        proposal = Proposal("p1", "trig", "hyp", ())
        routed = ProactiveEngine.route(proposal, authorization)
        self.assertEqual(routed.status, "human_review")


if __name__ == "__main__":
    unittest.main()


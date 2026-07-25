import unittest

from authorization import ActionLevel, AuthorizationGate
from context_assembly import ContextSource
from integration_pipeline import IntegrationPipeline
from perspectives import make_perspective
from proactive import Proposal, ProactiveEngine
from verification_pipeline import VerificationPipeline


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


if __name__ == "__main__":
    unittest.main()

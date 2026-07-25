import unittest

from authorization import ActionLevel, AuthorizationDecision
from observer import Observer
from verification_pipeline import Attestation, VerificationCheck, VerificationResult
from stack_runner import StackRun


class ObserverTests(unittest.TestCase):
    def run(self, status="verified", level=ActionLevel.ACT, confidence=0.95, dissent=False, attested=True):
        verification = VerificationResult(
            status=status,
            confidence=confidence,
            checks=(VerificationCheck("evidence", True),),
            dissent=dissent,
            provenance=("source",),
            result_hash="hash-123",
        )
        attestation = (
            Attestation("hash-123", "attested", confidence, ("source",), "Attested")
            if attested else None
        )
        authorization = AuthorizationDecision(
            level=level,
            reason="test",
            verification_hash="hash-123",
            requires_human=level == ActionLevel.HUMAN_REVIEW,
        )
        return StackRun(None, verification, attestation, authorization)

    def test_authorized_run_becomes_next_observation(self):
        observation = Observer().observe(self.run())
        self.assertEqual(observation.state, "authorized")
        self.assertEqual(observation.next_state, "act_then_observe")
        self.assertTrue(observation.attested)
        self.assertEqual(observation.verification_hash, "hash-123")

    def test_dissent_routes_to_human_review(self):
        observation = Observer().observe(
            self.run(level=ActionLevel.HUMAN_REVIEW, dissent=True)
        )
        self.assertEqual(observation.state, "human_review")
        self.assertEqual(observation.next_state, "await_human")
        self.assertTrue(observation.dissent)

    def test_held_run_returns_to_verification(self):
        observation = Observer().observe(
            self.run(status="held", level=ActionLevel.HOLD, attested=False)
        )
        self.assertEqual(observation.state, "held")
        self.assertEqual(observation.next_state, "verify_again")
        self.assertFalse(observation.attested)

    def test_projection_is_serializable(self):
        observation = Observer().observe(self.run())
        payload = Observer.to_dict(observation)
        self.assertEqual(payload["state"], "authorized")
        self.assertEqual(payload["provenance"], ["source"])


if __name__ == "__main__":
    unittest.main()

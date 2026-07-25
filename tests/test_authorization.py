import unittest

from authorization import ActionLevel, AuthorizationGate, AuthorizationPolicy
from verification_pipeline import VerificationResult, VerificationCheck


class AuthorizationTests(unittest.TestCase):
    def _verification(self, status="verified", confidence=0.8, dissent=False):
        return VerificationResult(
            status=status,
            confidence=confidence,
            checks=(VerificationCheck("evidence", True),),
            dissent=dissent,
            provenance=("source",),
            result_hash="abc123",
        )

    def test_unverified_result_is_held(self):
        decision = AuthorizationGate().decide(self._verification(status="held"))
        self.assertEqual(decision.level, ActionLevel.HOLD)
        self.assertTrue(decision.requires_human)

    def test_dissent_routes_to_human_review(self):
        decision = AuthorizationGate().decide(self._verification(dissent=True))
        self.assertEqual(decision.level, ActionLevel.HUMAN_REVIEW)
        self.assertTrue(decision.requires_human)

    def test_medium_confidence_allows_proposal_not_action(self):
        decision = AuthorizationGate().decide(self._verification(confidence=0.80))
        self.assertEqual(decision.level, ActionLevel.PROPOSE)
        self.assertFalse(decision.requires_human)

    def test_high_confidence_allows_action(self):
        decision = AuthorizationGate().decide(self._verification(confidence=0.95))
        self.assertEqual(decision.level, ActionLevel.ACT)

    def test_low_confidence_reports_only(self):
        decision = AuthorizationGate().decide(self._verification(confidence=0.50))
        self.assertEqual(decision.level, ActionLevel.REPORT)

    def test_missing_confidence_reports_only(self):
        decision = AuthorizationGate().decide(self._verification(confidence=None))
        self.assertEqual(decision.level, ActionLevel.REPORT)

    def test_invalid_thresholds_are_rejected(self):
        with self.assertRaises(ValueError):
            AuthorizationGate(AuthorizationPolicy(0.95, 0.80))


if __name__ == "__main__":
    unittest.main()

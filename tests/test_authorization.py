"""Tests for authorization.py — explicit authorization gate.

Covers:
  - ActionLevel decision mapping (HOLD, HUMAN_REVIEW, PROPOSE, ACT, REPORT)
  - Policy validations (invalid range <0/>1, proposal > action)
  - Custom require_human_for_dissent=False policy override
  - ActionLevel enum string representation and values
  - AuthorizationDecision field verification
  - Exact boundary thresholds for proposal and action confidence
"""
import unittest

from authorization import ActionLevel, AuthorizationDecision, AuthorizationGate, AuthorizationPolicy
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

    def test_negative_or_over_one_thresholds_rejected(self):
        with self.assertRaises(ValueError):
            AuthorizationGate(AuthorizationPolicy(-0.1, 0.90))
        with self.assertRaises(ValueError):
            AuthorizationGate(AuthorizationPolicy(0.70, 1.1))

    def test_dissent_without_human_requirement(self):
        policy = AuthorizationPolicy(require_human_for_dissent=False)
        gate = AuthorizationGate(policy)
        decision = gate.decide(self._verification(confidence=0.95, dissent=True))
        self.assertEqual(decision.level, ActionLevel.ACT)

    def test_action_level_enum_values(self):
        self.assertEqual(ActionLevel.REPORT, "report")
        self.assertEqual(ActionLevel.HUMAN_REVIEW, "human_review")
        self.assertEqual(ActionLevel.PROPOSE, "propose")
        self.assertEqual(ActionLevel.ACT, "act")
        self.assertEqual(ActionLevel.HOLD, "hold")

    def test_exact_threshold_boundaries(self):
        policy = AuthorizationPolicy(proposal_confidence=0.74, action_confidence=0.90)
        gate = AuthorizationGate(policy)
        d_prop = gate.decide(self._verification(confidence=0.74))
        self.assertEqual(d_prop.level, ActionLevel.PROPOSE)
        d_act = gate.decide(self._verification(confidence=0.90))
        self.assertEqual(d_act.level, ActionLevel.ACT)

    def test_decision_fields(self):
        decision = AuthorizationGate().decide(self._verification(confidence=0.95))
        self.assertIsInstance(decision, AuthorizationDecision)
        self.assertEqual(decision.verification_hash, "abc123")
        self.assertTrue(decision.reason)


if __name__ == "__main__":
    unittest.main()


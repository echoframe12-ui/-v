"""Tests for proactive.py — proactive proposal generation and routing.

Covers:
  - ProactiveEngine generator aggregation
  - Route statuses for ACT (authorized), PROPOSE (awaiting_confirmation), HUMAN_REVIEW (human_review), HOLD (held), REPORT (report_only)
  - Proposal dataclass default fields
  - ProposalDecision dataclass fields
"""
import unittest

from authorization import ActionLevel, AuthorizationDecision
from proactive import Proposal, ProposalDecision, ProactiveEngine


class ProactiveTests(unittest.TestCase):

    def setUp(self):
        self.proposal = Proposal(
            id="p1",
            trigger="observation-1",
            hypothesis="prepare a safer next step",
            evidence_refs=("source",),
            expected_value=0.8,
            risk=0.2,
        )

    def decision(self, level):
        return AuthorizationDecision(
            level=level,
            reason="test",
            verification_hash="hash",
            requires_human=level == ActionLevel.HUMAN_REVIEW,
        )

    def test_generator_produces_proposals(self):
        engine = ProactiveEngine(
            [lambda observation: [self.proposal] if observation == "observe" else []]
        )
        proposals = engine.propose("observe")
        self.assertEqual(proposals, (self.proposal,))

    def test_multiple_generators_combine_results(self):
        p2 = Proposal("p2", "trigger2", "hypothesis2", ())
        g1 = lambda obs: [self.proposal]
        g2 = lambda obs: [p2]
        engine = ProactiveEngine([g1, g2])
        self.assertEqual(engine.propose("any"), (self.proposal, p2))

    def test_proposal_requires_confirmation_at_propose_level(self):
        routed = ProactiveEngine.route(self.proposal, self.decision(ActionLevel.PROPOSE))
        self.assertEqual(routed.status, "awaiting_confirmation")

    def test_dissent_routes_proposal_to_human_review(self):
        routed = ProactiveEngine.route(self.proposal, self.decision(ActionLevel.HUMAN_REVIEW))
        self.assertEqual(routed.status, "human_review")

    def test_hold_blocks_proposal(self):
        routed = ProactiveEngine.route(self.proposal, self.decision(ActionLevel.HOLD))
        self.assertEqual(routed.status, "held")

    def test_act_authorizes_proposal(self):
        routed = ProactiveEngine.route(self.proposal, self.decision(ActionLevel.ACT))
        self.assertEqual(routed.status, "authorized")

    def test_report_level_routes_to_report_only(self):
        routed = ProactiveEngine.route(self.proposal, self.decision(ActionLevel.REPORT))
        self.assertEqual(routed.status, "report_only")

    def test_proposal_defaults(self):
        p = Proposal("id1", "trig1", "hyp1", ())
        self.assertIsNone(p.expected_value)
        self.assertIsNone(p.risk)
        self.assertIsNone(p.metadata)

    def test_proposal_decision_structure(self):
        dec = self.decision(ActionLevel.ACT)
        routed = ProactiveEngine.route(self.proposal, dec)
        self.assertIsInstance(routed, ProposalDecision)
        self.assertEqual(routed.proposal, self.proposal)
        self.assertEqual(routed.authorization, dec)
        self.assertTrue(routed.reason)


if __name__ == "__main__":
    unittest.main()


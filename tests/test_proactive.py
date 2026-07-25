import unittest

from authorization import ActionLevel, AuthorizationDecision
from proactive import Proposal, ProactiveEngine


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


if __name__ == "__main__":
    unittest.main()

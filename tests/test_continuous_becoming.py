import unittest

from authorization import ActionLevel, AuthorizationDecision
from continuous_becoming import ContinuousBecomingEngine
from observer import Observation
from verification_pipeline import Attestation


class ContinuousBecomingTests(unittest.TestCase):
    def observation(self, state="authorized", next_state="act_then_observe", attested=True):
        return Observation(
            state=state,
            verification_status="verified" if state != "held" else "held",
            authorization_level=ActionLevel.ACT.value if state == "authorized" else ActionLevel.HUMAN_REVIEW.value,
            confidence=0.95,
            dissent=False,
            provenance=("source",),
            verification_hash="hash-123",
            attested=attested,
            next_state=next_state,
        )

    def test_authorized_run_continues_becoming(self):
        transition = ContinuousBecomingEngine().advance(self.observation())
        self.assertEqual(transition.current_state, "authorized")
        self.assertEqual(transition.next_state, "act_then_observe")
        self.assertEqual(transition.action, "continue_becoming")
        self.assertTrue(transition.loop)

    def test_human_review_loops_back(self):
        observation = self.observation(state="human_review", next_state="await_human", attested=True)
        transition = ContinuousBecomingEngine().advance(observation)
        self.assertEqual(transition.action, "await_human")
        self.assertEqual(transition.next_state, "await_human")

    def test_held_run_reverifies(self):
        observation = self.observation(state="held", next_state="verify_again", attested=False)
        transition = ContinuousBecomingEngine().advance(observation)
        self.assertEqual(transition.action, "reverify")
        self.assertEqual(transition.next_state, "verify_again")

    def test_projection_is_serializable(self):
        transition = ContinuousBecomingEngine().advance(self.observation())
        payload = ContinuousBecomingEngine.to_dict(transition)
        self.assertEqual(payload["current_state"], "authorized")
        self.assertEqual(payload["provenance"], ["source"])


if __name__ == "__main__":
    unittest.main()

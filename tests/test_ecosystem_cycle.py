import unittest

from context_assembly import ContextSource
from ecosystem_cycle import EcosystemCycleEngine
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


class EcosystemCycleTests(unittest.TestCase):
    def test_cycle_consensus_path(self):
        stack = OceanicStack(
            IntegrationPipeline(
                [
                    Adapter("local", "a", "same", 0.95),
                    Adapter("open", "b", "same", 0.95),
                    Adapter("hosted", "c", "same", 0.95),
                ]
            )
        )
        cycle = EcosystemCycleEngine(stack).run(
            [ContextSource(ref="source", content="Observed evidence", authority="test")]
        )

        self.assertEqual(cycle.stack_run.verification.status, "verified")
        self.assertEqual(cycle.observation.state, "authorized")
        self.assertEqual(cycle.transition.action, "continue_becoming")
        self.assertTrue(cycle.stack_run.attestation is not None)

        payload = EcosystemCycleEngine.to_dict(cycle)
        self.assertEqual(payload["observation"]["state"], "authorized")
        self.assertEqual(payload["transition"]["action"], "continue_becoming")

    def test_cycle_dissent_path_routes_to_human_review(self):
        stack = OceanicStack(
            IntegrationPipeline(
                [
                    Adapter("local", "a", "approve", 0.95),
                    Adapter("open", "b", "revise", 0.95),
                    Adapter("hosted", "c", "approve", 0.95),
                ]
            )
        )
        cycle = EcosystemCycleEngine(stack).run(
            [ContextSource(ref="source", content="Observed evidence", authority="test")]
        )

        self.assertEqual(cycle.stack_run.authorization.level.value, "human_review")
        self.assertEqual(cycle.observation.state, "human_review")
        self.assertEqual(cycle.transition.action, "await_human")
        self.assertTrue(cycle.observation.dissent)

    def test_cycle_with_no_perspectives_is_held(self):
        stack = OceanicStack(IntegrationPipeline([]))
        cycle = EcosystemCycleEngine(stack).run([])

        self.assertEqual(cycle.stack_run.verification.status, "held")
        self.assertEqual(cycle.observation.state, "held")
        self.assertEqual(cycle.transition.action, "reverify")
        self.assertIsNone(cycle.stack_run.attestation)


if __name__ == "__main__":
    unittest.main()

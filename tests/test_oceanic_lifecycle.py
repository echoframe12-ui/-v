import tempfile
import unittest
from pathlib import Path

from oceanic_event_ledger import EventLedger
from oceanic_ir import OceanicIRContract
from oceanic_lifecycle import OceanicLifecycle
from oceanic_orchestrator import OceanicOrchestrator, default_adapters


class OceanicLifecycleTests(unittest.TestCase):
    def contract(self):
        return OceanicIRContract(
            api_version="oceanic.ir/v0.1",
            contract_id="lifecycle.add.v1",
            intent="combine two numeric values",
            inputs=(
                {"name": "a", "type": "integer"},
                {"name": "b", "type": "integer"},
            ),
            outputs={"type": "integer"},
            invariants=("result == mathematical_sum(a, b)",),
            effects=(),
            bounds={"time": "O(1)", "memory": "O(1)"},
            dependencies=(),
            proof_obligations=("arithmetic_correctness", "overflow_handling"),
            dissent_triggers=("overflow",),
            risk={"class": "low", "human_authorization": False},
        )

    def test_matching_lifecycle_is_recorded_without_evolution(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger = EventLedger(Path(directory) / "events.jsonl")
            lifecycle = OceanicLifecycle(OceanicOrchestrator(default_adapters()), ledger)
            result = lifecycle.run(
                self.contract(),
                reviewer="lifecycle-test",
                authorization_reason="Approved for deterministic lifecycle test.",
                execute=lambda: 4,
                expected=4,
            )

            self.assertEqual(result.observation.status, "matched")
            self.assertIsNone(result.evolution)
            self.assertTrue(ledger.verify_chain())
            self.assertEqual(
                [event.event_type for event in ledger.history()],
                [
                    "contract.created",
                    "verification.completed",
                    "attestation.created",
                    "authorization.granted",
                    "runtime.observed",
                    "observation.matched",
                ],
            )

    def test_deviation_creates_evolution_and_review_events(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger = EventLedger(Path(directory) / "events.jsonl")
            lifecycle = OceanicLifecycle(OceanicOrchestrator(default_adapters()), ledger)
            result = lifecycle.run(
                self.contract(),
                reviewer="lifecycle-test",
                authorization_reason="Approved for deviation testing.",
                execute=lambda: 5,
                expected=4,
            )

            self.assertEqual(result.observation.status, "deviated")
            self.assertIsNotNone(result.evolution)
            self.assertTrue(result.evolution.requires_human_review)
            self.assertTrue(ledger.verify_chain())
            event_types = [event.event_type for event in ledger.history()]
            self.assertIn("evolution.proposed", event_types)
            self.assertIn("human.review.required", event_types)


if __name__ == "__main__":
    unittest.main()

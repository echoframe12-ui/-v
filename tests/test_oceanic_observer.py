import unittest

from oceanic_attestation import create_attestation
from oceanic_authorization import authorize
from oceanic_ir import OceanicIRContract
from oceanic_observer import ExecutionDenied, execute_and_observe
from oceanic_orchestrator import OceanicOrchestrator, default_adapters


class OceanicObserverTests(unittest.TestCase):
    def setUp(self):
        contract = OceanicIRContract(
            api_version="oceanic.ir/v0.1",
            contract_id="example.add.v1",
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
        report = OceanicOrchestrator(default_adapters()).run(contract)
        attestation = create_attestation(report)
        self.authorized = authorize(
            attestation,
            reviewer="observer-test",
            reason="Approved for deterministic observer testing.",
        )
        self.pending = attestation

    def test_execution_requires_authorization(self):
        with self.assertRaises(ExecutionDenied):
            execute_and_observe(self.pending, execute=lambda: 4, expected=4)

    def test_matching_runtime_is_observed(self):
        updated, observation = execute_and_observe(
            self.authorized, execute=lambda: 4, expected=4
        )
        self.assertEqual(observation.status, "matched")
        self.assertEqual(observation.actual, 4)
        self.assertEqual(observation.deviations, ())
        self.assertEqual(updated.runtime.status, "observed")

    def test_deviation_becomes_learning_signal(self):
        _, observation = execute_and_observe(
            self.authorized, execute=lambda: 5, expected=4
        )
        self.assertEqual(observation.status, "deviated")
        self.assertTrue(observation.deviations)


if __name__ == "__main__":
    unittest.main()

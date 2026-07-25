import unittest

from oceanic_ir import ContractState, OceanicIRContract
from oceanic_orchestrator import OceanicOrchestrator, default_adapters


class OceanicOrchestratorTests(unittest.TestCase):
    def setUp(self):
        self.contract = OceanicIRContract(
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

    def test_three_adapters_produce_one_consolidated_report(self):
        report = OceanicOrchestrator(default_adapters()).run(self.contract)

        self.assertEqual(report.contract_id, "example.add.v1")
        self.assertEqual(len(report.runs), 3)
        self.assertEqual(report.overall_status, ContractState.PROVED_WITH_DISSENT)
        self.assertGreaterEqual(report.confidence, 0.9)
        self.assertEqual(
            {run.language for run in report.runs},
            {"python", "rust", "typescript"},
        )
        self.assertTrue(any("python:" in item for item in report.dissent))
        self.assertTrue(any("typescript:" in item for item in report.dissent))

    def test_empty_adapter_set_is_unproven(self):
        report = OceanicOrchestrator(()).run(self.contract)
        self.assertEqual(report.overall_status, ContractState.UNPROVEN)
        self.assertEqual(report.confidence, 0.0)
        self.assertIn("no adapters available", report.dissent)


if __name__ == "__main__":
    unittest.main()

import unittest

from adapters.python_adapter import compile_contract, prove_contract
from oceanic_ir import ContractState, OceanicIRContract, OceanicIRValidator


class PythonAdapterTests(unittest.TestCase):
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

    def test_compile_and_prove(self):
        artifact = compile_contract(self.contract)
        self.assertIn("def combine", artifact.source)

        proof = prove_contract(self.contract, artifact)
        outcome = OceanicIRValidator().verify(self.contract, proof)

        self.assertEqual(outcome.status, ContractState.PROVED_WITH_DISSENT)
        self.assertEqual(outcome.missing_obligations, ())
        self.assertIn("overflow guarantee relies on Python integer semantics rather than a static numeric bound", outcome.dissent)


if __name__ == "__main__":
    unittest.main()

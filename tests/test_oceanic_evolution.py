import unittest

from oceanic_attestation import create_attestation
from oceanic_authorization import authorize
from oceanic_evolution import propose_evolution
from oceanic_ir import OceanicIRContract
from oceanic_observer import execute_and_observe
from oceanic_orchestrator import OceanicOrchestrator, default_adapters


class OceanicEvolutionTests(unittest.TestCase):
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
        attestation = authorize(
            create_attestation(report),
            reviewer="evolution-test",
            reason="Approved for evolution testing.",
        )
        self.attestation = attestation

    def test_matching_observation_produces_no_proposal(self):
        _, observation = execute_and_observe(
            self.attestation, execute=lambda: 4, expected=4
        )
        self.assertIsNone(propose_evolution(self.attestation, observation))

    def test_deviation_produces_reviewable_proposal(self):
        _, observation = execute_and_observe(
            self.attestation, execute=lambda: 5, expected=4
        )
        proposal = propose_evolution(self.attestation, observation)
        self.assertIsNotNone(proposal)
        self.assertEqual(proposal.category, "contract_runtime_deviation")
        self.assertTrue(proposal.requires_human_review)
        self.assertEqual(proposal.attestation_id, self.attestation.attestation_id)
        self.assertTrue(proposal.proposal_id.startswith("evo_"))

    def test_proposal_does_not_mutate_historical_attestation(self):
        original_digest = self.attestation.digest()
        _, observation = execute_and_observe(
            self.attestation, execute=lambda: 5, expected=4
        )
        propose_evolution(self.attestation, observation)
        self.assertEqual(self.attestation.digest(), original_digest)


if __name__ == "__main__":
    unittest.main()

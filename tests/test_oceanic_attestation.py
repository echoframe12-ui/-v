import unittest

from oceanic_attestation import Authorization, create_attestation
from oceanic_ir import OceanicIRContract
from oceanic_orchestrator import OceanicOrchestrator, default_adapters


class OceanicAttestationTests(unittest.TestCase):
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

    def test_attestation_preserves_verification_evidence(self):
        report = OceanicOrchestrator(default_adapters()).run(self.contract)
        attestation = create_attestation(
            report,
            authorization=Authorization(status="pending", authority="human"),
        )

        self.assertEqual(attestation.schema, "oceanic.attestation/v0.1")
        self.assertEqual(attestation.contract_id, "example.add.v1")
        self.assertEqual(len(attestation.adapters), 3)
        self.assertEqual(attestation.aggregate["status"], "proved_with_dissent")
        self.assertEqual(attestation.authorization.status, "pending")
        self.assertEqual(attestation.runtime.status, "not_started")
        self.assertTrue(attestation.digest().startswith("sha256:"))
        self.assertTrue(any("python:" in item for item in attestation.aggregate["dissent"]))

    def test_attestation_digest_is_deterministic_for_same_record(self):
        report = OceanicOrchestrator(default_adapters()).run(self.contract)
        attestation = create_attestation(report)
        self.assertEqual(attestation.digest(), attestation.digest())


if __name__ == "__main__":
    unittest.main()

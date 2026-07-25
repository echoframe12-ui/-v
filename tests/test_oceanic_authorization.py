import unittest

from oceanic_attestation import Authorization, create_attestation
from oceanic_authorization import AuthorizationError, authorize, can_execute, reject
from oceanic_ir import OceanicIRContract
from oceanic_orchestrator import OceanicOrchestrator, default_adapters


class OceanicAuthorizationTests(unittest.TestCase):
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
        self.attestation = create_attestation(
            report, authorization=Authorization(status="pending")
        )

    def test_pending_attestation_cannot_execute(self):
        self.assertFalse(can_execute(self.attestation))

    def test_human_can_authorize_verified_attestation(self):
        authorized = authorize(
            self.attestation,
            reviewer="human-reviewer",
            reason="Reviewed dissent and accepted bounded runtime behavior.",
        )
        self.assertEqual(authorized.authorization.status, "authorized")
        self.assertTrue(can_execute(authorized))
        self.assertEqual(authorized.contract_id, self.attestation.contract_id)

    def test_rejection_blocks_execution(self):
        rejected = reject(
            self.attestation,
            reviewer="human-reviewer",
            reason="Dissent requires additional evidence.",
        )
        self.assertEqual(rejected.authorization.status, "rejected")
        self.assertFalse(can_execute(rejected))

    def test_invalid_authorization_is_rejected(self):
        with self.assertRaises(AuthorizationError):
            authorize(self.attestation, reviewer="", reason="missing reviewer")


if __name__ == "__main__":
    unittest.main()

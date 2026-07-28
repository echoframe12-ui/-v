"""Tests for Oceanic Attestation — durable, tamper-evident verification evidence.

Covers:
  - Schema, contract_id, adapter count, aggregate status (proved_with_dissent)
  - Digest is sha256-prefixed and deterministic for same record
  - No-dissent contract produces 'proved' aggregate status
  - All-failing adapters produce 'not_proved' aggregate status
  - attestation_id is 'att_'-prefixed
  - to_dict includes attestation_digest key
  - Zero proof obligations → full confidence, no dissent
  - Aggregate confidence matches CompilationReport confidence
  - Default authorization is pending
"""
import unittest

from oceanic_attestation import Authorization, create_attestation
from oceanic_ir import OceanicIRContract
from oceanic_orchestrator import ContractAdapter, OceanicOrchestrator, default_adapters


def _make_contract(contract_id: str = "example.add.v1", proof_obligations=None) -> OceanicIRContract:
    if proof_obligations is None:
        proof_obligations = ("arithmetic_correctness", "overflow_handling")
    return OceanicIRContract(
        api_version="oceanic.ir/v0.1",
        contract_id=contract_id,
        intent="combine two numeric values",
        inputs=({"name": "a", "type": "integer"}, {"name": "b", "type": "integer"}),
        outputs={"type": "integer"},
        invariants=("result == mathematical_sum(a, b)",),
        effects=(),
        bounds={"time": "O(1)", "memory": "O(1)"},
        dependencies=(),
        proof_obligations=proof_obligations,
        dissent_triggers=("overflow",),
        risk={"class": "low", "human_authorization": False},
    )


class OceanicAttestationTests(unittest.TestCase):
    def setUp(self):
        self.contract = _make_contract()
        self.report = OceanicOrchestrator(default_adapters()).run(self.contract)
        self.attestation = create_attestation(self.report)

    def test_attestation_preserves_verification_evidence(self):
        attestation = create_attestation(
            self.report,
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
        self.assertEqual(self.attestation.digest(), self.attestation.digest())

    def test_no_dissent_contract_produces_proved_status(self):
        # Only arithmetic_correctness: all 3 default adapters support it → no dissent
        contract = _make_contract(proof_obligations=("arithmetic_correctness",))
        report = OceanicOrchestrator(default_adapters()).run(contract)
        attestation = create_attestation(report)
        self.assertEqual(attestation.aggregate["status"], "proved")
        self.assertEqual(attestation.aggregate["dissent"], [])

    def test_all_failing_adapters_produce_not_proved(self):
        # An obligation no adapter supports → all fail
        contract = _make_contract(proof_obligations=("impossible_obligation",))
        # Use adapters with no capabilities
        adapters = (
            ContractAdapter("empty-a", capabilities=()),
            ContractAdapter("empty-b", capabilities=()),
        )
        report = OceanicOrchestrator(adapters).run(contract)
        attestation = create_attestation(report)
        self.assertEqual(attestation.aggregate["status"], "not_proved")

    def test_attestation_id_is_att_prefixed(self):
        self.assertTrue(self.attestation.attestation_id.startswith("att_"))
        self.assertEqual(len(self.attestation.attestation_id), len("att_") + 24)

    def test_to_dict_includes_attestation_digest(self):
        d = self.attestation.to_dict()
        self.assertIn("attestation_digest", d)
        self.assertTrue(d["attestation_digest"].startswith("sha256:"))

    def test_zero_obligations_full_confidence_no_dissent(self):
        contract = _make_contract(proof_obligations=())
        report = OceanicOrchestrator(default_adapters()).run(contract)
        attestation = create_attestation(report)
        self.assertEqual(attestation.aggregate["confidence"], 1.0)
        self.assertEqual(attestation.aggregate["dissent"], [])

    def test_aggregate_confidence_matches_report_confidence(self):
        self.assertAlmostEqual(
            self.attestation.aggregate["confidence"], self.report.confidence, places=6
        )

    def test_default_authorization_is_pending(self):
        attestation = create_attestation(self.report)
        self.assertEqual(attestation.authorization.status, "pending")
        self.assertIsNone(attestation.authorization.reviewer)
        self.assertIsNone(attestation.authorization.reason)

    def test_schema_is_always_oceanic_attestation(self):
        self.assertEqual(self.attestation.schema, "oceanic.attestation/v0.1")
        # Different contracts produce same schema
        contract2 = _make_contract("another.contract.v1", proof_obligations=())
        report2 = OceanicOrchestrator(default_adapters()).run(contract2)
        att2 = create_attestation(report2)
        self.assertEqual(att2.schema, "oceanic.attestation/v0.1")


if __name__ == "__main__":
    unittest.main()


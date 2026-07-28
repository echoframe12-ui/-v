"""Tests for the Oceanic Observer — runtime execution and contract comparison.

Covers:
  - ExecutionDenied on unauthorized attestation
  - Matched result: status, actual, deviations, updated runtime state
  - Deviated result: status, deviations populated
  - runtime_digest is sha256-prefixed and deterministic
  - evidence field content
  - observation.contract_id matches attestation.contract_id
  - Updated attestation runtime_digest matches observation runtime_digest
  - None expected value handled (None actual matches)
"""
import unittest

from oceanic_attestation import create_attestation
from oceanic_authorization import authorize
from oceanic_ir import OceanicIRContract
from oceanic_observer import ExecutionDenied, execute_and_observe
from oceanic_orchestrator import OceanicOrchestrator, default_adapters


def _build_authorized(contract_id: str = "example.add.v1") -> object:
    contract = OceanicIRContract(
        api_version="oceanic.ir/v0.1",
        contract_id=contract_id,
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
    return authorize(
        attestation,
        reviewer="observer-test",
        reason="Approved for deterministic observer testing.",
    )


class OceanicObserverTests(unittest.TestCase):
    def setUp(self):
        self.authorized = _build_authorized()
        self.pending = create_attestation(
            OceanicOrchestrator(default_adapters()).run(
                OceanicIRContract(
                    api_version="oceanic.ir/v0.1",
                    contract_id="example.add.v1",
                    intent="combine two numeric values",
                    inputs=({"name": "a", "type": "integer"}, {"name": "b", "type": "integer"}),
                    outputs={"type": "integer"},
                    invariants=("result == mathematical_sum(a, b)",),
                    effects=(),
                    bounds={"time": "O(1)", "memory": "O(1)"},
                    dependencies=(),
                    proof_obligations=("arithmetic_correctness", "overflow_handling"),
                    dissent_triggers=("overflow",),
                    risk={"class": "low", "human_authorization": False},
                )
            )
        )

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

    def test_runtime_digest_is_sha256_prefixed(self):
        _, observation = execute_and_observe(
            self.authorized, execute=lambda: 4, expected=4
        )
        self.assertTrue(observation.runtime_digest.startswith("sha256:"))
        self.assertEqual(len(observation.runtime_digest), len("sha256:") + 64)

    def test_runtime_digest_is_deterministic_for_same_values(self):
        _, obs1 = execute_and_observe(self.authorized, execute=lambda: 4, expected=4)
        authorized2 = _build_authorized()
        _, obs2 = execute_and_observe(authorized2, execute=lambda: 4, expected=4)
        self.assertEqual(obs1.runtime_digest, obs2.runtime_digest)

    def test_different_outcomes_produce_different_digests(self):
        _, obs1 = execute_and_observe(self.authorized, execute=lambda: 4, expected=4)
        authorized2 = _build_authorized()
        _, obs2 = execute_and_observe(authorized2, execute=lambda: 5, expected=4)
        self.assertNotEqual(obs1.runtime_digest, obs2.runtime_digest)

    def test_evidence_field_is_deterministic_comparison(self):
        _, observation = execute_and_observe(
            self.authorized, execute=lambda: 4, expected=4
        )
        self.assertEqual(observation.evidence, "deterministic equality comparison")

    def test_observation_contract_id_matches_attestation(self):
        _, observation = execute_and_observe(
            self.authorized, execute=lambda: 4, expected=4
        )
        self.assertEqual(observation.contract_id, self.authorized.contract_id)

    def test_updated_attestation_runtime_digest_matches_observation(self):
        updated, observation = execute_and_observe(
            self.authorized, execute=lambda: 7, expected=7
        )
        self.assertEqual(updated.runtime.runtime_digest, observation.runtime_digest)

    def test_none_expected_and_none_actual_is_matched(self):
        _, observation = execute_and_observe(
            self.authorized, execute=lambda: None, expected=None
        )
        self.assertEqual(observation.status, "matched")
        self.assertIsNone(observation.actual)

    def test_none_actual_with_non_none_expected_is_deviated(self):
        _, observation = execute_and_observe(
            self.authorized, execute=lambda: None, expected=4
        )
        self.assertEqual(observation.status, "deviated")
        self.assertTrue(observation.deviations)


if __name__ == "__main__":
    unittest.main()


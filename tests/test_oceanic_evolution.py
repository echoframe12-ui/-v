"""Tests for Oceanic Evolution — evidence-preserving evolution proposals.

Covers:
  - Matched observation produces no proposal
  - Deviation produces reviewable proposal (category, requires_human_review, attestation_id, proposal_id)
  - Proposal does not mutate historical attestation (digest unchanged)
  - to_dict includes schema, proposal_id, category, requires_human_review
  - Mismatched contract_id between observation and attestation raises ValueError
  - proposal_id is unique for different deviations
  - proposed_changes is a non-empty tuple
  - reason field is non-empty for deviations
"""
import unittest
from dataclasses import replace

from oceanic_attestation import create_attestation
from oceanic_authorization import authorize
from oceanic_evolution import EvolutionProposal, propose_evolution
from oceanic_ir import OceanicIRContract
from oceanic_observer import Observation, execute_and_observe
from oceanic_orchestrator import OceanicOrchestrator, default_adapters


def _setup_authorized():
    contract = OceanicIRContract(
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
    report = OceanicOrchestrator(default_adapters()).run(contract)
    return authorize(
        create_attestation(report),
        reviewer="evolution-test",
        reason="Approved for evolution testing.",
    )


class OceanicEvolutionTests(unittest.TestCase):
    def setUp(self):
        self.attestation = _setup_authorized()

    def _deviated_observation(self, execute_value=5, expected=4):
        _, obs = execute_and_observe(
            self.attestation, execute=lambda: execute_value, expected=expected
        )
        return obs

    def test_matching_observation_produces_no_proposal(self):
        _, observation = execute_and_observe(
            self.attestation, execute=lambda: 4, expected=4
        )
        self.assertIsNone(propose_evolution(self.attestation, observation))

    def test_deviation_produces_reviewable_proposal(self):
        observation = self._deviated_observation()
        proposal = propose_evolution(self.attestation, observation)
        self.assertIsNotNone(proposal)
        self.assertEqual(proposal.category, "contract_runtime_deviation")
        self.assertTrue(proposal.requires_human_review)
        self.assertEqual(proposal.attestation_id, self.attestation.attestation_id)
        self.assertTrue(proposal.proposal_id.startswith("evo_"))

    def test_proposal_does_not_mutate_historical_attestation(self):
        original_digest = self.attestation.digest()
        propose_evolution(self.attestation, self._deviated_observation())
        self.assertEqual(self.attestation.digest(), original_digest)

    def test_to_dict_includes_schema_and_key_fields(self):
        observation = self._deviated_observation()
        proposal = propose_evolution(self.attestation, observation)
        d = proposal.to_dict()
        self.assertEqual(d["schema"], "oceanic.evolution-proposal/v0.1")
        self.assertIn("proposal_id", d)
        self.assertIn("contract_id", d)
        self.assertIn("attestation_id", d)
        self.assertIn("category", d)
        self.assertIn("requires_human_review", d)
        self.assertTrue(d["requires_human_review"])
        self.assertEqual(d["observation_status"], "deviated")

    def test_mismatched_contract_id_raises_value_error(self):
        """A proposal must match the attestation's contract_id."""
        observation = self._deviated_observation()
        # Synthesize an observation with a different contract_id
        wrong_obs = Observation(
            status="deviated",
            contract_id="wrong.contract.id",
            runtime_digest=observation.runtime_digest,
            expected=observation.expected,
            actual=observation.actual,
            deviations=observation.deviations,
        )
        with self.assertRaises(ValueError):
            propose_evolution(self.attestation, wrong_obs)

    def test_unique_proposal_ids_for_different_deviations(self):
        obs1 = self._deviated_observation(execute_value=99)
        obs2 = self._deviated_observation(execute_value=77)
        p1 = propose_evolution(self.attestation, obs1)
        p2 = propose_evolution(self.attestation, obs2)
        self.assertNotEqual(p1.proposal_id, p2.proposal_id)

    def test_proposed_changes_is_non_empty(self):
        observation = self._deviated_observation()
        proposal = propose_evolution(self.attestation, observation)
        self.assertTrue(len(proposal.proposed_changes) > 0)
        # Each change is a non-empty string
        for change in proposal.proposed_changes:
            self.assertIsInstance(change, str)
            self.assertTrue(change.strip())

    def test_reason_field_is_populated_for_deviation(self):
        observation = self._deviated_observation()
        proposal = propose_evolution(self.attestation, observation)
        self.assertTrue(proposal.reason.strip())
        # The deviation message should appear in the reason
        self.assertIn("runtime", proposal.reason)


if __name__ == "__main__":
    unittest.main()


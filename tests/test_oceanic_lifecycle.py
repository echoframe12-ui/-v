"""Comprehensive tests for the OceanicLifecycle coordinator.

Covers:
  - Matched run: correct event sequence, no evolution, chain intact
  - Deviated run: evolution proposal, human.review.required, chain intact
  - Authorization fields propagated into LifecycleResult
  - Report confidence and dissent surface through LifecycleResult
  - Ledger chain integrity across consecutive runs
  - Zero proof obligations (all adapters pass, full confidence)
  - Ledger event count per run mode
  - Unique proposal IDs for distinct deviations
"""
import tempfile
import unittest
from pathlib import Path

from oceanic_event_ledger import EventLedger
from oceanic_ir import OceanicIRContract
from oceanic_lifecycle import OceanicLifecycle
from oceanic_orchestrator import OceanicOrchestrator, default_adapters


def _make_contract(
    contract_id: str = "lifecycle.add.v1",
    proof_obligations: tuple = ("arithmetic_correctness", "overflow_handling"),
) -> OceanicIRContract:
    return OceanicIRContract(
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
        proof_obligations=proof_obligations,
        dissent_triggers=("overflow",),
        risk={"class": "low", "human_authorization": False},
    )


def _run(ledger, *, execute_value=4, expected=4, contract=None, reviewer="test-reviewer"):
    lifecycle = OceanicLifecycle(OceanicOrchestrator(default_adapters()), ledger)
    return lifecycle.run(
        contract or _make_contract(),
        reviewer=reviewer,
        authorization_reason="Approved for test.",
        execute=lambda: execute_value,
        expected=expected,
    )


class OceanicLifecycleTests(unittest.TestCase):

    def test_matching_lifecycle_is_recorded_without_evolution(self):
        with tempfile.TemporaryDirectory() as d:
            ledger = EventLedger(Path(d) / "events.jsonl")
            result = _run(ledger, execute_value=4, expected=4)

            self.assertEqual(result.observation.status, "matched")
            self.assertIsNone(result.evolution)
            self.assertTrue(ledger.verify_chain())
            self.assertEqual(
                [e.event_type for e in ledger.history()],
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
        with tempfile.TemporaryDirectory() as d:
            ledger = EventLedger(Path(d) / "events.jsonl")
            result = _run(ledger, execute_value=5, expected=4)

            self.assertEqual(result.observation.status, "deviated")
            self.assertIsNotNone(result.evolution)
            self.assertTrue(result.evolution.requires_human_review)
            self.assertTrue(ledger.verify_chain())
            event_types = [e.event_type for e in ledger.history()]
            self.assertIn("evolution.proposed", event_types)
            self.assertIn("human.review.required", event_types)

    def test_authorization_fields_surface_through_lifecycle_result(self):
        with tempfile.TemporaryDirectory() as d:
            ledger = EventLedger(Path(d) / "events.jsonl")
            result = _run(ledger, reviewer="explicit-reviewer")

            # result.authorization is the authorized Attestation returned by authorize()
            self.assertEqual(result.authorization.authorization.reviewer, "explicit-reviewer")
            self.assertEqual(result.authorization.authorization.status, "authorized")
            # The final attestation (post-observation) also carries authorized status
            self.assertEqual(result.attestation.authorization.status, "authorized")

    def test_report_confidence_surfaces_through_result(self):
        with tempfile.TemporaryDirectory() as d:
            ledger = EventLedger(Path(d) / "events.jsonl")
            result = _run(ledger)

            # Rust covers both obligations; python/ts cover only one — aggregate is between 0 and 1
            self.assertGreater(result.report.confidence, 0.0)
            self.assertLessEqual(result.report.confidence, 1.0)
            # The report has 3 adapters (python, rust, typescript)
            self.assertEqual(len(result.report.results), 3)

    def test_matched_run_produces_exactly_six_events(self):
        with tempfile.TemporaryDirectory() as d:
            ledger = EventLedger(Path(d) / "events.jsonl")
            _run(ledger, execute_value=4, expected=4)
            self.assertEqual(len(list(ledger.history())), 6)

    def test_deviated_run_produces_eight_events(self):
        with tempfile.TemporaryDirectory() as d:
            ledger = EventLedger(Path(d) / "events.jsonl")
            _run(ledger, execute_value=99, expected=4)
            # 6 base + evolution.proposed + human.review.required
            self.assertEqual(len(list(ledger.history())), 8)

    def test_chain_integrity_across_consecutive_runs(self):
        """Two back-to-back lifecycle runs share one ledger — chain must stay intact."""
        with tempfile.TemporaryDirectory() as d:
            ledger = EventLedger(Path(d) / "events.jsonl")
            _run(ledger, execute_value=4, expected=4, contract=_make_contract("run.1"))
            _run(ledger, execute_value=5, expected=4, contract=_make_contract("run.2"))

            self.assertTrue(ledger.verify_chain())
            events = list(ledger.history())
            # First 6 events for run.1 (matched), next 8 for run.2 (deviated)
            self.assertEqual(len(events), 14)
            # Sequence numbers are consecutive
            for i, event in enumerate(events):
                self.assertEqual(event.sequence, i + 1)

    def test_zero_proof_obligations_all_adapters_pass(self):
        """A contract with no obligations gives full confidence and no dissent."""
        with tempfile.TemporaryDirectory() as d:
            ledger = EventLedger(Path(d) / "events.jsonl")
            result = _run(
                ledger,
                contract=_make_contract("no-obligations.v1", proof_obligations=()),
            )
            self.assertEqual(result.report.confidence, 1.0)
            self.assertEqual(result.report.dissent, ())

    def test_unique_proposal_ids_for_distinct_deviations(self):
        """Two different deviation observations produce distinct proposal IDs."""
        with tempfile.TemporaryDirectory() as d:
            l1 = EventLedger(Path(d) / "e1.jsonl")
            l2 = EventLedger(Path(d) / "e2.jsonl")
            r1 = _run(l1, execute_value=99, expected=4)
            r2 = _run(l2, execute_value=77, expected=4)
            self.assertNotEqual(r1.evolution.proposal_id, r2.evolution.proposal_id)

    def test_evolution_category_is_contract_runtime_deviation(self):
        with tempfile.TemporaryDirectory() as d:
            ledger = EventLedger(Path(d) / "events.jsonl")
            result = _run(ledger, execute_value=999, expected=0)
            self.assertEqual(result.evolution.category, "contract_runtime_deviation")
            self.assertEqual(result.evolution.contract_id, "lifecycle.add.v1")

    def test_evolution_contract_id_matches_original_contract(self):
        with tempfile.TemporaryDirectory() as d:
            ledger = EventLedger(Path(d) / "events.jsonl")
            contract = _make_contract("evolution-id-check.v1")
            result = _run(ledger, execute_value=1, expected=0, contract=contract)
            self.assertEqual(result.evolution.contract_id, "evolution-id-check.v1")
            self.assertEqual(result.attestation.contract_id, "evolution-id-check.v1")

    def test_observation_deviation_recorded_in_ledger_payload(self):
        with tempfile.TemporaryDirectory() as d:
            ledger = EventLedger(Path(d) / "events.jsonl")
            _run(ledger, execute_value=42, expected=7)
            events = list(ledger.history())
            deviated_event = next(e for e in events if e.event_type == "observation.deviated")
            self.assertIn("deviations", deviated_event.payload)
            self.assertTrue(len(deviated_event.payload["deviations"]) > 0)


if __name__ == "__main__":
    unittest.main()


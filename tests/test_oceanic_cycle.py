"""Tests for oceanic_cycle.py — the Oceanic Cycle Kernel.

Required tests (from the master prompt):
  1. Observe → Verify → Consensus
  2. Observe → Verify → Dissent
  3. Dissent → Human Hold
  4. Verified → Evolve
  5. Evolution → Reverify
  6. Drift → Recompile
  7. Full Cycle → Immutable Audit Record

Additional tests:
  - Provenance hash is deterministic
  - Provenance hash verification (re-derive and match)
  - State counter advances S0 → S1 → S2 → ...
  - INVARIANTS are all non-empty strings
  - VerificationStatus and DecisionRoute enum values
  - Partially verified → continue_checking route
  - Unverified → hold route
  - Blocked → human_authorization route
  - audit_trail() returns serializable dicts
  - Events are append-only (tuple copy)
  - Default action/consequence descriptions
  - CycleEvent contains all 14 required fields
"""
import json
import unittest

from oceanic_cycle import (
    INVARIANTS,
    Contract,
    CycleEvent,
    DecisionRoute,
    OceanicCycle,
    Observation,
    VerificationResult,
    VerificationStatus,
    provenance_hash,
    route_decision,
)


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _observe(what="test observation", evidence=("evidence-1",), observer="test-observer"):
    return Observation(observer=observer, what=what, evidence=evidence)


def _contract(contract_id="C-001", clauses=("clause-1", "clause-2")):
    return Contract(contract_id=contract_id, clauses=clauses)


def _verify(status=VerificationStatus.VERIFIED, confidence=0.9, dissent=()):
    evidence_hash = "abc123"
    return VerificationResult(
        status=status, confidence=confidence, evidence_hash=evidence_hash,
        dissent=dissent, checks_passed=2, checks_total=2,
    )


# ─── Required tests from the master prompt ────────────────────────────────────

class ObserveVerifyConsensusTests(unittest.TestCase):
    """1. Observe → Verify → Consensus"""

    def test_verified_observation_produces_accept_decision(self):
        cycle = OceanicCycle()
        event = cycle.execute(_observe(), _contract(), _verify())
        self.assertEqual(event.verification, VerificationStatus.VERIFIED)
        self.assertEqual(event.decision, DecisionRoute.ACCEPT)
        self.assertEqual(event.state_id, "S0")
        self.assertEqual(event.next_state, "S1")

    def test_consensus_has_no_dissent(self):
        cycle = OceanicCycle()
        event = cycle.execute(_observe(), _contract(), _verify())
        self.assertEqual(event.dissent, ())

    def test_consensus_confidence_is_preserved(self):
        cycle = OceanicCycle()
        event = cycle.execute(_observe(), _contract(), _verify(confidence=0.95))
        self.assertEqual(event.confidence, 0.95)


class ObserveVerifyDissentTests(unittest.TestCase):
    """2. Observe → Verify → Dissent"""

    def test_dissent_produces_human_route_decision(self):
        cycle = OceanicCycle()
        event = cycle.execute(
            _observe(), _contract(),
            _verify(status=VerificationStatus.DISSENT, dissent=("model-A disagrees",)),
        )
        self.assertEqual(event.verification, VerificationStatus.DISSENT)
        self.assertEqual(event.decision, DecisionRoute.HUMAN_ROUTE)
        self.assertEqual(event.dissent, ("model-A disagrees",))

    def test_dissent_is_never_suppressed(self):
        """No dissent without a record — invariant."""
        cycle = OceanicCycle()
        event = cycle.execute(
            _observe(), _contract(),
            _verify(status=VerificationStatus.DISSENT, dissent=("dissent-1", "dissent-2")),
        )
        self.assertEqual(len(event.dissent), 2)
        self.assertIn("dissent-1", event.dissent)
        self.assertIn("dissent-2", event.dissent)


class DissentHumanHoldTests(unittest.TestCase):
    """3. Dissent → Human Hold"""

    def test_dissent_holds_for_human_judgment(self):
        cycle = OceanicCycle()
        event = cycle.execute(
            _observe(), _contract(),
            _verify(status=VerificationStatus.DISSENT, dissent=("material dissent",)),
        )
        self.assertEqual(event.decision, DecisionRoute.HUMAN_ROUTE)
        self.assertIn("human", event.action.lower())
        self.assertIn("held", event.consequence.lower())

    def test_blocked_escalates_to_human_authorization(self):
        cycle = OceanicCycle()
        event = cycle.execute(
            _observe(), _contract(),
            _verify(status=VerificationStatus.BLOCKED),
        )
        self.assertEqual(event.decision, DecisionRoute.HUMAN_AUTHORIZATION)
        self.assertIn("human", event.action.lower())


class VerifiedEvolveTests(unittest.TestCase):
    """4. Verified → Evolve"""

    def test_verified_state_advances(self):
        cycle = OceanicCycle()
        e1 = cycle.execute(_observe(what="first"), _contract(), _verify())
        self.assertEqual(e1.state_id, "S0")
        self.assertEqual(e1.next_state, "S1")
        e2 = cycle.execute(_observe(what="second"), _contract(), _verify())
        self.assertEqual(e2.state_id, "S1")
        self.assertEqual(e2.next_state, "S2")

    def test_evolution_preserves_provenance(self):
        cycle = OceanicCycle()
        e1 = cycle.execute(_observe(), _contract(), _verify())
        self.assertTrue(e1.provenance_hash)
        self.assertTrue(cycle.verify_provenance(e1))


class EvolutionReverifyTests(unittest.TestCase):
    """5. Evolution → Reverify"""

    def test_partial_verification_continues_checking(self):
        cycle = OceanicCycle()
        event = cycle.execute(
            _observe(), _contract(),
            _verify(status=VerificationStatus.PARTIALLY_VERIFIED, confidence=0.6),
        )
        self.assertEqual(event.decision, DecisionRoute.CONTINUE_CHECKING)
        self.assertIn("continue", event.action.lower())

    def test_unverified_holds_state(self):
        cycle = OceanicCycle()
        event = cycle.execute(
            _observe(), _contract(),
            _verify(status=VerificationStatus.UNVERIFIED, confidence=0.2),
        )
        self.assertEqual(event.decision, DecisionRoute.HOLD)
        self.assertIn("hold", event.action.lower())


class DriftRecompileTests(unittest.TestCase):
    """6. Drift → Recompile"""

    def test_drift_detected_produces_new_state(self):
        """When drift is detected (dissent from reality), the cycle produces
        a new state — the recompilation."""
        cycle = OceanicCycle()
        # First cycle: verified
        e1 = cycle.execute(_observe(what="initial state"), _contract(), _verify())
        # Drift detected: reality diverged from model
        e2 = cycle.execute(
            _observe(what="drift detected — reality ≠ model"),
            _contract(contract_id="C-RECOMPILE"),
            _verify(status=VerificationStatus.DISSENT, dissent=("reality diverged",)),
        )
        self.assertEqual(e2.state_id, "S1")
        self.assertEqual(e2.next_state, "S2")
        self.assertEqual(e2.contract_id, "C-RECOMPILE")
        # Recompilation: new contract verified
        e3 = cycle.execute(
            _observe(what="recompiled state"),
            _contract(contract_id="C-002"),
            _verify(),
        )
        self.assertEqual(e3.state_id, "S2")
        self.assertEqual(e3.next_state, "S3")
        self.assertEqual(e3.decision, DecisionRoute.ACCEPT)


class FullCycleAuditRecordTests(unittest.TestCase):
    """7. Full Cycle → Immutable Audit Record"""

    def test_full_cycle_produces_immutable_audit_trail(self):
        cycle = OceanicCycle()
        # Run a complete cycle
        cycle.execute(_observe(), _contract(), _verify())
        trail = cycle.audit_trail()
        self.assertEqual(len(trail), 1)
        record = trail[0]
        # All 14 required fields from the event schema
        required_fields = {
            "cycle_id", "state_id", "contract_id", "observer",
            "evidence", "verification", "confidence", "dissent",
            "decision", "action", "consequence", "next_state",
            "provenance_hash", "timestamp",
        }
        self.assertEqual(set(record.keys()), required_fields)

    def test_audit_trail_is_serializable_json(self):
        cycle = OceanicCycle()
        cycle.execute(_observe(), _contract(), _verify())
        cycle.execute(
            _observe(), _contract(),
            _verify(status=VerificationStatus.DISSENT, dissent=("dissent",)),
        )
        trail = cycle.audit_trail()
        # Must be JSON-serializable without error
        json_str = json.dumps(trail)
        self.assertTrue(json_str)
        self.assertEqual(len(json.loads(json_str)), 2)

    def test_events_are_append_only_tuple(self):
        cycle = OceanicCycle()
        cycle.execute(_observe(), _contract(), _verify())
        events = cycle.events
        self.assertIsInstance(events, tuple)
        self.assertEqual(len(events), 1)
        # Modifying the returned tuple must not affect the cycle's internal list
        cycle.execute(_observe(), _contract(), _verify())
        self.assertEqual(len(events), 1)  # old tuple unchanged
        self.assertEqual(len(cycle.events), 2)  # new tuple has both

    def test_multiple_cycles_build_contiguous_state_chain(self):
        cycle = OceanicCycle()
        for i in range(5):
            event = cycle.execute(_observe(what=f"cycle-{i}"), _contract(), _verify())
            self.assertEqual(event.state_id, f"S{i}")
            self.assertEqual(event.next_state, f"S{i+1}")
        self.assertEqual(len(cycle.events), 5)


# ─── Additional coverage ─────────────────────────────────────────────────────

class ProvenanceTests(unittest.TestCase):

    def test_provenance_hash_is_deterministic(self):
        h1 = provenance_hash("S0", "C-001", ("ev",), VerificationStatus.VERIFIED, DecisionRoute.ACCEPT)
        h2 = provenance_hash("S0", "C-001", ("ev",), VerificationStatus.VERIFIED, DecisionRoute.ACCEPT)
        self.assertEqual(h1, h2)
        self.assertEqual(len(h1), 64)  # SHA-256 hex

    def test_provenance_hash_changes_with_inputs(self):
        h1 = provenance_hash("S0", "C-001", ("ev",), VerificationStatus.VERIFIED, DecisionRoute.ACCEPT)
        h2 = provenance_hash("S1", "C-001", ("ev",), VerificationStatus.VERIFIED, DecisionRoute.ACCEPT)
        self.assertNotEqual(h1, h2)

    def test_verify_provenance_on_cycle_event(self):
        cycle = OceanicCycle()
        event = cycle.execute(_observe(), _contract(), _verify())
        self.assertTrue(cycle.verify_provenance(event))


class RouteDecisionTests(unittest.TestCase):

    def test_all_statuses_have_a_route(self):
        for status in VerificationStatus:
            result = _verify(status=status)
            decision = route_decision(result)
            self.assertIsInstance(decision, DecisionRoute)


class InvariantsTests(unittest.TestCase):

    def test_invariants_are_nonempty_strings(self):
        self.assertGreaterEqual(len(INVARIANTS), 5)
        for inv in INVARIANTS:
            self.assertIsInstance(inv, str)
            self.assertTrue(inv.strip())


class EnumTests(unittest.TestCase):

    def test_verification_status_values(self):
        self.assertEqual(VerificationStatus.VERIFIED.value, "verified")
        self.assertEqual(VerificationStatus.DISSENT.value, "dissent")
        self.assertEqual(VerificationStatus.BLOCKED.value, "blocked")

    def test_decision_route_values(self):
        self.assertEqual(DecisionRoute.ACCEPT.value, "accept")
        self.assertEqual(DecisionRoute.HUMAN_ROUTE.value, "human_route")
        self.assertEqual(DecisionRoute.HOLD.value, "hold")


class ObservationTests(unittest.TestCase):

    def test_observation_has_auto_fields(self):
        obs = _observe()
        self.assertTrue(obs.timestamp)
        self.assertTrue(obs.observation_id)
        self.assertEqual(len(obs.observation_id), 16)

    def test_observation_is_frozen(self):
        obs = _observe()
        with self.assertRaises(AttributeError):
            obs.what = "mutated"


class CycleEventSchemaTests(unittest.TestCase):

    def test_cycle_event_has_14_fields(self):
        cycle = OceanicCycle()
        event = cycle.execute(_observe(), _contract(), _verify())
        # CycleEvent should have exactly 14 fields
        from dataclasses import fields
        self.assertEqual(len(fields(event)), 14)

    def test_custom_action_and_consequence(self):
        cycle = OceanicCycle()
        event = cycle.execute(
            _observe(), _contract(), _verify(),
            action="deploy to staging",
            consequence="staging environment updated",
        )
        self.assertEqual(event.action, "deploy to staging")
        self.assertEqual(event.consequence, "staging environment updated")


if __name__ == "__main__":
    unittest.main()

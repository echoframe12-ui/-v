from __future__ import annotations

from attestation_protocol import attest_cycle, generate_keypair, verify_attestation
from attestation_recompile import recompile_and_reattest
from oceanic_cycle import CycleEvent, DecisionRoute, VerificationStatus
from oceanic_event_ledger import EventLedger


def _event(cycle_id: str, status: VerificationStatus, next_state: str) -> CycleEvent:
    return CycleEvent(
        cycle_id=cycle_id,
        state_id="state-1",
        contract_id="contract-1",
        observer="heartbeat-observer",
        evidence=(f"evidence:{cycle_id}",),
        verification=status,
        confidence=0.99 if status == VerificationStatus.VERIFIED else 0.2,
        dissent=(),
        decision=DecisionRoute.ACCEPT if status == VerificationStatus.VERIFIED else DecisionRoute.HOLD,
        action="observe",
        consequence="advance",
        next_state=next_state,
        provenance_hash=f"sha256:{cycle_id}",
        timestamp="2026-08-04T00:00:00+00:00",
    )


def test_full_persisted_heartbeat():
    private, public = generate_keypair()
    ledger = EventLedger()

    parent = attest_cycle(
        _event("heartbeat-parent", VerificationStatus.VERIFIED, "observe"),
        prompt="input",
        final_output="state-0",
        schema_digest="sha256:schema-v1",
        private_key=private,
    )
    ledger.append_attestation(parent)

    assert verify_attestation(parent.to_dict(), expected_schema_digest="sha256:schema-v1", public_key=public)["valid"]

    child = recompile_and_reattest(
        parent,
        _event("heartbeat-child", VerificationStatus.VERIFIED, "observe"),
        prompt="recompiled input",
        final_output="state-1",
        schema_digest="sha256:schema-v2",
        private_key=private,
        drift_state="detected",
        recompile_state="completed",
    )
    ledger.append_attestation(child)

    restored_parent = ledger.get_attestation(parent.document["attestation_id"])
    restored_child = ledger.get_attestation(child.document["attestation_id"])

    assert restored_parent is not None
    assert restored_child is not None
    assert restored_child.document["parent_attestation_id"] == restored_parent.document["attestation_id"]
    assert verify_attestation(restored_parent.to_dict(), expected_schema_digest="sha256:schema-v1", public_key=public)["valid"]
    assert verify_attestation(restored_child.to_dict(), expected_schema_digest="sha256:schema-v2", public_key=public)["valid"]
    assert ledger.verify_chain()


def test_failed_recompile_stops_before_ledger_append():
    private, _ = generate_keypair()
    ledger = EventLedger()
    parent = attest_cycle(
        _event("heartbeat-parent-fail", VerificationStatus.VERIFIED, "observe"),
        prompt="input",
        final_output="state-0",
        schema_digest="sha256:schema-v1",
        private_key=private,
    )
    ledger.append_attestation(parent)

    try:
        recompile_and_reattest(
            parent,
            _event("heartbeat-failed", VerificationStatus.PARTIALLY_VERIFIED, "hold"),
            prompt="bad recompile",
            final_output="bad-state",
            schema_digest="sha256:schema-v2",
            private_key=private,
            drift_state="detected",
            recompile_state="failed",
        )
    except ValueError:
        pass
    else:
        raise AssertionError("failed reverification crossed the attestation boundary")

    assert len(ledger.events) == 1
    assert ledger.verify_chain()

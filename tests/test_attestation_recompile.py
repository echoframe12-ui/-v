from __future__ import annotations

import pytest

from attestation_protocol import attest_cycle, generate_keypair, verify_attestation
from attestation_recompile import recompile_and_reattest
from oceanic_cycle import CycleEvent, DecisionRoute, VerificationStatus


def _event(cycle_id: str, status: VerificationStatus, next_state: str) -> CycleEvent:
    return CycleEvent(
        cycle_id=cycle_id,
        state_id="state-1",
        contract_id="contract-1",
        observer="test-observer",
        evidence=(f"evidence:{cycle_id}",),
        verification=status,
        confidence=0.99 if status == VerificationStatus.VERIFIED else 0.4,
        dissent=(),
        decision=DecisionRoute.ACCEPT if status == VerificationStatus.VERIFIED else DecisionRoute.HOLD,
        action="recompile",
        consequence="new state",
        next_state=next_state,
        provenance_hash=f"sha256:{cycle_id}",
        timestamp="2026-08-04T00:00:00+00:00",
    )


def _parent():
    private, _ = generate_keypair()
    return attest_cycle(
        _event("parent", VerificationStatus.VERIFIED, "observe"),
        prompt="initial input",
        final_output="state-0",
        schema_digest="sha256:schema",
        private_key=private,
    ), private


def test_drift_recompile_reverify_creates_new_signed_lineage():
    parent, private = _parent()
    before = parent.to_json()

    child = recompile_and_reattest(
        parent,
        _event("recompiled", VerificationStatus.VERIFIED, "observe"),
        prompt="recompiled input",
        final_output="state-1",
        schema_digest="sha256:schema-v2",
        private_key=private,
        drift_state="detected",
        recompile_state="completed",
    )

    assert parent.to_json() == before
    assert child.document["attestation_id"] != parent.document["attestation_id"]
    assert child.document["parent_attestation_id"] == parent.document["attestation_id"]
    assert child.document["drift_state"] == "detected"
    assert child.document["recompile_state"] == "completed"
    assert verify_attestation(parent.to_dict(), expected_schema_digest="sha256:schema")["valid"]
    assert verify_attestation(child.to_dict(), expected_schema_digest="sha256:schema-v2")["valid"]


def test_failed_reverification_cannot_become_attested():
    parent, private = _parent()

    with pytest.raises(ValueError, match="independently verified"):
        recompile_and_reattest(
            parent,
            _event("failed-recompile", VerificationStatus.PARTIALLY_VERIFIED, "hold"),
            prompt="bad recompile",
            final_output="state-bad",
            schema_digest="sha256:schema-v2",
            private_key=private,
            drift_state="detected",
            recompile_state="failed",
        )

    assert parent.document["attestation_status"] == "ATTESTED"


def test_drift_does_not_mutate_parent():
    parent, private = _parent()
    before = parent.to_json()

    recompile_and_reattest(
        parent,
        _event("recompiled-2", VerificationStatus.VERIFIED, "observe"),
        prompt="recompiled input",
        final_output="state-2",
        schema_digest="sha256:schema-v2",
        private_key=private,
        drift_state="detected",
        recompile_state="completed",
    )

    assert parent.to_json() == before

from __future__ import annotations

import pytest

from oceanic_cycle import CycleEvent, DecisionRoute, VerificationStatus
from omega_signer import OmegaSigner
from omega_vaas_bridge import attest_verified_cycle
from attestation_protocol import verify_attestation


def event(status: VerificationStatus) -> CycleEvent:
    return CycleEvent(
        cycle_id="vaas-cycle-1",
        state_id="state-1",
        contract_id="contract-1",
        observer="vaas-observer",
        evidence=("evidence-1",),
        verification=status,
        confidence=0.99 if status is VerificationStatus.VERIFIED else 0.2,
        dissent=(),
        decision=DecisionRoute.ACCEPT if status is VerificationStatus.VERIFIED else DecisionRoute.HOLD,
        action="observe",
        consequence="advance",
        next_state="observe",
        provenance_hash="sha256:provenance",
        timestamp="2026-08-04T00:00:00+00:00",
    )


def test_bridge_emits_independently_verifiable_omega_attestation():
    private, _ = OmegaSigner.generate()
    signer = OmegaSigner(private)
    result = attest_verified_cycle(
        event(VerificationStatus.VERIFIED),
        signer=signer,
        prompt="input",
        final_output="output",
        schema_digest="sha256:schema-v1",
    )

    report = verify_attestation(
        result.signed.to_dict(),
        expected_schema_digest="sha256:schema-v1",
    )
    assert result.verified is True
    assert report["valid"] is True
    assert report["signature_valid"] is True


def test_bridge_refuses_partial_or_blocked_cycles():
    private, _ = OmegaSigner.generate()
    signer = OmegaSigner(private)
    for status in (VerificationStatus.PARTIALLY_VERIFIED, VerificationStatus.DISSENT, VerificationStatus.BLOCKED):
        with pytest.raises(ValueError, match="requires VERIFIED cycle status"):
            attest_verified_cycle(
                event(status),
                signer=signer,
                prompt="input",
                final_output="output",
                schema_digest="sha256:schema-v1",
            )

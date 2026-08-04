from __future__ import annotations

from attestation_protocol import attest_cycle, generate_keypair
from oceanic_cycle import CycleEvent, DecisionRoute, VerificationStatus
from omega_edge import verify_edge_attestation


def verified_event() -> CycleEvent:
    return CycleEvent(
        cycle_id="edge-cycle-1",
        state_id="state-1",
        contract_id="contract-1",
        observer="edge-test",
        evidence=("evidence-1",),
        verification=VerificationStatus.VERIFIED,
        confidence=0.99,
        dissent=(),
        decision=DecisionRoute.ACCEPT,
        action="observe",
        consequence="advance",
        next_state="observe",
        provenance_hash="sha256:provenance",
        timestamp="2026-08-04T00:00:00+00:00",
    )


def make_attestation() -> dict:
    private, _ = generate_keypair()
    return attest_cycle(
        verified_event(),
        prompt="input",
        final_output="output",
        schema_digest="sha256:schema-v1",
        private_key=private,
    ).to_dict()


def test_edge_delegates_to_canonical_verifier():
    result = verify_edge_attestation(
        make_attestation(),
        expected_schema_digest="sha256:schema-v1",
    )
    assert result.valid is True
    assert result.report["signature_valid"] is True


def test_edge_rejects_tampered_attestation():
    attestation = make_attestation()
    attestation["final_output"] = "tampered"
    result = verify_edge_attestation(attestation, expected_schema_digest="sha256:schema-v1")
    assert result.valid is False


def test_edge_rejects_wrong_schema_digest():
    result = verify_edge_attestation(
        make_attestation(),
        expected_schema_digest="sha256:wrong",
    )
    assert result.valid is False

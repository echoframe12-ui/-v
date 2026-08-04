from __future__ import annotations

import pytest

from attestation_continuity import transition_from_attestation
from attestation_protocol import attest_cycle, generate_keypair
from oceanic_cycle import CycleEvent, DecisionRoute, VerificationStatus


def _attestation():
    private, _ = generate_keypair()
    event = CycleEvent(
        cycle_id="cycle-continuity",
        state_id="state-1",
        contract_id="contract-1",
        observer="test-observer",
        evidence=("evidence:1",),
        verification=VerificationStatus.VERIFIED,
        confidence=1.0,
        dissent=(),
        decision=DecisionRoute.ACCEPT,
        action="continue",
        consequence="verified",
        next_state="continue_observing",
        provenance_hash="sha256:provenance",
        timestamp="2026-08-04T00:00:00+00:00",
    )
    return attest_cycle(
        event,
        prompt="observe",
        final_output="verified output",
        schema_digest="sha256:schema",
        private_key=private,
    )


def test_verified_attestation_drives_existing_observer_model():
    attestation = _attestation()

    transition = transition_from_attestation(
        attestation,
        expected_schema_digest="sha256:schema",
    )

    assert transition.parent_attestation_id == attestation.document["attestation_id"]
    assert transition.observation.state == "attested"
    assert transition.observation.verification_status == "verified"
    assert transition.observation.attested is True
    assert transition.observation.next_state == "continue_observing"
    assert attestation.document["attestation_id"] in transition.observation.provenance
    assert transition.observation.verification_hash.startswith("sha256:")


def test_invalid_attestation_cannot_bypass_verification():
    attestation = _attestation()
    tampered = attestation.to_dict()
    tampered["final_output"] = "tampered"

    class Fake:
        def to_dict(self):
            return tampered

        document = attestation.document

    with pytest.raises(ValueError, match="invalid attestation"):
        transition_from_attestation(Fake())

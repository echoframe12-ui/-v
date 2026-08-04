from __future__ import annotations

import pytest

from attestation_continuity import transition_from_attestation
from attestation_protocol import attest_cycle, generate_keypair
from continuous_becoming import State
from oceanic_cycle import CycleEvent, Decision, VerificationStatus


def _attestation():
    private, _ = generate_keypair()
    event = CycleEvent(
        cycle_id="cycle-continuity",
        contract_id="contract-1",
        verification=VerificationStatus.VERIFIED,
        decision=Decision.CONTINUE,
        confidence=1.0,
        provenance_hash="sha256:provenance",
        evidence=("evidence:1",),
        dissent=(),
        next_state=State.ACT.value,
    )
    return attest_cycle(
        event,
        prompt="observe",
        final_output="verified output",
        schema_digest="sha256:schema",
        private_key=private,
    )


def test_verified_attestation_drives_existing_continuous_becoming_model():
    attestation = _attestation()

    transition = transition_from_attestation(
        attestation,
        expected_schema_digest="sha256:schema",
    )

    assert transition.parent_attestation_id == attestation.document["attestation_id"]
    assert transition.observation.state is State.ACT
    assert transition.observation.value == "verified output"
    assert transition.observation.provenance == attestation.document["attestation_id"]


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

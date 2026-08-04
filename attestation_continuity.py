from __future__ import annotations

"""Small adapter from signed attestations into Continuous Becoming.

This module deliberately does not create a second lifecycle. It validates the
signed attestation, converts its recorded next state into the existing
Continuous Becoming Observation shape, and lets that existing state machine
produce the next observation.
"""

from dataclasses import dataclass
from typing import Any

from attestation_protocol import SignedAttestation, verify_attestation
from continuous_becoming import Observation, State


@dataclass(frozen=True)
class ContinuityTransition:
    parent_attestation_id: str
    observation: Observation


def transition_from_attestation(
    attestation: SignedAttestation,
    *,
    expected_schema_digest: str | None = None,
) -> ContinuityTransition:
    """Turn an independently verified signed attestation into the existing
    Continuous Becoming observation model.

    No lifecycle state is mutated here and no verification is bypassed.
    """
    report = verify_attestation(
        attestation.to_dict(),
        expected_schema_digest=expected_schema_digest,
    )
    if not report["valid"]:
        raise ValueError("cannot transition from an invalid attestation")

    document = attestation.document
    state_name = str(document.get("next_state") or State.OBSERVE.value)
    try:
        state = State(state_name)
    except ValueError as exc:
        raise ValueError(f"unknown Continuous Becoming state: {state_name}") from exc

    observation = Observation(
        state=state,
        value=document["final_output"],
        provenance=document["attestation_id"],
    )
    return ContinuityTransition(
        parent_attestation_id=document["attestation_id"],
        observation=observation,
    )

from __future__ import annotations

"""Adapter from signed attestations into the existing Observer/Continuous Becoming boundary.

This module deliberately does not create a second lifecycle. It independently
verifies a signed attestation and projects its already-recorded result into the
repository's real ``observer.Observation`` shape. ContinuousBecomingEngine can
then consume that observation without bypassing the existing lifecycle.
"""

from dataclasses import dataclass

from attestation_protocol import SignedAttestation, hash_json, verify_attestation
from observer import Observation


@dataclass(frozen=True)
class ContinuityTransition:
    parent_attestation_id: str
    observation: Observation


def transition_from_attestation(
    attestation: SignedAttestation,
    *,
    expected_schema_digest: str | None = None,
) -> ContinuityTransition:
    """Project an independently verified attestation into an Observation.

    No lifecycle state is mutated here. The existing
    ``ContinuousBecomingEngine.advance`` remains the only transition engine.
    """
    report = verify_attestation(
        attestation.to_dict(),
        expected_schema_digest=expected_schema_digest,
    )
    if not report["valid"]:
        raise ValueError("cannot transition from an invalid attestation")

    document = attestation.document
    verification = document.get("verification", {})
    dissent = document.get("dissent", [])
    provenance = tuple(
        value
        for value in (
            document.get("attestation_id"),
            verification.get("cycle_id"),
            verification.get("contract_id"),
        )
        if value
    )

    observation = Observation(
        state=str(document.get("attestation_status", "UNVERIFIED")).lower(),
        verification_status=str(verification.get("status", "UNVERIFIED")).lower(),
        authorization_level="unknown",
        confidence=verification.get("confidence"),
        dissent=bool(dissent),
        provenance=provenance,
        verification_hash=hash_json(verification),
        attested=True,
        next_state=str(document.get("next_state", "observe")),
    )
    return ContinuityTransition(
        parent_attestation_id=str(document["attestation_id"]),
        observation=observation,
    )

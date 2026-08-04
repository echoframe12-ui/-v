from __future__ import annotations

"""Auditable lineage projection from signed Ω∞v attestations to Observation."""

from dataclasses import dataclass
from attestation_continuity import ContinuityTransition, transition_from_attestation
from attestation_protocol import SignedAttestation
from observer import Observation

@dataclass(frozen=True)
class ObserverLineage:
    attestation_id: str
    parent_attestation_id: str | None
    observation: Observation
    lineage_depth: int


def project(attestation: SignedAttestation, *, expected_schema_digest: str | None = None) -> ObserverLineage:
    transition: ContinuityTransition = transition_from_attestation(attestation, expected_schema_digest=expected_schema_digest)
    parent = attestation.document.get("parent_attestation_id")
    return ObserverLineage(transition.parent_attestation_id, parent, transition.observation, 1 if parent else 0)

from __future__ import annotations

"""Preserve verified attestation lineage across Continuous Becoming."""

from dataclasses import dataclass
from typing import Any

from continuous_becoming import BecomingTransition, ContinuousBecomingEngine
from observer import Observation


@dataclass(frozen=True)
class BecomingLineage:
    transition: BecomingTransition
    attestation_id: str
    parent_attestation_id: str | None
    lineage_depth: int


def advance_with_lineage(
    observation: Observation,
    *,
    attestation_id: str,
    parent_attestation_id: str | None = None,
    lineage_depth: int = 0,
) -> BecomingLineage:
    """Advance the canonical engine without discarding attestation provenance."""
    if lineage_depth < 0:
        raise ValueError("lineage_depth must be non-negative")
    if parent_attestation_id is not None and lineage_depth == 0:
        raise ValueError("a parent attestation requires positive lineage depth")

    transition = ContinuousBecomingEngine().advance(observation)
    return BecomingLineage(
        transition=transition,
        attestation_id=attestation_id,
        parent_attestation_id=parent_attestation_id,
        lineage_depth=lineage_depth,
    )


def to_dict(lineage: BecomingLineage) -> dict[str, Any]:
    return {
        "attestation_id": lineage.attestation_id,
        "parent_attestation_id": lineage.parent_attestation_id,
        "lineage_depth": lineage.lineage_depth,
        "transition": ContinuousBecomingEngine.to_dict(lineage.transition),
    }

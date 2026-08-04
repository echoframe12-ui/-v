from __future__ import annotations

"""Preserve Ω∞ attestation lineage when runtime evidence becomes evolution."""

from dataclasses import dataclass
from typing import Any
from oceanic_attestation import Attestation
from oceanic_evolution import EvolutionProposal, propose_evolution
from oceanic_observer import Observation

LINEAGE_SCHEMA = "omega.evolution-lineage/v1"

@dataclass(frozen=True)
class EvolutionLineage:
    attestation_id: str
    parent_attestation_id: str | None
    runtime_digest: str
    proposal: EvolutionProposal | None
    lineage_depth: int


def propose_with_lineage(attestation: Attestation, observation: Observation, *, parent_attestation_id: str | None = None, lineage_depth: int = 0) -> EvolutionLineage:
    if observation.contract_id != attestation.contract_id:
        raise ValueError("observation and attestation contract IDs must match")
    if lineage_depth < 0:
        raise ValueError("lineage_depth must be non-negative")
    if parent_attestation_id is not None and lineage_depth == 0:
        raise ValueError("a parent attestation requires positive lineage depth")
    proposal = propose_evolution(attestation, observation)
    return EvolutionLineage(attestation.attestation_id, parent_attestation_id, observation.runtime_digest, proposal, lineage_depth)


def to_dict(lineage: EvolutionLineage) -> dict[str, Any]:
    return {"schema": LINEAGE_SCHEMA, "attestation_id": lineage.attestation_id, "parent_attestation_id": lineage.parent_attestation_id, "runtime_digest": lineage.runtime_digest, "lineage_depth": lineage.lineage_depth, "proposal": lineage.proposal.to_dict() if lineage.proposal else None}

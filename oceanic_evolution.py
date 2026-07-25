from __future__ import annotations

"""Evidence-preserving evolution proposals for Ω∞ Oceanic."""

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from oceanic_attestation import Attestation
from oceanic_observer import Observation


@dataclass(frozen=True)
class EvolutionProposal:
    proposal_id: str
    contract_id: str
    attestation_id: str
    observation_status: str
    category: str
    reason: str
    proposed_changes: tuple[str, ...]
    requires_human_review: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "oceanic.evolution-proposal/v0.1",
            "proposal_id": self.proposal_id,
            "contract_id": self.contract_id,
            "attestation_id": self.attestation_id,
            "observation_status": self.observation_status,
            "category": self.category,
            "reason": self.reason,
            "proposed_changes": list(self.proposed_changes),
            "requires_human_review": self.requires_human_review,
        }


def propose_evolution(
    attestation: Attestation,
    observation: Observation,
) -> EvolutionProposal | None:
    """Turn runtime evidence into a proposal without mutating history."""
    if observation.contract_id != attestation.contract_id:
        raise ValueError("observation and attestation contract IDs must match")

    if observation.status == "matched":
        return None

    if observation.status != "deviated":
        category = "inconclusive_observation"
        changes = (
            "clarify the contract evidence required for a conclusive observation",
            "add an explicit observation rule for the ambiguous runtime state",
        )
    else:
        category = "contract_runtime_deviation"
        changes = (
            "review whether the contract invariant is incomplete",
            "review whether the adapter proof obligation is incomplete",
            "consider adding a dissent trigger for the observed deviation",
        )

    reason = "; ".join(observation.deviations) or "runtime behavior requires review"
    seed = json.dumps(
        {
            "attestation_id": attestation.attestation_id,
            "runtime_digest": observation.runtime_digest,
            "category": category,
            "reason": reason,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    proposal_id = "evo_" + hashlib.sha256(seed.encode("utf-8")).hexdigest()[:24]

    return EvolutionProposal(
        proposal_id=proposal_id,
        contract_id=attestation.contract_id,
        attestation_id=attestation.attestation_id,
        observation_status=observation.status,
        category=category,
        reason=reason,
        proposed_changes=changes,
    )

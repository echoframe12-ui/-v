from __future__ import annotations

"""Observer boundary for the Ω∞ Oceanic runtime.

The Observer does not invent a conclusion. It exposes the state produced by
verification and authorization so the next state transition is auditable.
"""

from dataclasses import dataclass
from typing import Any

from stack_runner import StackRun


@dataclass(frozen=True)
class Observation:
    state: str
    verification_status: str
    authorization_level: str
    confidence: float | None
    dissent: bool
    provenance: tuple[str, ...]
    verification_hash: str
    attested: bool
    next_state: str


class Observer:
    """Read-only projection of a completed Oceanic stack run."""

    def observe(self, run: StackRun) -> Observation:
        verification = run.verification
        authorization = run.authorization

        if verification.status != "verified":
            state = "held"
            next_state = "verify_again"
        elif authorization.requires_human:
            state = "human_review"
            next_state = "await_human"
        elif authorization.level.value == "act":
            state = "authorized"
            next_state = "act_then_observe"
        elif authorization.level.value == "propose":
            state = "proposal_ready"
            next_state = "await_confirmation"
        else:
            state = "observed"
            next_state = "continue_observing"

        return Observation(
            state=state,
            verification_status=verification.status,
            authorization_level=authorization.level.value,
            confidence=verification.confidence,
            dissent=verification.dissent,
            provenance=verification.provenance,
            verification_hash=verification.result_hash,
            attested=run.attestation is not None,
            next_state=next_state,
        )

    @staticmethod
    def to_dict(observation: Observation) -> dict[str, Any]:
        return {
            "state": observation.state,
            "verification_status": observation.verification_status,
            "authorization_level": observation.authorization_level,
            "confidence": observation.confidence,
            "dissent": observation.dissent,
            "provenance": list(observation.provenance),
            "verification_hash": observation.verification_hash,
            "attested": observation.attested,
            "next_state": observation.next_state,
        }

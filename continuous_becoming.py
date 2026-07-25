from __future__ import annotations

"""Continuous Becoming boundary for the Ω∞ Oceanic stack.

The engine does not terminate the system; it turns an observation into the
next auditable transition while preserving the reason the transition exists.
"""

from dataclasses import dataclass
from typing import Any

from observer import Observation


@dataclass(frozen=True)
class BecomingTransition:
    current_state: str
    next_state: str
    action: str
    loop: bool
    reason: str
    provenance: tuple[str, ...]
    verification_hash: str


class ContinuousBecomingEngine:
    """Translate an observation into the next state transition."""

    def advance(self, observation: Observation) -> BecomingTransition:
        if observation.state == "held":
            action = "reverify"
            reason = "Verification was held; the system loops back for another evidence-bound pass."
            loop = True
        elif observation.state == "human_review":
            action = "await_human"
            reason = "Material dissent requires human judgment before any further action."
            loop = True
        elif observation.state == "proposal_ready":
            action = "await_confirmation"
            reason = "A proposal exists, but confirmation is still required before action."
            loop = True
        elif observation.state == "authorized":
            action = "continue_becoming"
            reason = "The run is authorized; the next bounded state may proceed."
            loop = True
        else:
            action = "observe"
            reason = "The system remains in observation until new evidence arrives."
            loop = True

        return BecomingTransition(
            current_state=observation.state,
            next_state=observation.next_state,
            action=action,
            loop=loop,
            reason=reason,
            provenance=observation.provenance,
            verification_hash=observation.verification_hash,
        )

    @staticmethod
    def to_dict(transition: BecomingTransition) -> dict[str, Any]:
        return {
            "current_state": transition.current_state,
            "next_state": transition.next_state,
            "action": transition.action,
            "loop": transition.loop,
            "reason": transition.reason,
            "provenance": list(transition.provenance),
            "verification_hash": transition.verification_hash,
        }

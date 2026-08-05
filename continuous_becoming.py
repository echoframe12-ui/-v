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

    def advance_mood(
        self,
        assessment: Any,
        *,
        current_state: str = "observed",
        provenance: tuple[str, ...] = ("mood",),
        verification_hash: str = "",
    ) -> BecomingTransition:
        """Translate a MOOD assessment into a BecomingTransition."""
        requires_human = getattr(assessment, "requires_human", False)
        status = getattr(assessment, "status", "clear")
        gaps = getattr(assessment, "gaps", ())

        if requires_human or status == "dissent":
            next_state = "await_human"
            action = "await_human"
            reason = f"MOOD dissent: {', '.join(gaps) if gaps else 'dissent detected'}"
        else:
            next_state = "act_then_observe"
            action = "continue_becoming"
            reason = "MOOD clear: verification passed"

        return BecomingTransition(
            current_state=current_state,
            next_state=next_state,
            action=action,
            loop=True,
            reason=reason,
            provenance=provenance,
            verification_hash=verification_hash,
        )

    def advance_consensus(
        self,
        result: Any,
        *,
        current_state: str = "consensus_evaluating",
    ) -> BecomingTransition:
        """Translate a MultiAgentConsensusResult into a BecomingTransition."""
        converged = getattr(result, "converged", False)
        score = getattr(result, "final_dissent_score", 0.0)
        prompt = getattr(result, "prompt", "unknown")

        if converged:
            next_state = "consensus_reached"
            action = "continue_becoming"
            reason = f"Consensus converged (dissent score: {score})"
        else:
            next_state = "await_human"
            action = "await_human"
            reason = f"Consensus failed to converge (dissent score: {score}); human review required"

        return BecomingTransition(
            current_state=current_state,
            next_state=next_state,
            action=action,
            loop=True,
            reason=reason,
            provenance=("multi_agent_consensus", prompt[:32]),
            verification_hash=getattr(result, "assessment", None).assessment_id if getattr(result, "assessment", None) else "",
        )

    def advance_handoff(
        self,
        packet: Any,
        *,
        current_state: str = "handoff_pending",
    ) -> BecomingTransition:
        """Translate a HandoffPacket into a BecomingTransition."""
        packet_id = getattr(packet, "packet_id", "unknown")
        source = getattr(packet, "source_repo", "unknown")
        target = getattr(packet, "target_repo", "unknown")
        state_hash = getattr(packet, "state_hash", "")

        return BecomingTransition(
            current_state=current_state,
            next_state="handoff_transferred",
            action="continue_becoming",
            loop=True,
            reason=f"State handoff {packet_id} active: {source} -> {target}",
            provenance=(source, target, packet_id),
            verification_hash=state_hash,
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

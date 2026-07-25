from __future__ import annotations

"""Proactive proposal layer for Ω∞ Oceanic.

The system may anticipate and propose, but proposals remain subject to the
same verification and authorization boundaries as reactive work.
"""

from dataclasses import dataclass
from typing import Any, Callable, Iterable

from authorization import ActionLevel, AuthorizationDecision


@dataclass(frozen=True)
class Proposal:
    id: str
    trigger: str
    hypothesis: str
    evidence_refs: tuple[str, ...]
    expected_value: float | None = None
    risk: float | None = None
    metadata: dict[str, Any] | None = None


@dataclass(frozen=True)
class ProposalDecision:
    proposal: Proposal
    authorization: AuthorizationDecision
    status: str
    reason: str


class ProactiveEngine:
    """Generate bounded proposals without bypassing authorization."""

    def __init__(self, generators: Iterable[Callable[[Any], Iterable[Proposal]]] = ()):
        self.generators = tuple(generators)

    def propose(self, observation: Any) -> tuple[Proposal, ...]:
        proposals: list[Proposal] = []
        for generator in self.generators:
            proposals.extend(generator(observation))
        return tuple(proposals)

    @staticmethod
    def route(proposal: Proposal, authorization: AuthorizationDecision) -> ProposalDecision:
        if authorization.level == ActionLevel.ACT:
            return ProposalDecision(
                proposal=proposal,
                authorization=authorization,
                status="authorized",
                reason="Proposal may proceed under the active authorization policy.",
            )

        if authorization.level == ActionLevel.PROPOSE:
            return ProposalDecision(
                proposal=proposal,
                authorization=authorization,
                status="awaiting_confirmation",
                reason="Proposal is permitted but requires explicit confirmation before action.",
            )

        if authorization.level == ActionLevel.HUMAN_REVIEW:
            return ProposalDecision(
                proposal=proposal,
                authorization=authorization,
                status="human_review",
                reason="Proposal is routed to human judgment because authorization requires review.",
            )

        if authorization.level == ActionLevel.REPORT:
            return ProposalDecision(
                proposal=proposal,
                authorization=authorization,
                status="report_only",
                reason="Proposal cannot advance beyond reporting under current evidence.",
            )

        return ProposalDecision(
            proposal=proposal,
            authorization=authorization,
            status="held",
            reason="Proposal is blocked because verification or authorization is incomplete.",
        )

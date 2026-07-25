from __future__ import annotations

"""Explicit authorization gate for Ω∞ Oceanic.

Verification establishes that checks passed. Authorization decides what the
system is permitted to do next. These are intentionally separate concerns.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Iterable

from verification_pipeline import VerificationResult


class ActionLevel(str, Enum):
    REPORT = "report"
    HUMAN_REVIEW = "human_review"
    PROPOSE = "propose"
    ACT = "act"
    HOLD = "hold"


@dataclass(frozen=True)
class AuthorizationPolicy:
    """Policy thresholds for moving from evidence to action."""

    proposal_confidence: float = 0.74
    action_confidence: float = 0.90
    require_human_for_dissent: bool = True


@dataclass(frozen=True)
class AuthorizationDecision:
    level: ActionLevel
    reason: str
    verification_hash: str
    requires_human: bool


class AuthorizationGate:
    """Convert verified evidence into an explicit permission boundary."""

    def __init__(self, policy: AuthorizationPolicy | None = None):
        self.policy = policy or AuthorizationPolicy()
        self._validate_policy()

    def decide(self, verification: VerificationResult) -> AuthorizationDecision:
        if verification.status != "verified":
            return self._decision(
                ActionLevel.HOLD,
                "Verification is not complete; no downstream action is authorized.",
                verification,
                True,
            )

        if verification.dissent and self.policy.require_human_for_dissent:
            return self._decision(
                ActionLevel.HUMAN_REVIEW,
                "Material dissent is present and policy requires human review.",
                verification,
                True,
            )

        if verification.confidence is None:
            return self._decision(
                ActionLevel.REPORT,
                "Verification passed, but confidence is unavailable; reporting only.",
                verification,
                False,
            )

        if verification.confidence >= self.policy.action_confidence:
            return self._decision(
                ActionLevel.ACT,
                "Verification passed and confidence meets the action threshold.",
                verification,
                False,
            )

        if verification.confidence >= self.policy.proposal_confidence:
            return self._decision(
                ActionLevel.PROPOSE,
                "Verification passed and confidence permits a proposal, not autonomous action.",
                verification,
                False,
            )

        return self._decision(
            ActionLevel.REPORT,
            "Verification passed, but confidence is below the proposal threshold.",
            verification,
            False,
        )

    def _decision(
        self,
        level: ActionLevel,
        reason: str,
        verification: VerificationResult,
        requires_human: bool,
    ) -> AuthorizationDecision:
        return AuthorizationDecision(
            level=level,
            reason=reason,
            verification_hash=verification.result_hash,
            requires_human=requires_human,
        )

    def _validate_policy(self) -> None:
        values = (self.policy.proposal_confidence, self.policy.action_confidence)
        if any(not 0.0 <= value <= 1.0 for value in values):
            raise ValueError("confidence thresholds must be between 0.0 and 1.0")
        if self.policy.proposal_confidence > self.policy.action_confidence:
            raise ValueError("proposal threshold cannot exceed action threshold")

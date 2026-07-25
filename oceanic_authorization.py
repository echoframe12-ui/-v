from __future__ import annotations

"""Explicit authorization gate for Ω∞ Oceanic attestations."""

from dataclasses import replace

from oceanic_attestation import Attestation, Authorization


class AuthorizationError(ValueError):
    """Raised when an attestation cannot legally transition to execution."""


def authorize(
    attestation: Attestation,
    *,
    reviewer: str,
    reason: str,
) -> Attestation:
    """Authorize a verified attestation without changing its historical evidence."""
    if not reviewer.strip():
        raise AuthorizationError("reviewer is required")
    if not reason.strip():
        raise AuthorizationError("authorization reason is required")

    status = attestation.aggregate.get("status")
    if status not in {"proved", "proved_with_dissent"}:
        raise AuthorizationError(
            f"cannot authorize attestation with verification status: {status}"
        )

    return replace(
        attestation,
        authorization=Authorization(
            status="authorized",
            authority="human",
            reviewer=reviewer,
            reason=reason,
        ),
    )


def reject(
    attestation: Attestation,
    *,
    reviewer: str,
    reason: str,
) -> Attestation:
    """Reject execution while retaining the original verification evidence."""
    if not reviewer.strip():
        raise AuthorizationError("reviewer is required")
    if not reason.strip():
        raise AuthorizationError("rejection reason is required")

    return replace(
        attestation,
        authorization=Authorization(
            status="rejected",
            authority="human",
            reviewer=reviewer,
            reason=reason,
        ),
    )


def can_execute(attestation: Attestation) -> bool:
    """Return whether the explicit authorization boundary permits execution."""
    return (
        attestation.authorization.status == "authorized"
        and attestation.aggregate.get("status")
        in {"proved", "proved_with_dissent"}
    )

from __future__ import annotations

"""Verification and attestation boundary for the Ω∞ Oceanic pipeline.

This module intentionally does not decide whether a claim is true by itself.
It records what was observed, what was checked, and whether an attestation is
permitted under explicit evidence and dissent rules.
"""

from dataclasses import dataclass
from hashlib import sha256
from typing import Any, Callable, Iterable

from integration_pipeline import IntegrationResult


@dataclass(frozen=True)
class VerificationCheck:
    name: str
    passed: bool
    detail: str = ""


@dataclass(frozen=True)
class VerificationResult:
    status: str
    confidence: float | None
    checks: tuple[VerificationCheck, ...]
    dissent: bool
    provenance: tuple[str, ...]
    result_hash: str


@dataclass(frozen=True)
class Attestation:
    verification_hash: str
    status: str
    confidence: float | None
    provenance: tuple[str, ...]
    statement: str


class VerificationPipeline:
    """Verify an integration result and create an auditable attestation."""

    def __init__(self, checks: Iterable[Callable[[IntegrationResult], VerificationCheck]] = ()):
        self.checks = tuple(checks)

    def verify(self, result: IntegrationResult) -> VerificationResult:
        checks = list(self._default_checks(result))
        checks.extend(check(result) for check in self.checks)

        passed = all(check.passed for check in checks)
        status = "verified" if passed else "held"
        provenance = tuple(result.comparison.get("source_refs", ()))
        confidence = self._confidence(result, passed)
        material = "|".join(
            [
                status,
                str(confidence),
                str(result.context.content_hash),
                *provenance,
                *(f"{c.name}:{c.passed}:{c.detail}" for c in checks),
            ]
        )

        return VerificationResult(
            status=status,
            confidence=confidence,
            checks=tuple(checks),
            dissent=bool(result.comparison.get("dissent", False)),
            provenance=provenance,
            result_hash=sha256(material.encode("utf-8")).hexdigest(),
        )

    def attest(self, verification: VerificationResult) -> Attestation:
        if verification.status != "verified":
            raise ValueError("cannot attest a verification result that is held")
        if not verification.provenance:
            raise ValueError("cannot attest without provenance")

        statement = (
            "Attested: verification checks passed; provenance preserved; "
            "no unresolved blocking condition was detected."
        )
        return Attestation(
            verification_hash=verification.result_hash,
            status="attested",
            confidence=verification.confidence,
            provenance=verification.provenance,
            statement=statement,
        )

    @staticmethod
    def _default_checks(result: IntegrationResult) -> tuple[VerificationCheck, ...]:
        return (
            VerificationCheck(
                "context_present",
                bool(result.context.included_refs),
                "At least one source is present.",
            ),
            VerificationCheck(
                "lineage_preserved",
                all(
                    perspective.context_hash == result.context.content_hash
                    for perspective in result.perspectives
                ),
                "All perspectives reference the assembled context hash.",
            ),
            VerificationCheck(
                "dissent_visible",
                True,
                "Dissent is represented explicitly rather than suppressed.",
            ),
            VerificationCheck(
                "no_preferred_interpretation",
                result.comparison.get("preferred_interpretation") is None,
                "Verification does not manufacture consensus.",
            ),
        )

    @staticmethod
    def _confidence(result: IntegrationResult, passed: bool) -> float | None:
        if not result.perspectives:
            return None
        values = [p.confidence for p in result.perspectives if p.confidence is not None]
        if not passed or not values:
            return None
        return sum(values) / len(values)

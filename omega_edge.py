from __future__ import annotations

"""Thin Ω∞v Edge boundary.

Edge transports and independently verifies signed attestations; it does not
create signatures or redefine lifecycle verification.
"""

from dataclasses import dataclass
from typing import Any

from attestation_protocol import verify_attestation


@dataclass(frozen=True)
class EdgeVerification:
    valid: bool
    report: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {"valid": self.valid, "report": self.report}


def verify_edge_attestation(
    attestation: dict[str, Any],
    *,
    expected_schema_digest: str | None = None,
) -> EdgeVerification:
    """Verify an inbound Ω∞v attestation using the canonical verifier."""
    report = verify_attestation(
        attestation,
        expected_schema_digest=expected_schema_digest,
    )
    return EdgeVerification(valid=bool(report.get("valid")), report=report)

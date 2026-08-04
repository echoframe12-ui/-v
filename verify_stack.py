"""Single verification gate for the OceanicOS full stack."""

from dataclasses import dataclass
from typing import Any

from mood import MoodAssessment, MoodSignal, assess


@dataclass(frozen=True)
class VerificationResult:
    checks: dict[str, bool]
    mood: MoodAssessment

    @property
    def verified(self) -> bool:
        return all(self.checks.values()) and self.mood.status == "clear"


def verify(evidence: dict[str, Any]) -> VerificationResult:
    """Evaluate supplied runtime evidence without inventing missing checks."""
    checks = {
        "deployment": bool(evidence.get("deployment_ready", False)),
        "smoke": bool(evidence.get("smoke_ready", False)),
        "status_endpoint": evidence.get("status_code") == 200,
        "request_id": evidence.get("request_id") == "production-smoke",
        "integrity": bool(evidence.get("integrity", False)),
    }

    signals = [
        MoodSignal(name, value, "verification")
        for name, value in checks.items()
    ]
    mood = assess(signals)
    return VerificationResult(checks=checks, mood=mood)

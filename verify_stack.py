"""Single live verification gate for the OceanicOS full stack."""

from __future__ import annotations

import tempfile
from dataclasses import dataclass
from pathlib import Path
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
    signals = [MoodSignal(name, value, "verification") for name, value in checks.items()]
    return VerificationResult(checks=checks, mood=assess(signals))


def verify_live() -> VerificationResult:
    """Exercise the real app test client and feed its E2E evidence into MOOD."""
    from app import app, service
    from final_e2e import verify as verify_e2e
    from mood_integrity import assess_e2e

    with tempfile.TemporaryDirectory(prefix="oceanicos-verify-") as root:
        root_path = Path(root)
        db_path = root_path / "verify.db"
        workspace = root_path / "workspace"
        previous_db = service._db_path
        try:
            service._db_path = db_path
            service._init_db()
            with app.test_client() as client:
                e2e = verify_e2e(client, db_path=str(db_path), workspace=str(workspace))
            mood = assess_e2e(e2e)
            checks = {
                "deployment": e2e.deployment["ready"],
                "smoke": e2e.smoke_ready,
                "status_endpoint": e2e.status_code == 200,
                "request_id": e2e.request_id == "production-smoke",
                "integrity": e2e.integrity,
            }
            return VerificationResult(checks=checks, mood=mood)
        finally:
            service._db_path = previous_db


def main() -> int:
    result = verify_live()
    print("OceanicOS full-stack verification")
    for name, passed in result.checks.items():
        print(f"{name:18} {'PASS' if passed else 'FAIL'}")
    print(f"MOOD               {result.mood.status.upper()}")
    print(f"ROUTE              {result.mood.route}")
    print(f"VERIFIED           {'YES' if result.verified else 'NO'}")
    if result.mood.gaps:
        print("GAPS               " + ", ".join(result.mood.gaps))
    return 0 if result.verified else 1


if __name__ == "__main__":
    raise SystemExit(main())

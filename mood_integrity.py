"""Bridge deployment/E2E evidence into the MOOD routing layer."""

from typing import Any

from mood import MoodAssessment, MoodSignal, assess


def assess_e2e(result: Any) -> MoodAssessment:
    """Turn final E2E evidence into an explicit MOOD assessment."""
    signals = [
        MoodSignal("deployment_ready", result.deployment["ready"], "deployment"),
        MoodSignal("smoke_ready", result.smoke_ready, "production-smoke"),
        MoodSignal("status_endpoint", result.status_code == 200, "production-smoke"),
        MoodSignal("request_id", result.request_id == "production-smoke", "production-smoke"),
        MoodSignal("integrity", result.integrity, "final-e2e"),
    ]
    return assess(signals)

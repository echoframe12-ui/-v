"""Bridge deployment/E2E evidence and Ω∞v contract gate into the MOOD routing layer."""

from typing import Any

from full_stack_e2e_gate import check as check_contract_stack
from mood import MoodAssessment, MoodSignal, assess


def assess_e2e(result: Any) -> MoodAssessment:
    """Turn final E2E evidence into an explicit MOOD assessment."""
    contract_stack = getattr(result, "contract_stack", None)
    if contract_stack is None:
        contract_stack = check_contract_stack()

    contract_healthy = bool(contract_stack.get("ok"))
    edge_enforced = bool(contract_stack.get("edge_rejects_empty_attestation"))

    signals = [
        MoodSignal("contract_stack_healthy", contract_healthy, "full-stack-e2e-gate"),
        MoodSignal("edge_attestation_enforced", edge_enforced, "full-stack-e2e-gate"),
        MoodSignal("deployment_ready", result.deployment["ready"], "deployment"),
        MoodSignal("smoke_ready", result.smoke_ready, "production-smoke"),
        MoodSignal("status_endpoint", result.status_code == 200, "production-smoke"),
        MoodSignal("request_id", result.request_id == "production-smoke", "production-smoke"),
        MoodSignal("integrity", result.integrity, "final-e2e"),
    ]
    return assess(signals)


def assess_full_stack(client: Any, *, db_path: str, workspace: str) -> MoodAssessment:
    """Run full E2E verification and return the unified MOOD assessment."""
    from final_e2e import verify

    e2e_result = verify(client, db_path=db_path, workspace=workspace)
    return assess_e2e(e2e_result)

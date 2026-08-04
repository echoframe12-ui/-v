"""Bridge deployment/E2E evidence and Ω∞v contract gate into the MOOD routing layer."""

from typing import Any

from full_stack_e2e_gate import check as check_contract_stack
from mood import MoodAssessment, MoodSignal, assess, record_to_ledger


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


def assess_full_stack(
    client: Any,
    *,
    db_path: str,
    workspace: str,
    ledger: Any | None = None,
) -> MoodAssessment:
    """Run full E2E verification and return the unified MOOD assessment.

    When *ledger* is provided (an ``EventLedger`` instance), the assessment
    result is automatically recorded as a ``mood.clear`` or ``mood.dissent``
    event.
    """
    from final_e2e import verify

    e2e_result = verify(client, db_path=db_path, workspace=workspace)
    assessment = assess_e2e(e2e_result)
    if ledger is not None:
        record_to_ledger(assessment, ledger, entity_id="full-stack-e2e")
    return assessment


def assess_perspectives(
    perspectives: list[Any],
    *,
    ledger: Any | None = None,
    entity_id: str = "perspective-panel",
) -> MoodAssessment:
    """Turn a list of Perspective objects into an explicit MOOD assessment.

    Evaluates cross-provider responses, surfacing any dissent or low confidence
    as explicit gaps routing to human review.
    """
    signals = []
    for p in perspectives:
        conf = getattr(p, "confidence", None)
        confidence = conf if conf is not None else 1.0
        signals.append(
            MoodSignal(
                name="response",
                value=getattr(p, "response", None),
                source=getattr(p, "provider", "unknown"),
                confidence=confidence,
            )
        )
    assessment = assess(signals)
    if ledger is not None:
        record_to_ledger(assessment, ledger, entity_id=entity_id)
    return assessment



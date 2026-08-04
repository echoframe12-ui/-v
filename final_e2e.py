from __future__ import annotations

"""Final deterministic end-to-end integrity gate unifying contract stack and runtime verification."""

from dataclasses import dataclass
from typing import Any

from deployment_contract import evaluate, to_dict
from full_stack_e2e_gate import check as check_contract_stack
from production_smoke import run as run_smoke


@dataclass(frozen=True)
class FinalE2E:
    deployment: dict[str, Any]
    smoke_ready: bool
    status_code: int
    request_id: str
    integrity: bool
    contract_stack: dict[str, Any] | None = None


def verify(client: Any, *, db_path: str, workspace: str) -> FinalE2E:
    contract = evaluate(db_path=db_path, workspace=workspace)
    smoke = run_smoke(client, db_path=db_path, workspace=workspace)
    contract_gate = check_contract_stack()
    deployment = to_dict(contract)
    required_checks = set(deployment["required_checks"])
    smoke_check_names = set(smoke.checks)
    integrity = (
        smoke.ready
        and smoke.status_code == 200
        and smoke.request_id == "production-smoke"
        and deployment["ready"] is True
        and required_checks.issubset(smoke_check_names)
        and all(smoke.checks[name] for name in required_checks)
        and smoke.checks["status_endpoint"] is True
        and bool(contract_gate.get("ok"))
    )
    return FinalE2E(
        deployment=deployment,
        smoke_ready=smoke.ready,
        status_code=smoke.status_code,
        request_id=smoke.request_id,
        integrity=integrity,
        contract_stack=contract_gate,
    )

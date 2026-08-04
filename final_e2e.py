from __future__ import annotations

"""Final deterministic end-to-end integrity gate."""

from dataclasses import dataclass
from typing import Any

from deployment_contract import build_contract
from production_smoke import run as run_smoke


@dataclass(frozen=True)
class FinalE2E:
    deployment: dict[str, Any]
    smoke_ready: bool
    status_code: int
    request_id: str
    integrity: bool


def verify(client: Any, *, db_path: str, workspace: str) -> FinalE2E:
    contract = build_contract(client, db_path=db_path, workspace=workspace)
    smoke = run_smoke(client, db_path=db_path, workspace=workspace)
    deployment = contract.to_dict()
    integrity = (
        smoke.ready
        and smoke.status_code == 200
        and smoke.request_id == "production-smoke"
        and deployment["ready"] is True
        and deployment["checks"] == smoke.checks
    )
    return FinalE2E(
        deployment=deployment,
        smoke_ready=smoke.ready,
        status_code=smoke.status_code,
        request_id=smoke.request_id,
        integrity=integrity,
    )

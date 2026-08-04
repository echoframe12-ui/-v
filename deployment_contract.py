from __future__ import annotations

"""Deterministic deployment contract for the validated application boundary."""

from dataclasses import dataclass
from typing import Any

from readiness import probe

DEPLOYMENT_SCHEMA = "oceanic.deployment-contract/v1"


@dataclass(frozen=True)
class DeploymentContract:
    schema: str
    status_endpoint: str
    required_checks: tuple[str, ...]
    ready: bool


def evaluate(*, db_path: str, workspace: str, status_endpoint: str = "/status.json") -> DeploymentContract:
    readiness: dict[str, Any] = probe(db_path, workspace)
    checks = tuple(sorted(readiness["checks"].keys()))
    return DeploymentContract(
        schema=DEPLOYMENT_SCHEMA,
        status_endpoint=status_endpoint,
        required_checks=checks,
        ready=bool(readiness["ready"]),
    )


def to_dict(contract: DeploymentContract) -> dict[str, Any]:
    return {
        "schema": contract.schema,
        "status_endpoint": contract.status_endpoint,
        "required_checks": list(contract.required_checks),
        "ready": contract.ready,
    }

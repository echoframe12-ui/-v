from __future__ import annotations

"""Runtime observation and contract/reality comparison for Ω∞ Oceanic."""

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Callable

from oceanic_attestation import Attestation, RuntimeState
from oceanic_authorization import can_execute


@dataclass(frozen=True)
class Observation:
    status: str
    contract_id: str
    runtime_digest: str
    expected: Any
    actual: Any
    deviations: tuple[str, ...] = ()
    evidence: str = ""


class ExecutionDenied(PermissionError):
    pass


def _digest(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, default=str, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def execute_and_observe(
    attestation: Attestation,
    *,
    execute: Callable[[], Any],
    expected: Any,
) -> tuple[Attestation, Observation]:
    """Execute only an authorized attestation and compare runtime reality."""
    if not can_execute(attestation):
        raise ExecutionDenied("attestation is not authorized for execution")

    actual = execute()
    deviations: list[str] = []
    status = "matched"
    if actual != expected:
        status = "deviated"
        deviations.append("runtime result differs from expected contract outcome")

    runtime_digest = _digest({"expected": expected, "actual": actual})
    observation = Observation(
        status=status,
        contract_id=attestation.contract_id,
        runtime_digest=runtime_digest,
        expected=expected,
        actual=actual,
        deviations=tuple(deviations),
        evidence="deterministic equality comparison",
    )

    updated = Attestation(
        schema=attestation.schema,
        attestation_id=attestation.attestation_id,
        contract_id=attestation.contract_id,
        created_at=attestation.created_at,
        adapters=attestation.adapters,
        aggregate=attestation.aggregate,
        authorization=attestation.authorization,
        runtime=RuntimeState(status="observed", runtime_digest=runtime_digest),
    )
    return updated, observation

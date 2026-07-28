from __future__ import annotations

"""Durable attestation generation for the Ω∞ Oceanic verification pipeline."""

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any

from oceanic_orchestrator import CompilationReport, VerificationReport


@dataclass(frozen=True)
class Authorization:
    status: str = "pending"
    authority: str = "human"
    reviewer: str | None = None
    reason: str | None = None


@dataclass(frozen=True)
class RuntimeState:
    status: str = "not_started"
    runtime_digest: str | None = None


@dataclass(frozen=True)
class Attestation:
    schema: str
    attestation_id: str
    contract_id: str
    created_at: str
    adapters: tuple[dict[str, Any], ...]
    aggregate: dict[str, Any]
    authorization: Authorization
    runtime: RuntimeState

    def canonical_payload(self) -> str:
        payload = asdict(self)
        return json.dumps(payload, sort_keys=True, separators=(",", ":"))

    def digest(self) -> str:
        return "sha256:" + hashlib.sha256(
            self.canonical_payload().encode("utf-8")
        ).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["attestation_digest"] = self.digest()
        return payload


def create_attestation(
    report: CompilationReport,
    *,
    authorization: Authorization | None = None,
) -> Attestation:
    """Convert one consolidated verification report into durable evidence."""
    created_at = datetime.now(timezone.utc).isoformat()

    # Derive overall status from CompilationReport results.
    has_supported = any(r.supported for r in report.results)
    has_dissent = bool(report.dissent)
    if has_supported and not has_dissent:
        overall_status = "proved"
    elif has_supported:
        overall_status = "proved_with_dissent"
    else:
        overall_status = "not_proved"

    adapter_records = tuple(
        {
            "language": result.language,
            "adapter_version": "1.0",
            "implementation_digest": hashlib.sha256(
                json.dumps(result.proof, sort_keys=True, default=str).encode("utf-8")
            ).hexdigest(),
            "proof_status": "proved" if result.supported else "not_proved",
            "confidence": result.confidence,
            "dissent": list(result.dissent),
        }
        for result in report.results
    )

    aggregate = {
        "status": overall_status,
        "confidence": report.confidence,
        "dissent": list(report.dissent),
    }

    seed = json.dumps(
        {
            "contract_id": report.contract_id,
            "created_at": created_at,
            "adapters": adapter_records,
            "aggregate": aggregate,
        },
        sort_keys=True,
        default=str,
        separators=(",", ":"),
    )
    attestation_id = "att_" + hashlib.sha256(seed.encode("utf-8")).hexdigest()[:24]

    return Attestation(
        schema="oceanic.attestation/v0.1",
        attestation_id=attestation_id,
        contract_id=report.contract_id,
        created_at=created_at,
        adapters=adapter_records,
        aggregate=aggregate,
        authorization=authorization or Authorization(),
        runtime=RuntimeState(),
    )


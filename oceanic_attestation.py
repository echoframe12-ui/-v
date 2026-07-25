from __future__ import annotations

"""Durable attestation generation for the Ω∞ Oceanic verification pipeline."""

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any

from oceanic_orchestrator import VerificationReport


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
    report: VerificationReport,
    *,
    authorization: Authorization | None = None,
) -> Attestation:
    """Convert one consolidated verification report into durable evidence."""
    created_at = datetime.now(timezone.utc).isoformat()
    adapter_records = tuple(
        {
            "language": run.language,
            "adapter_version": run.manifest.adapter_version,
            "implementation_digest": run.implementation_digest,
            "proof_status": run.outcome.status.value,
            "confidence": run.outcome.confidence,
            "dissent": list(run.outcome.dissent),
        }
        for run in report.runs
    )

    seed = json.dumps(
        {
            "contract_id": report.contract_id,
            "created_at": created_at,
            "adapters": adapter_records,
            "aggregate": {
                "status": report.overall_status.value,
                "confidence": report.confidence,
                "dissent": list(report.dissent),
            },
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
        aggregate={
            "status": report.overall_status.value,
            "confidence": report.confidence,
            "dissent": list(report.dissent),
        },
        authorization=authorization or Authorization(),
        runtime=RuntimeState(),
    )

from __future__ import annotations

"""Production-boundary smoke checks built on the existing Flask/readiness contracts."""

from dataclasses import dataclass
from typing import Any

from readiness import probe


@dataclass(frozen=True)
class ProductionSmoke:
    ready: bool
    checks: dict[str, bool]
    status_code: int
    content_type: str
    request_id: str


def run(client: Any, *, db_path: str, workspace: str) -> ProductionSmoke:
    readiness = probe(db_path, workspace)
    response = client.get("/status.json", headers={"X-Request-ID": "production-smoke"})
    request_id = response.headers.get("X-Request-ID", "")
    return ProductionSmoke(
        ready=readiness["ready"] and response.status_code == 200,
        checks={**readiness["checks"], "status_endpoint": response.status_code == 200},
        status_code=response.status_code,
        content_type=response.content_type or "",
        request_id=request_id,
    )

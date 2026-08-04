from __future__ import annotations

"""Small, dependency-light gate for the Ω∞v full-stack contract.

This module deliberately does not start Flask, open a database, or perform
network calls. It verifies that the major stack layers remain importable and
that the external Edge boundary still reaches the canonical verifier.
"""

from importlib import import_module
from typing import Any

STACK_MODULES = (
    "oceanic_ir",
    "oceanic_cycle",
    "oceanic_lifecycle",
    "attestation_protocol",
    "omega_vaas_bridge",
    "omega_edge",
    "omega_edge_http",
    "attestation_continuity",
    "continuous_becoming",
    "oceanic_observer",
    "oceanic_evolution",
    "oceanic_orchestrator",
)


def probe_stack() -> dict[str, Any]:
    """Return a deterministic, side-effect-free stack health report."""
    imports: dict[str, str] = {}
    for name in STACK_MODULES:
        try:
            import_module(name)
        except Exception as exc:  # pragma: no cover - surfaced by the gate
            imports[name] = f"error:{type(exc).__name__}:{exc}"
        else:
            imports[name] = "ok"

    from omega_edge import verify_edge_attestation

    edge = verify_edge_attestation({})
    return {
        "ok": all(status == "ok" for status in imports.values()) and edge.valid is False,
        "imports": imports,
        "edge_rejects_empty_attestation": edge.valid is False,
    }


def assert_stack_healthy() -> dict[str, Any]:
    report = probe_stack()
    if not report["ok"]:
        raise RuntimeError(f"full-stack gate failed: {report}")
    return report

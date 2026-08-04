from __future__ import annotations

"""Deterministic end-to-end contract gate for the Ω∞v stack."""

from importlib import import_module

STACK = (
    "oceanic_ir",
    "oceanic_attestation",
    "attestation_protocol",
    "oceanic_ir_attestation_contract",
    "omega_vaas_bridge",
    "omega_edge",
    "omega_edge_http",
    "attestation_continuity",
    "observer",
    "omega_observer_lineage",
    "continuous_becoming",
    "omega_becoming_lineage",
    "oceanic_observer",
    "oceanic_evolution",
    "omega_evolution_lineage",
    "oceanic_orchestrator",
)


def check() -> dict[str, object]:
    modules: dict[str, str] = {}
    for name in STACK:
        try:
            import_module(name)
        except Exception as exc:
            modules[name] = f"error:{type(exc).__name__}:{exc}"
        else:
            modules[name] = "ok"

    from omega_edge import verify_edge_attestation
    rejected = verify_edge_attestation({}).valid is False
    return {
        "ok": all(status == "ok" for status in modules.values()) and rejected,
        "modules": modules,
        "edge_rejects_empty_attestation": rejected,
    }


def assert_healthy() -> dict[str, object]:
    report = check()
    if not report["ok"]:
        raise AssertionError(report)
    return report

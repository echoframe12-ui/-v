from __future__ import annotations

from importlib import import_module

STACK = (
    "oceanic_ir",
    "oceanic_attestation",
    "attestation_protocol",
    "omega_vaas_bridge",
    "omega_edge",
    "omega_edge_http",
    "attestation_continuity",
    "observer",
    "continuous_becoming",
    "oceanic_observer",
    "oceanic_evolution",
    "omega_evolution_lineage",
    "oceanic_orchestrator",
)


def check():
    statuses = {}
    for name in STACK:
        try:
            import_module(name)
        except Exception as exc:
            statuses[name] = f"error:{type(exc).__name__}:{exc}"
        else:
            statuses[name] = "ok"

    from omega_edge import verify_edge_attestation

    rejected = verify_edge_attestation({}).valid is False
    return {
        "ok": all(value == "ok" for value in statuses.values()) and rejected,
        "modules": statuses,
        "edge_rejects_empty_attestation": rejected,
    }


def assert_healthy():
    report = check()
    if not report["ok"]:
        raise AssertionError(report)
    return report

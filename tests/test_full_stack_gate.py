from __future__ import annotations

from full_stack_gate import STACK_MODULES, assert_stack_healthy, probe_stack


def test_full_stack_modules_are_importable():
    report = probe_stack()
    assert report["ok"] is True
    assert report["edge_rejects_empty_attestation"] is True
    assert set(report["imports"]) == set(STACK_MODULES)
    assert all(status == "ok" for status in report["imports"].values())


def test_full_stack_gate_is_deterministic():
    first = assert_stack_healthy()
    second = assert_stack_healthy()
    assert first == second

from types import SimpleNamespace

from mood_integrity import assess_e2e, assess_full_stack


def test_e2e_clear_evidence_continues():
    result = SimpleNamespace(
        deployment={"ready": True},
        smoke_ready=True,
        status_code=200,
        request_id="production-smoke",
        integrity=True,
        contract_stack={"ok": True, "edge_rejects_empty_attestation": True},
    )
    assessment = assess_e2e(result)
    assert assessment.status == "clear"
    assert assessment.route == "continue"
    assert assessment.requires_human is False


def test_e2e_failed_integrity_routes_human():
    result = SimpleNamespace(
        deployment={"ready": True},
        smoke_ready=True,
        status_code=200,
        request_id="production-smoke",
        integrity=False,
        contract_stack={"ok": True, "edge_rejects_empty_attestation": True},
    )
    assessment = assess_e2e(result)
    assert assessment.status == "dissent"
    assert assessment.route == "human"
    assert assessment.requires_human is True


def test_e2e_failed_contract_stack_routes_human():
    result = SimpleNamespace(
        deployment={"ready": True},
        smoke_ready=True,
        status_code=200,
        request_id="production-smoke",
        integrity=True,
        contract_stack={"ok": False, "edge_rejects_empty_attestation": True},
    )
    assessment = assess_e2e(result)
    assert assessment.status == "dissent"
    assert assessment.route == "human"
    assert "failed:contract_stack_healthy" in assessment.gaps


def test_assess_full_stack_integration():
    from app import app

    client = app.test_client()
    assessment = assess_full_stack(client, db_path="oceanicos.db", workspace="workspace")
    assert assessment.status in ("clear", "dissent")
    assert hasattr(assessment, "route")

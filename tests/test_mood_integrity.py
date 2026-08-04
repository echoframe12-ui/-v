from types import SimpleNamespace

from mood_integrity import assess_e2e


def test_e2e_clear_evidence_continues():
    result = SimpleNamespace(
        deployment={"ready": True},
        smoke_ready=True,
        status_code=200,
        request_id="production-smoke",
        integrity=True,
    )
    assessment = assess_e2e(result)
    assert assessment.status == "clear"
    assert assessment.route == "continue"


def test_e2e_failed_integrity_routes_human():
    result = SimpleNamespace(
        deployment={"ready": True},
        smoke_ready=True,
        status_code=200,
        request_id="production-smoke",
        integrity=False,
    )
    assessment = assess_e2e(result)
    assert assessment.status == "dissent"
    assert assessment.route == "human"
    assert "low-confidence:integrity" not in assessment.gaps
    assert "dissent:integrity" not in assessment.gaps
    assert "dissent:integrity" in assessment.gaps or "low-confidence:integrity" in assessment.gaps or assessment.requires_human

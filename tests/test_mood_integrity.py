from types import SimpleNamespace

from mood_integrity import assess_e2e


def make_result(*, integrity: bool):
    return SimpleNamespace(
        deployment={"ready": True},
        smoke_ready=True,
        status_code=200,
        request_id="production-smoke",
        integrity=integrity,
    )


def test_e2e_clear_evidence_continues():
    assessment = assess_e2e(make_result(integrity=True))
    assert assessment.status == "clear"
    assert assessment.route == "continue"
    assert assessment.requires_human is False


def test_e2e_failed_integrity_routes_human():
    assessment = assess_e2e(make_result(integrity=False))
    assert assessment.status == "dissent"
    assert "low-confidence:integrity" in assessment.gaps
    assert assessment.route == "human"
    assert assessment.requires_human is True

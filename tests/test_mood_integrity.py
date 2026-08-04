from types import SimpleNamespace

from mood_integrity import assess_e2e


def result(**overrides):
    values = dict(
        deployment={"ready": True},
        smoke_ready=True,
        status_code=200,
        request_id="production-smoke",
        integrity=True,
    )
    values.update(overrides)
    return SimpleNamespace(**values)


def test_clear_e2e_evidence_continues():
    assessment = assess_e2e(result())
    assert assessment.status == "clear"
    assert assessment.route == "continue"
    assert assessment.requires_human is False


def test_failed_integrity_routes_human():
    assessment = assess_e2e(result(integrity=False))
    assert assessment.status == "dissent"
    assert assessment.route == "human"
    assert assessment.requires_human is True


def test_failed_status_routes_human():
    assessment = assess_e2e(result(status_code=503))
    assert assessment.status == "dissent"
    assert assessment.route == "human"
    assert assessment.requires_human is True

from verify_stack import verify


def test_verify_full_stack_passes_only_when_all_evidence_is_true():
    result = verify({
        "omega_contract": True,
        "deployment_ready": True,
        "smoke_ready": True,
        "status_code": 200,
        "request_id": "production-smoke",
        "integrity": True,
    })
    assert result.verified is True
    assert result.mood.status == "clear"
    assert result.mood.route == "continue"


def test_verify_routes_failed_evidence_to_mood():
    result = verify({
        "omega_contract": True,
        "deployment_ready": True,
        "smoke_ready": True,
        "status_code": 500,
        "request_id": "production-smoke",
        "integrity": True,
    })
    assert result.verified is False
    assert result.mood.status == "dissent"
    assert result.mood.route == "human"
    assert "failed:status_endpoint" in result.mood.gaps


def test_verify_requires_omega_contract():
    result = verify({
        "omega_contract": False,
        "deployment_ready": True,
        "smoke_ready": True,
        "status_code": 200,
        "request_id": "production-smoke",
        "integrity": True,
    })
    assert result.verified is False
    assert result.mood.status == "dissent"
    assert result.mood.route == "human"
    assert "failed:omega_contract" in result.mood.gaps

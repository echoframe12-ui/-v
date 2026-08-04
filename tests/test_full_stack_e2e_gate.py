from full_stack_e2e_gate import STACK, assert_healthy


def test_full_stack_contract_is_healthy():
    report = assert_healthy()
    assert report["edge_rejects_empty_attestation"] is True
    assert set(report["modules"]) == set(STACK)


def test_application_boundary_is_reachable():
    from app import app

    client = app.test_client()
    response = client.get("/status.json")
    assert response.status_code == 200
    assert response.is_json

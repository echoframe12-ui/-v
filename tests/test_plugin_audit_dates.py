from app import app


def test_plugin_audit_date_validation():
    import os

    os.environ["API_KEY"] = "test-key"
    client = app.test_client()
    headers = {"X-API-Key": "test-key"}

    # invalid start_ts
    res = client.get("/plugins/audit?start_ts=not-a-date", headers=headers)
    assert res.status_code == 400
    j = res.get_json()
    assert j.get("error") == "invalid date"

    # invalid end_ts
    res2 = client.get("/plugins/audit?end_ts=2021-13-01T00:00:00", headers=headers)
    assert res2.status_code == 400
    j2 = res2.get_json()
    assert j2.get("error") == "invalid date"

    # valid ISO should return 200
    res3 = client.get("/plugins/audit?start_ts=2021-01-01T00:00:00", headers=headers)
    assert res3.status_code == 200

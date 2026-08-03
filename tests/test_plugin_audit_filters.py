from app import app


def test_plugin_audit_filters_and_csv():
    import os

    os.environ["API_KEY"] = "test-key"
    client = app.test_client()
    headers = {"X-API-Key": "test-key"}

    # register and update plugin
    res = client.post("/plugins", json={"name": "mem_filter", "builtin": True, "builtin_name": "memory_inmem"}, headers=headers)
    assert res.status_code == 200

    # update
    res2 = client.put("/plugins/mem_filter", json={"capabilities": ["memory"]}, headers=headers)
    assert res2.status_code == 200

    # unregister
    res3 = client.delete("/plugins/mem_filter", headers=headers)
    assert res3.status_code == 200

    # list audit filtered by name
    res4 = client.get("/plugins/audit?name=mem_filter", headers=headers)
    assert res4.status_code == 200
    j = res4.get_json()
    assert all(e.get("name") == "mem_filter" for e in j)

    # filter by action
    res5 = client.get("/plugins/audit?action=register", headers=headers)
    assert res5.status_code == 200
    j2 = res5.get_json()
    assert any(e.get("action") == "register" for e in j2)

    # CSV download
    res6 = client.get("/plugins/audit.csv?name=mem_filter", headers=headers)
    assert res6.status_code == 200
    assert res6.mimetype == "text/csv"
    assert "mem_filter" in res6.get_data(as_text=True)

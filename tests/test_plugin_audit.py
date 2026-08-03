from app import app


def test_plugin_audit_records():
    import os

    os.environ["API_KEY"] = "test-key"
    client = app.test_client()
    headers = {"X-API-Key": "test-key"}

    # register a plugin
    res = client.post("/plugins", json={"name": "mem_audit", "builtin": True, "builtin_name": "memory_inmem"}, headers=headers)
    assert res.status_code == 200

    # list audit
    res2 = client.get("/plugins/audit", headers=headers)
    assert res2.status_code == 200
    j = res2.get_json()
    assert isinstance(j, list)
    # find a register entry for mem_audit
    assert any(e.get("name") == "mem_audit" and e.get("action") == "register" for e in j)

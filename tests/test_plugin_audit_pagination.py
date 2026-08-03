from app import app
import os


def test_plugin_audit_pagination():
    os.environ["API_KEY"] = "test-key"
    client = app.test_client()
    headers = {"X-API-Key": "test-key"}

    names = [f"audit_pag_{i}" for i in range(5)]
    for n in names:
        res = client.post("/plugins", json={"name": n, "builtin": True, "builtin_name": "memory_inmem"}, headers=headers)
        assert res.status_code == 200

    # page 1 per_page=2
    res1 = client.get("/plugins/audit?page=1&per_page=2", headers=headers)
    assert res1.status_code == 200
    j1 = res1.get_json()
    assert isinstance(j1, dict) and len(j1.get("items", [])) == 2
    assert j1.get("page") == 1 and j1.get("per_page") == 2

    # page 2
    res2 = client.get("/plugins/audit?page=2&per_page=2", headers=headers)
    assert res2.status_code == 200
    j2 = res2.get_json()
    assert isinstance(j2, dict) and len(j2.get("items", [])) == 2
    assert j2.get("page") == 2

    # page 3
    res3 = client.get("/plugins/audit?page=3&per_page=2", headers=headers)
    assert res3.status_code == 200
    j3 = res3.get_json()
    assert isinstance(j3, dict) and len(j3.get("items", [])) >= 1

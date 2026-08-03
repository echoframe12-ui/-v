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
    assert len(j1) == 2

    # page 2
    res2 = client.get("/plugins/audit?page=2&per_page=2", headers=headers)
    assert res2.status_code == 200
    j2 = res2.get_json()
    assert len(j2) == 2

    # page 3
    res3 = client.get("/plugins/audit?page=3&per_page=2", headers=headers)
    assert res3.status_code == 200
    j3 = res3.get_json()
    assert len(j3) >= 1

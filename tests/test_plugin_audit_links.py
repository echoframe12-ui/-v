from app import app
import os


def test_plugin_audit_link_header():
    os.environ["API_KEY"] = "test-key"
    client = app.test_client()
    headers = {"X-API-Key": "test-key"}

    # create multiple entries
    for i in range(5):
        name = f"audit_link_{i}"
        res = client.post("/plugins", json={"name": name, "builtin": True, "builtin_name": "memory_inmem"}, headers=headers)
        assert res.status_code == 200

    res = client.get("/plugins/audit?page=1&per_page=2", headers=headers)
    assert res.status_code == 200
    assert "Link" in res.headers
    link = res.headers.get("Link")
    assert 'rel="next"' in link or 'rel=\"next\"' in link

    # page 2 should have both next or prev accordingly
    res2 = client.get("/plugins/audit?page=2&per_page=2", headers=headers)
    assert res2.status_code == 200
    assert "Link" in res2.headers

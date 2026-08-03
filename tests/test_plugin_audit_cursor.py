from app import app
import os


def test_plugin_audit_cursor_pagination():
    os.environ["API_KEY"] = "test-key"
    client = app.test_client()
    headers = {"X-API-Key": "test-key"}

    # create several audit entries
    ids = []
    for i in range(6):
        name = f"audit_cursor_{i}"
        res = client.post("/plugins", json={"name": name, "builtin": True, "builtin_name": "memory_inmem"}, headers=headers)
        assert res.status_code == 200
        # fetch latest audit to get id
    # First page: no cursor, per_page=2
    res1 = client.get("/plugins/audit?per_page=2", headers=headers)
    assert res1.status_code == 200
    data1 = res1.get_json()
    assert isinstance(data1, list) and len(data1) == 2
    # determine next cursor as last item's id
    next_cursor = data1[-1]["id"]

    # Next page using cursor
    res2 = client.get(f"/plugins/audit?cursor={next_cursor}&per_page=2", headers=headers)
    assert res2.status_code == 200
    data2 = res2.get_json()
    assert isinstance(data2, list) and len(data2) == 2
    assert data2[0]["id"] < next_cursor


def test_plugin_audit_cursor_returns_next_link():
    os.environ["API_KEY"] = "test-key"
    client = app.test_client()
    headers = {"X-API-Key": "test-key"}

    names = [f"audit_next_link_{i}" for i in range(5)]
    for n in names:
        res = client.post("/plugins", json={"name": n, "builtin": True, "builtin_name": "memory_inmem"}, headers=headers)
        assert res.status_code == 200

    res = client.get("/plugins/audit?per_page=2", headers=headers)
    assert res.status_code == 200
    assert "Link" in res.headers
    link = res.headers.get("Link")
    assert 'rel="next"' in link
    assert "cursor=" in link

    first_ids = [item["id"] for item in res.get_json()]
    next_cursor = int(link.split("cursor=")[1].split("&")[0])
    assert next_cursor == first_ids[-1]

    res2 = client.get(f"/plugins/audit?cursor={next_cursor}&per_page=2", headers=headers)
    assert res2.status_code == 200
    data2 = res2.get_json()
    assert len(data2) == 2
    assert data2[0]["id"] < first_ids[-1]


def test_plugin_audit_invalid_cursor_returns_400():
    os.environ["API_KEY"] = "test-key"
    client = app.test_client()
    headers = {"X-API-Key": "test-key"}

    res = client.get("/plugins/audit?cursor=not-an-int&per_page=2", headers=headers)
    assert res.status_code == 400
    assert res.get_json().get("error") == "invalid cursor"


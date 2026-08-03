from app import app


def test_plugin_lifecycle_http():
    import os

    os.environ["API_KEY"] = "test-key"
    client = app.test_client()
    headers = {"X-API-Key": "test-key"}

    # register builtin memory plugin under 'mem_life'
    res = client.post("/plugins", json={"name": "mem_life", "builtin": True, "builtin_name": "memory_inmem"}, headers=headers)
    assert res.status_code == 200

    # delete it
    res2 = client.delete("/plugins/mem_life", headers=headers)
    assert res2.status_code == 200
    j = res2.get_json()
    assert j.get("unregistered") is True

    # invoking after delete should return 404
    res3 = client.post("/tools/mem_life", json={"action": "query", "term": "x"}, headers=headers)
    assert res3.status_code == 404

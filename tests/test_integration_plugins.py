from app import app


def test_http_register_and_invoke_builtin_memory_plugin():
    client = app.test_client()

    # register builtin memory plugin under name 'mem_http'
    res = client.post("/plugins", json={"name": "mem_http", "builtin": True, "builtin_name": "memory_inmem"})
    assert res.status_code == 200
    j = res.get_json()
    assert j.get("registered") is True

    # store via HTTP tools invoke
    res2 = client.post("/tools/mem_http", json={"action": "store", "entry": {"text": "integration test", "source": "http"}})
    assert res2.status_code == 200
    rj = res2.get_json()
    assert rj.get("result") and rj["result"]["id"] == 1

    # query via HTTP
    res3 = client.post("/tools/mem_http", json={"action": "query", "term": "integration"})
    assert res3.status_code == 200
    qj = res3.get_json()
    assert len(qj.get("result", [])) >= 1

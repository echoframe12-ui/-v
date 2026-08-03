from server import OceanicOSService


def test_register_and_invoke_builtin_memory_plugin(tmp_path):
    db = tmp_path / "test.db"
    svc = OceanicOSService(db_path=str(db))
    # register a builtin memory plugin under name 'mem'
    res = svc.register_plugin("mem", {"builtin": True, "builtin_name": "memory_inmem"})
    assert res.get("registered") is True

    # invoke the plugin via tools API
    out = svc.invoke_tool("mem", {"action": "store", "entry": {"text": "hi", "source": "test"}})
    assert out["result"]["id"] == 1

    q = svc.invoke_tool("mem", {"action": "query", "term": "hi"})
    assert len(q["result"]) == 1

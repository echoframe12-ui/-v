from app import app


def test_invoke_with_schema_validation():
    client = app.test_client()

    # register builtin memory plugin with a schema requiring entry.text
    schema = {
        "type": "object",
        "properties": {
            "action": {"type": "string"},
            "entry": {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]},
        },
        "required": ["action"],
        "if": {"properties": {"action": {"const": "store"}}},
        "then": {"required": ["entry"]},
    }

    res = client.post("/plugins", json={"name": "mem_schema", "builtin": True, "builtin_name": "memory_inmem", "capabilities": ["memory"], "schema": schema})
    assert res.status_code == 200

    # invalid payload: missing entry
    res2 = client.post("/tools/mem_schema", json={"action": "store"})
    assert res2.status_code == 400

    # valid payload
    res3 = client.post("/tools/mem_schema", json={"action": "store", "entry": {"text": "valid", "source": "t"}})
    assert res3.status_code == 200

from plugins import PluginRegistry
from memory_plugin_example import MemoryPlugin


def test_memory_plugin_store_and_query():
    registry = PluginRegistry()
    plugin = MemoryPlugin()
    registry.register_plugin(plugin)

    # store an entry
    res = plugin.invoke({"action": "store", "entry": {"text": "hello world", "source": "test"}})
    assert res["result"]["id"] == 1

    # query it
    q = plugin.invoke({"action": "query", "term": "hello"})
    assert len(q["result"]) == 1
    assert q["result"][0]["text"] == "hello world"

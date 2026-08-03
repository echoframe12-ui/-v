from plugins.samples import EchoPlugin
from plugins import PluginRegistry


def test_echo_plugin_register_and_invoke():
    registry = PluginRegistry()
    plugin = EchoPlugin(name="echo", capabilities=["tool"]) 
    registry.register_plugin(plugin)
    entry = registry.find("echo")
    assert entry is not None
    inst = entry["instance"]
    assert inst.invoke("hello") == {"echo": "hello"}

from __future__ import annotations

from typing import Any

from plugins import PluginBase, PluginRegistry


class EchoPlugin(PluginBase):
    """A minimal example plugin that echoes the payload back."""

    def invoke(self, payload: Any) -> dict[str, Any]:
        return {"echo": payload}


def example_usage() -> None:
    registry = PluginRegistry()
    plugin = EchoPlugin(name="echo", capabilities=["tool"])
    registry.register_plugin(plugin)
    found = registry.find("echo")
    assert found is not None
    instance = found["instance"]
    print(instance.invoke("hello"))


if __name__ == "__main__":
    example_usage()

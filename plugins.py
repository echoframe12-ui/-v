from __future__ import annotations

from typing import Any, Callable, List, Optional
from dataclasses import dataclass, field


@dataclass
class PluginBase:
    name: str
    version: str = "0.0.1"
    description: str = ""
    capabilities: List[str] = field(default_factory=list)
    schema: Optional[dict] = None

    def invoke(self, payload: Any) -> Any:
        raise NotImplementedError("Plugin must implement invoke()")


class PluginRegistry:
    def __init__(self) -> None:
        self._plugins: list[dict[str, Any]] = []

    def register(self, name: str, capabilities: list[str]) -> dict[str, Any]:
        """Backward-compatible registration by name and capabilities."""
        plugin = {"name": name, "capabilities": capabilities}
        self._plugins.append(plugin)
        return plugin

    def register_plugin(self, plugin: PluginBase) -> PluginBase:
        """Register a `PluginBase` instance for richer plugin contracts."""
        entry = {
            "name": plugin.name,
            "version": plugin.version,
            "description": plugin.description,
            "capabilities": list(plugin.capabilities),
            "schema": plugin.schema,
            "instance": plugin,
        }
        self._plugins.append(entry)
        return plugin

    def list(self) -> list[dict[str, Any]]:
        return list(self._plugins)

    def find(self, name: str) -> Optional[dict[str, Any]]:
        for p in self._plugins:
            if p.get("name") == name:
                return p
        return None

from __future__ import annotations

import time
from typing import Any, Dict, List

from plugins import PluginBase


class MemoryPlugin(PluginBase):
    """Top-level in-memory memory plugin example (avoids package import conflicts)."""

    def __init__(self, name: str = "memory-inmem", version: str = "0.0.1", description: str = "In-memory memory plugin", capabilities: list[str] | None = None, schema: dict | None = None) -> None:
        capabilities = capabilities or ["memory"]
        super().__init__(name=name, version=version, description=description, capabilities=capabilities, schema=schema)
        self._store: List[Dict[str, Any]] = []
        self._next_id = 1

    def invoke(self, payload: Any) -> Dict[str, Any]:
        action = payload.get("action")
        if action == "store":
            entry = payload.get("entry")
            if not isinstance(entry, dict) or "text" not in entry:
                raise ValueError("entry must be a dict with a 'text' field")
            record = {
                "id": self._next_id,
                "text": entry.get("text"),
                "source": entry.get("source"),
                "timestamp": time.time(),
            }
            self._next_id += 1
            self._store.append(record)
            return {"result": record}

        if action == "query":
            term = (payload.get("term") or "").lower()
            matches = [e for e in self._store if term in (e.get("text") or "").lower()]
            return {"result": matches}

        raise ValueError("unknown action")

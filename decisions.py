from __future__ import annotations

from typing import Any


class DecisionRegistry:
    def __init__(self) -> None:
        self._decisions: list[dict[str, Any]] = []

    def record(self, title: str, context: str, decision: str) -> dict[str, Any]:
        entry = {"title": title, "context": context, "decision": decision}
        self._decisions.append(entry)
        return entry

    def update(self, title: str, decision: str) -> dict[str, Any] | None:
        for entry in self._decisions:
            if entry["title"] == title:
                entry["decision"] = decision
                return entry
        return None

    def list(self) -> list[dict[str, Any]]:
        return list(self._decisions)

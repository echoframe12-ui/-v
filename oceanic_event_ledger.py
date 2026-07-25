from __future__ import annotations

"""Append-only local event ledger for Ω∞ Oceanic.

The ledger records lifecycle evidence without rewriting historical events.
It is intentionally dependency-free and can be persisted as JSON Lines.
"""

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class LedgerEvent:
    sequence: int
    event_type: str
    entity_id: str
    timestamp: str
    payload: dict[str, Any]
    previous_digest: str | None
    event_digest: str


class EventLedger:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _events(self) -> list[LedgerEvent]:
        if not self.path.exists():
            return []
        events = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                events.append(LedgerEvent(**json.loads(line)))
        return events

    def append(self, event_type: str, entity_id: str, payload: dict[str, Any]) -> LedgerEvent:
        events = self._events()
        previous_digest = events[-1].event_digest if events else None
        sequence = len(events) + 1
        timestamp = datetime.now(timezone.utc).isoformat()
        canonical = json.dumps(
            {
                "sequence": sequence,
                "event_type": event_type,
                "entity_id": entity_id,
                "timestamp": timestamp,
                "payload": payload,
                "previous_digest": previous_digest,
            },
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        )
        event_digest = "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        event = LedgerEvent(
            sequence=sequence,
            event_type=event_type,
            entity_id=entity_id,
            timestamp=timestamp,
            payload=payload,
            previous_digest=previous_digest,
            event_digest=event_digest,
        )
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(asdict(event), sort_keys=True, default=str) + "\n")
        return event

    def verify_chain(self) -> bool:
        events = self._events()
        previous_digest = None
        for index, event in enumerate(events, start=1):
            if event.sequence != index or event.previous_digest != previous_digest:
                return False
            canonical = json.dumps(
                {
                    "sequence": event.sequence,
                    "event_type": event.event_type,
                    "entity_id": event.entity_id,
                    "timestamp": event.timestamp,
                    "payload": event.payload,
                    "previous_digest": event.previous_digest,
                },
                sort_keys=True,
                separators=(",", ":"),
                default=str,
            )
            expected = "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()
            if event.event_digest != expected:
                return False
            previous_digest = event.event_digest
        return True

    def history(self) -> tuple[LedgerEvent, ...]:
        return tuple(self._events())

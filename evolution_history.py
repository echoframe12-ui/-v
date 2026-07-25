"""A persistent trajectory of the platform's compounding footprint.

`evolution.compounding` reports how many records the append-only ledgers hold *now*;
this remembers that total *over time*, so "the histories compound" becomes a curve
you can watch rather than a claim you take on faith. It records the total at the
moments it can grow — a build, a held-review decision — and only when it actually
changes, so the series is real movement, not a log of identical reads.

This ledger watches the compounding; it is not itself part of what compounds. It is
deliberately kept out of `_ledger_counts`, so recording a growth point never changes
the total it measures — the observer that does not interrupt what it observes.
"""
from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class EvolutionHistory:
    """Change-only history of the compounding footprint's `records_total`."""

    def __init__(self, db_path: str | None = None) -> None:
        self._db_path = Path(db_path or os.getenv("OCEANICOS_DB", "oceanicos.db"))
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS evolution_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    records_total INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )

    def record(self, records_total: int) -> dict[str, Any]:
        created_at = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.execute(
                "INSERT INTO evolution_snapshots (records_total, created_at) VALUES (?, ?)",
                (int(records_total), created_at),
            )
        return {"id": cursor.lastrowid, "records_total": int(records_total), "created_at": created_at}

    def record_if_changed(self, records_total: int) -> dict[str, Any] | None:
        """Record only when the total differs from the latest point.

        Keeps the series a trajectory of real growth — reading the footprint a
        hundred times without anything new adds no rows — so the curve reflects when
        the record actually compounded, not how often it was observed.
        """
        series = self.list(limit=1)
        if series and series[-1]["records_total"] == int(records_total):
            return None
        return self.record(records_total)

    def list(self, limit: int | None = None) -> list[dict[str, Any]]:
        query = "SELECT id, records_total, created_at FROM evolution_snapshots ORDER BY id DESC"
        params: list[Any] = []
        if limit is not None:
            query += " LIMIT ?"
            params.append(int(limit))
        with sqlite3.connect(self._db_path) as conn:
            rows = conn.execute(query, tuple(params)).fetchall()
        # fetched newest-first for the LIMIT; return oldest-first for a time series
        return [
            {"id": row[0], "records_total": row[1], "created_at": row[2]}
            for row in reversed(rows)
        ]

    def growth(self) -> dict[str, Any]:
        """The trajectory in one glance — first total, latest total, and the gain.

        `gain` is how much the record has compounded across the series; `points` is
        how many times it moved. Empty (all zero/None) until the first snapshot.
        """
        series = self.list()
        if not series:
            return {"points": 0, "first": None, "latest": None, "gain": 0}
        first = series[0]["records_total"]
        latest = series[-1]["records_total"]
        return {
            "points": len(series),
            "first": first,
            "latest": latest,
            "gain": latest - first,
            "since": series[0]["created_at"],
        }

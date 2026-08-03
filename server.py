from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any
from importlib import import_module

from plugins import PluginRegistry


class OceanicOSService:
    def __init__(self, db_path: str | None = None) -> None:
        self._db_path = Path(db_path or "oceanicos.db")
        self._memory: list[dict[str, Any]] = []
        self._tools = {
            "echo": self._echo_tool,
        }
        self._plugins: list[dict[str, Any]] = []
        self._plugin_registry = PluginRegistry()
        # built-in plugin factories (module path, class name)
        self._builtin_plugins: dict[str, tuple[str, str]] = {
            "echo_plugin": ("plugins_example", "EchoPlugin"),
            "memory_inmem": ("memory_plugin_example", "MemoryPlugin"),
        }
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS memory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    payload TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS plugins (
                    name TEXT PRIMARY KEY,
                    config TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS plugin_audit (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    action TEXT NOT NULL,
                    actor TEXT,
                    details TEXT,
                    ts DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

    def record_plugin_audit(self, name: str, action: str, actor: str | None = None, details: dict | None = None) -> None:
        """Record a plugin lifecycle action for audit and debugging."""
        details_text = json.dumps(details) if details is not None else None
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                "INSERT INTO plugin_audit (name, action, actor, details) VALUES (?, ?, ?, ?)",
                (name, action, actor, details_text),
            )

    def list_plugin_audit(
        self,
        limit: int = 100,
        name: str | None = None,
        action: str | None = None,
        start_ts: str | None = None,
        end_ts: str | None = None,
        page: int | None = None,
        per_page: int | None = None,
        cursor: int | None = None,
    ) -> list[dict[str, Any]]:
        """List plugin audit entries with optional filtering by name, action, and time range.

        Supports simple page/per_page pagination. Returns entries ordered by id desc.
        """
        base_sql = "SELECT id, name, action, actor, details, ts FROM plugin_audit"
        params: list[Any] = []
        clauses: list[str] = []
        if name:
            clauses.append("name = ?")
            params.append(name)
        if action:
            clauses.append("action = ?")
            params.append(action)
        if start_ts:
            clauses.append("ts >= ?")
            params.append(start_ts)
        if end_ts:
            clauses.append("ts <= ?")
            params.append(end_ts)

        # If caller provided per_page without page and no cursor, treat per_page as the limit
        if page is None and per_page is not None and cursor is None:
            limit = per_page

        # Support cursor-based pagination when `cursor` is provided: return items with id < cursor
        if cursor is not None:
            clauses.append("id < ?")
            params.append(cursor)
            per = per_page or limit

        # assemble final SQL with WHERE (including cursor if added)
        if clauses:
            sql = base_sql + " WHERE " + " AND ".join(clauses)
        else:
            sql = base_sql

        # apply ordering and limits
        if cursor is not None:
            sql += " ORDER BY id DESC LIMIT ?"
            params.append(per)
        elif page is not None and per_page is not None:
            offset = max(0, (page - 1)) * per_page
            sql += " ORDER BY id DESC LIMIT ? OFFSET ?"
            params.append(per_page)
            params.append(offset)
        else:
            sql += " ORDER BY id DESC LIMIT ?"
            params.append(limit)

        with sqlite3.connect(self._db_path) as conn:
            rows = conn.execute(sql, tuple(params)).fetchall()
        return [
            {"id": row[0], "name": row[1], "action": row[2], "actor": row[3], "details": json.loads(row[4]) if row[4] else None, "ts": row[5]}
            for row in rows
        ]

    def count_plugin_audit(self, name: str | None = None, action: str | None = None, start_ts: str | None = None, end_ts: str | None = None) -> int:
        sql = "SELECT COUNT(*) FROM plugin_audit"
        params: list[Any] = []
        clauses: list[str] = []
        if name:
            clauses.append("name = ?")
            params.append(name)
        if action:
            clauses.append("action = ?")
            params.append(action)
        if start_ts:
            clauses.append("ts >= ?")
            params.append(start_ts)
        if end_ts:
            clauses.append("ts <= ?")
            params.append(end_ts)
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        with sqlite3.connect(self._db_path) as conn:
            row = conn.execute(sql, tuple(params)).fetchone()
        return int(row[0]) if row else 0

    def health(self) -> dict[str, Any]:
        return {"status": "ok", "service": "OceanicOS"}

    def create_plan(self, task: str) -> dict[str, Any]:
        return {
            "task": task,
            "steps": [
                "Clarify the goal",
                "Gather relevant context",
                "Execute the work",
                "Record the outcome",
            ],
        }

    def store_memory(self, entry: dict[str, Any]) -> dict[str, Any]:
        payload = json.dumps(entry)
        with sqlite3.connect(self._db_path) as conn:
            conn.execute("INSERT INTO memory (payload) VALUES (?)", (payload,))
        self._memory.append(entry)
        return {"stored": True, "count": len(self._memory)}

    def search_memory(self, query: str) -> list[dict[str, Any]]:
        q = query.lower()
        with sqlite3.connect(self._db_path) as conn:
            rows = conn.execute("SELECT payload FROM memory").fetchall()
        entries = [json.loads(row[0]) for row in rows]
        self._memory = entries
        return [entry for entry in entries if q in str(entry.get("text", "")).lower()]

    def list_tools(self) -> list[dict[str, Any]]:
        return [{"name": name} for name in sorted(self._tools)]

    def invoke_tool(self, name: str, payload: dict[str, Any]) -> dict[str, Any]:
        if name not in self._tools:
            raise KeyError(f"Unknown tool: {name}")
        return self._tools[name](payload)

    def register_plugin(self, name: str, config: dict[str, Any]) -> dict[str, Any]:
        # If config requests a builtin plugin, try to instantiate and register it.
        if config.get("builtin"):
            builtin = config.get("builtin_name") or name
            if builtin in self._builtin_plugins:
                mod_path, cls_name = self._builtin_plugins[builtin]
                try:
                    mod = import_module(mod_path)
                    cls = getattr(mod, cls_name)
                    instance = cls(name=name)
                    # register instance as a callable tool
                    self._plugin_registry.register_plugin(instance)
                    self._tools[name] = lambda payload, inst=instance: inst.invoke(payload)
                except Exception as exc:  # pragma: no cover - defensive
                    return {"registered": False, "error": str(exc)}

        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO plugins (name, config) VALUES (?, ?)",
                (name, json.dumps(config)),
            )
        self._plugins.append({"name": name, "config": config})
        # audit record
        try:
            self.record_plugin_audit(name, "register", None, config)
        except Exception:
            pass
        return {"registered": True, "name": name}

    def unregister_plugin(self, name: str) -> dict[str, Any]:
        """Remove plugin from DB, internal registry, and any exposed tools."""
        with sqlite3.connect(self._db_path) as conn:
            conn.execute("DELETE FROM plugins WHERE name = ?", (name,))
        # remove from in-memory lists
        self._plugins = [p for p in self._plugins if p.get("name") != name]
        # remove tool mapping if present
        if name in self._tools:
            del self._tools[name]
        # remove from plugin registry if present
        found = self._plugin_registry.find(name)
        if found:
            # unregister by filtering
            self._plugin_registry._plugins = [p for p in self._plugin_registry._plugins if p.get("name") != name]
        # audit record
        try:
            self.record_plugin_audit(name, "unregister", None, None)
        except Exception:
            pass
        return {"unregistered": True, "name": name}

    def update_plugin(self, name: str, config: dict[str, Any]) -> dict[str, Any]:
        """Update plugin config in DB and re-instantiate builtin if requested."""
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO plugins (name, config) VALUES (?, ?)",
                (name, json.dumps(config)),
            )
        # update in-memory copy
        for p in self._plugins:
            if p.get("name") == name:
                p["config"] = config
                break
        else:
            self._plugins.append({"name": name, "config": config})

        # if replacing a builtin, (re)instantiate and attach
        if config.get("builtin"):
            builtin = config.get("builtin_name") or name
            if builtin in self._builtin_plugins:
                mod_path, cls_name = self._builtin_plugins[builtin]
                try:
                    mod = import_module(mod_path)
                    cls = getattr(mod, cls_name)
                    instance = cls(name=name)
                    # replace in registry and tools
                    self._plugin_registry.register_plugin(instance)
                    self._tools[name] = lambda payload, inst=instance: inst.invoke(payload)
                except Exception as exc:  # pragma: no cover - defensive
                    return {"updated": False, "error": str(exc)}

        # audit record
        try:
            self.record_plugin_audit(name, "update", None, config)
        except Exception:
            pass

        return {"updated": True, "name": name}

    def list_plugins(self) -> list[dict[str, Any]]:
        with sqlite3.connect(self._db_path) as conn:
            rows = conn.execute("SELECT name, config FROM plugins").fetchall()
        self._plugins = [{"name": row[0], "config": json.loads(row[1])} for row in rows]
        return self._plugins

    def get_plugin_config(self, name: str) -> dict[str, Any] | None:
        """Return stored plugin config from the DB by name, or None if missing."""
        with sqlite3.connect(self._db_path) as conn:
            row = conn.execute("SELECT config FROM plugins WHERE name = ?", (name,)).fetchone()
        if not row:
            return None
        return json.loads(row[0])

    def _echo_tool(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"output": payload.get("message", "")}

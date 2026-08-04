from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class WorkflowEngine:
    def __init__(self, db_path: str | None = None) -> None:
        self._db_path = Path(db_path or "oceanicos.db")
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS workflows (
                    name TEXT PRIMARY KEY,
                    steps TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    runs TEXT NOT NULL
                )
                """
            )

    def _load(self, name: str) -> dict[str, Any]:
        with sqlite3.connect(self._db_path) as conn:
            row = conn.execute(
                "SELECT name, steps, status, created_at, runs FROM workflows WHERE name = ?",
                (name,),
            ).fetchone()
        if not row:
            raise KeyError(f"Unknown workflow: {name}")
        return {
            "name": row[0],
            "steps": json.loads(row[1]),
            "status": row[2],
            "created_at": row[3],
            "runs": json.loads(row[4]),
        }

    def _save(self, wf: dict[str, Any]) -> None:
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO workflows (name, steps, status, created_at, runs)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    wf["name"],
                    json.dumps(wf["steps"]),
                    wf["status"],
                    wf["created_at"],
                    json.dumps(wf["runs"]),
                ),
            )

    def create_workflow(self, name: str, steps: list[dict[str, Any]]) -> dict[str, Any]:
        workflow = {
            "name": name,
            "steps": steps,
            "status": "created",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "runs": [],
        }
        self._save(workflow)
        return {"created": True, "name": name, "steps": len(steps)}

    def get_workflow(self, name: str) -> dict[str, Any]:
        wf = self._load(name)
        return {"name": name, "steps": wf["steps"], "status": wf["status"], "runs": len(wf["runs"])}

    def list_workflows(self) -> list[dict[str, Any]]:
        with sqlite3.connect(self._db_path) as conn:
            rows = conn.execute(
                "SELECT name, steps, status, runs FROM workflows ORDER BY created_at DESC"
            ).fetchall()
        return [
            {
                "name": row[0],
                "steps": len(json.loads(row[1])),
                "status": row[2],
                "runs": len(json.loads(row[3])),
            }
            for row in rows
        ]

    def execute_workflow(
        self,
        name: str,
        tool_runner: Any | None = None,
    ) -> dict[str, Any]:
        wf = self._load(name)
        wf["status"] = "running"
        self._save(wf)

        started_at = datetime.now(timezone.utc).isoformat()
        step_results: list[dict[str, Any]] = []
        failed = False

        for i, step in enumerate(wf["steps"]):
            step_name = step.get("name", f"step-{i}")
            step_type = step.get("type", "unknown")
            result: dict[str, Any] = {
                "step": step_name,
                "type": step_type,
                "index": i,
            }
            if step_type == "mood_gate":
                from full_stack_e2e_gate import check as check_contract_stack
                from mood import MoodSignal, assess

                gate = check_contract_stack()
                contract_ok = bool(gate.get("ok"))
                edge_ok = bool(gate.get("edge_rejects_empty_attestation"))
                signals = [
                    MoodSignal("contract_stack_healthy", contract_ok, "full-stack-e2e-gate"),
                    MoodSignal("edge_attestation_enforced", edge_ok, "full-stack-e2e-gate"),
                ]
                assessment = assess(signals)
                result["output"] = {
                    "mood": assessment.status,
                    "route": assessment.route,
                    "gaps": list(assessment.gaps),
                }
                if assessment.status == "clear":
                    result["status"] = "completed"
                else:
                    result["status"] = "failed"
                    result["error"] = f"MOOD dissent: {', '.join(assessment.gaps)}"
                    failed = True
            elif step_type == "tool" and tool_runner is not None:
                try:
                    output = tool_runner(step_name, step.get("params", {}))
                    result["status"] = "completed"
                    result["output"] = output
                except Exception as exc:
                    result["status"] = "failed"
                    result["error"] = str(exc)
                    failed = True
            else:
                result["status"] = "completed"
                result["output"] = None

            step_results.append(result)
            if failed:
                break

        overall = "failed" if failed else "completed"
        wf["status"] = overall
        completed_at = datetime.now(timezone.utc).isoformat()
        run_record = {
            "started_at": started_at,
            "completed_at": completed_at,
            "status": overall,
            "steps_completed": sum(1 for s in step_results if s["status"] == "completed"),
            "steps_total": len(wf["steps"]),
        }
        wf["runs"].append(run_record)
        self._save(wf)

        return {
            "executed": overall == "completed",
            "name": name,
            "status": overall,
            "steps": step_results,
            "run": run_record,
        }

    def reset_workflow(self, name: str) -> dict[str, Any]:
        wf = self._load(name)
        wf["status"] = "created"
        self._save(wf)
        return {"name": name, "status": "created"}

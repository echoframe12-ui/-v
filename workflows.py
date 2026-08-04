from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


class WorkflowEngine:
    def __init__(self) -> None:
        self._workflows: dict[str, dict[str, Any]] = {}

    def create_workflow(self, name: str, steps: list[dict[str, Any]]) -> dict[str, Any]:
        workflow = {
            "name": name,
            "steps": steps,
            "status": "created",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "runs": [],
        }
        self._workflows[name] = workflow
        return {"created": True, "name": name, "steps": len(steps)}

    def get_workflow(self, name: str) -> dict[str, Any]:
        if name not in self._workflows:
            raise KeyError(f"Unknown workflow: {name}")
        wf = self._workflows[name]
        return {"name": name, "steps": wf["steps"], "status": wf["status"], "runs": len(wf["runs"])}

    def list_workflows(self) -> list[dict[str, Any]]:
        return [
            {"name": wf["name"], "steps": len(wf["steps"]), "status": wf["status"], "runs": len(wf["runs"])}
            for wf in self._workflows.values()
        ]

    def execute_workflow(
        self,
        name: str,
        tool_runner: Any | None = None,
    ) -> dict[str, Any]:
        """Execute a workflow step by step.

        If a `tool_runner` callable is provided, each step of type ``"tool"``
        is dispatched through it as ``tool_runner(step_name, {})``.  Steps of
        other types are recorded as completed without side-effects.

        Returns the execution report with per-step results and overall status.
        """
        if name not in self._workflows:
            raise KeyError(f"Unknown workflow: {name}")
        wf = self._workflows[name]
        wf["status"] = "running"
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
            if step_type == "tool" and tool_runner is not None:
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

        return {
            "executed": overall == "completed",
            "name": name,
            "status": overall,
            "steps": step_results,
            "run": run_record,
        }

    def reset_workflow(self, name: str) -> dict[str, Any]:
        """Reset a workflow's status back to created so it can be re-executed."""
        if name not in self._workflows:
            raise KeyError(f"Unknown workflow: {name}")
        wf = self._workflows[name]
        wf["status"] = "created"
        return {"name": name, "status": "created"}

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from full_stack_e2e_gate import check as check_contract_stack
from mood import MoodSignal, assess
from server import OceanicOSService
from universal_builder import UniversalBuilder
from workflows import WorkflowEngine


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="oceanicos",
        description="OceanicOS CLI Execution Interface",
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # health
    subparsers.add_parser("health", help="Check OceanicOS service health")

    # plan
    plan_parser = subparsers.add_parser("plan", help="Create an execution plan")
    plan_parser.add_argument("task", type=str, help="Task description")

    # run (UniversalBuilder)
    run_parser = subparsers.add_parser("run", help="Run UniversalBuilder on a task")
    run_parser.add_argument("task", type=str, help="Task description")
    run_parser.add_argument("--context", "-c", type=str, default=None, help="Context string")

    # tool
    tool_parser = subparsers.add_parser("tool", help="Invoke a registered tool")
    tool_parser.add_argument("name", type=str, help="Tool name (e.g. echo)")
    tool_parser.add_argument("payload", type=str, nargs="?", default="{}", help="JSON payload string")

    # workflow
    wf_parser = subparsers.add_parser("workflow", help="Manage and execute workflows")
    wf_sub = wf_parser.add_subparsers(dest="wf_action", help="Workflow action")

    wf_create = wf_sub.add_parser("create", help="Create a workflow")
    wf_create.add_argument("name", type=str, help="Workflow name")
    wf_create.add_argument("steps", type=str, help="JSON steps array string (e.g. '[{\"name\":\"echo\",\"type\":\"tool\"}]')")

    wf_exec = wf_sub.add_parser("run", help="Execute a workflow")
    wf_exec.add_argument("name", type=str, help="Workflow name")

    wf_list = wf_sub.add_parser("list", help="List all workflows")

    # verify (MOOD gate)
    subparsers.add_parser("verify", help="Run full-stack MOOD verification gate")

    # gate (contract stack only)
    subparsers.add_parser("gate", help="Run Ω∞v contract stack check")

    # plugins
    subparsers.add_parser("plugins", help="List registered plugins")

    return parser


def main(args: list[str] | None = None) -> int:
    parser = build_parser()
    parsed = parser.parse_args(args)

    if not parsed.command:
        parser.print_help()
        return 0

    service = OceanicOSService()

    if parsed.command == "health":
        print(json.dumps(service.health(), indent=2))

    elif parsed.command == "plan":
        result = service.create_plan(parsed.task)
        print(json.dumps(result, indent=2))

    elif parsed.command == "run":
        builder = UniversalBuilder()
        result = builder.run(parsed.task, parsed.context)
        print(json.dumps(result, indent=2))

    elif parsed.command == "tool":
        try:
            payload = json.loads(parsed.payload)
        except json.JSONDecodeError as exc:
            print(f"Error: Invalid JSON payload: {exc}", file=sys.stderr)
            return 1
        try:
            result = service.invoke_tool(parsed.name, payload)
            print(json.dumps(result, indent=2))
        except KeyError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1

    elif parsed.command == "workflow":
        wf_engine = WorkflowEngine()
        if parsed.wf_action == "create":
            try:
                steps = json.loads(parsed.steps)
            except json.JSONDecodeError as exc:
                print(f"Error: Invalid JSON steps: {exc}", file=sys.stderr)
                return 1
            result = wf_engine.create_workflow(parsed.name, steps)
            print(json.dumps(result, indent=2))

        elif parsed.wf_action == "run":
            def tool_runner(name: str, params: dict[str, Any]) -> Any:
                return service.invoke_tool(name, params)

            try:
                result = wf_engine.execute_workflow(parsed.name, tool_runner=tool_runner)
                print(json.dumps(result, indent=2))
            except KeyError as exc:
                print(f"Error: {exc}", file=sys.stderr)
                return 1

        elif parsed.wf_action == "list":
            print(json.dumps(wf_engine.list_workflows(), indent=2))

        else:
            wf_parser = parser._subparsers._group_actions[0]._name_parser_map["workflow"]
            wf_parser.print_help()

    elif parsed.command == "verify":
        gate_result = check_contract_stack()
        contract_ok = bool(gate_result.get("ok"))
        edge_ok = bool(gate_result.get("edge_rejects_empty_attestation"))
        signals = [
            MoodSignal("contract_stack_healthy", contract_ok, "full-stack-e2e-gate"),
            MoodSignal("edge_attestation_enforced", edge_ok, "full-stack-e2e-gate"),
        ]
        assessment = assess(signals)
        output = {
            "mood": assessment.status,
            "route": assessment.route,
            "gaps": list(assessment.gaps),
            "contract_stack": gate_result,
        }
        print(json.dumps(output, indent=2))
        return 0 if assessment.status == "clear" else 1

    elif parsed.command == "gate":
        gate_result = check_contract_stack()
        print(json.dumps(gate_result, indent=2))
        return 0 if gate_result.get("ok") else 1

    elif parsed.command == "plugins":
        print(json.dumps(service.list_plugins(), indent=2))

    return 0


if __name__ == "__main__":
    sys.exit(main())

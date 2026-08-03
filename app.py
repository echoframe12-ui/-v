import os

from flask import Flask, jsonify, render_template, request
from jsonschema import validate, ValidationError

from agent import AgentLoop
from artifacts import ArtifactRegistry
from dashboard import Dashboard
from decisions import DecisionRegistry
from models import ModelAdapter, ModelRouter
from planner import Planner
from review import ReviewEngine
from server import OceanicOSService
from state import StateSnapshot
from workflows import WorkflowEngine

app = Flask(__name__)
service = OceanicOSService()
workflow_engine = WorkflowEngine()
planner = Planner()
model_router = ModelRouter()
model_router.register(ModelAdapter("local", "demo"))
agent_loop = AgentLoop()
state_snapshot = StateSnapshot()
review_engine = ReviewEngine()
decision_registry = DecisionRegistry()
artifact_registry = ArtifactRegistry()
dashboard = Dashboard()


def _require_api_key(req: request) -> tuple[bool, tuple[dict, int] | None]:
    """Return (True, None) when API key is valid; otherwise (False, (resp, status))."""
    expected = os.getenv("API_KEY", "")
    # If no API_KEY configured, allow open access (useful for local/dev)
    if not expected:
        return True, None
    # accept either X-API-Key or Authorization: Bearer <token>
    key = req.headers.get("X-API-Key", "")
    if key == expected:
        return True, None
    auth = req.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        token = auth.split(" ", 1)[1].strip()
        if token == expected:
            return True, None
    return False, (jsonify({"error": "unauthorized"}), 401)


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/health", methods=["GET"])
def health():
    return jsonify(service.health())


@app.route("/status", methods=["GET"])
def status():
    return jsonify(
        {
            "health": service.health(),
            "memory_count": len(service.search_memory("")),
            "tools": service.list_tools(),
            "plugins_count": len(service.list_plugins()),
            "artifacts_count": len(artifact_registry.list()),
            "dashboard_count": dashboard.summary()["count"],
        }
    )


@app.route("/plans", methods=["POST"])
def create_plan():
    payload = request.get_json(silent=True) or {}
    task = payload.get("task", "")
    return jsonify(service.create_plan(task))


@app.route("/memory", methods=["POST"])
def store_memory():
    payload = request.get_json(silent=True) or {}
    return jsonify(service.store_memory(payload))


@app.route("/memory", methods=["GET"])
def search_memory():
    query = request.args.get("query", "")
    return jsonify(service.search_memory(query))


@app.route("/tools", methods=["GET"])
def list_tools():
    return jsonify(service.list_tools())


@app.route("/tools/<name>", methods=["POST"])
def invoke_tool(name: str):
    payload = request.get_json(silent=True) or {}
    ok, resp = _require_api_key(request)
    if not ok:
        return resp
    # If plugin provides a schema in its stored config, validate the payload first.
    config = service.get_plugin_config(name)
    schema = None
    if config:
        schema = config.get("schema")
    if schema:
        try:
            validate(instance=payload, schema=schema)
        except ValidationError as exc:
            return (
                jsonify({"error": "invalid payload", "message": str(exc)}),
                400,
            )
    try:
        return jsonify(service.invoke_tool(name, payload))
    except ValueError as exc:
        return jsonify({"error": "invalid input", "message": str(exc)}), 400
    except KeyError as exc:
        return jsonify({"error": "not found", "message": str(exc)}), 404
    except Exception as exc:  # pragma: no cover - unexpected plugin error
        return jsonify({"error": "internal error", "message": str(exc)}), 500


@app.route("/workflows", methods=["POST"])
def create_workflow():
    payload = request.get_json(silent=True) or {}
    name = payload.get("name", "")
    steps = payload.get("steps", [])
    return jsonify(workflow_engine.create_workflow(name, steps))


@app.route("/workflows/<name>", methods=["GET"])
def get_workflow(name: str):
    return jsonify(workflow_engine.get_workflow(name))


@app.route("/workflows/<name>/execute", methods=["POST"])
def execute_workflow(name: str):
    return jsonify(workflow_engine.execute_workflow(name))


@app.route("/plans/execute", methods=["POST"])
def execute_planner():
    payload = request.get_json(silent=True) or {}
    task = payload.get("task", "")
    context = payload.get("context")
    return jsonify(planner.plan(task, context))


@app.route("/plans/trace", methods=["GET"])
def planner_trace():
    return jsonify(planner.get_trace())


@app.route("/models/route", methods=["POST"])
def route_model():
    payload = request.get_json(silent=True) or {}
    prompt = payload.get("prompt", "")
    return jsonify(model_router.route(prompt))


@app.route("/agent/run", methods=["POST"])
def run_agent():
    payload = request.get_json(silent=True) or {}
    task = payload.get("task", "")
    context = payload.get("context")
    return jsonify(agent_loop.run(task, context))


@app.route("/agent/events", methods=["GET"])
def agent_events():
    return jsonify(agent_loop.events())


@app.route("/state", methods=["POST"])
def record_state():
    payload = request.get_json(silent=True) or {}
    event = payload.get("event", "")
    detail = payload.get("detail")
    state_snapshot.record(event, detail)
    return jsonify(state_snapshot.snapshot())


@app.route("/state", methods=["GET"])
def get_state():
    return jsonify(state_snapshot.snapshot())


@app.route("/reviews", methods=["POST"])
def submit_review():
    payload = request.get_json(silent=True) or {}
    proposal = payload.get("proposal", "")
    reviewer = payload.get("reviewer", "")
    return jsonify(review_engine.submit(proposal, reviewer))


@app.route("/reviews/<proposal>/approve", methods=["POST"])
def approve_review(proposal: str):
    return jsonify(review_engine.approve(proposal))


@app.route("/reviews", methods=["GET"])
def list_reviews():
    return jsonify(review_engine.list_reviews())


@app.route("/decisions", methods=["POST"])
def record_decision():
    payload = request.get_json(silent=True) or {}
    title = payload.get("title", "")
    context = payload.get("context", "")
    decision = payload.get("decision", "")
    return jsonify(decision_registry.record(title, context, decision))


@app.route("/decisions", methods=["GET"])
def list_decisions():
    return jsonify(decision_registry.list())


@app.route("/artifacts", methods=["POST"])
def create_artifact():
    payload = request.get_json(silent=True) or {}
    name = payload.get("name", "")
    kind = payload.get("kind", "")
    status = payload.get("status", "draft")
    return jsonify(artifact_registry.create(name, kind, status))


@app.route("/artifacts", methods=["GET"])
def list_artifacts():
    return jsonify(artifact_registry.list())


@app.route("/dashboard", methods=["POST"])
def add_dashboard_item():
    payload = request.get_json(silent=True) or {}
    title = payload.get("title", "")
    kind = payload.get("kind", "")
    status = payload.get("status", "active")
    dashboard.add(title, kind, status)
    return jsonify(dashboard.summary())


@app.route("/dashboard", methods=["GET"])
def get_dashboard():
    return jsonify(dashboard.summary())


@app.route("/builder/run", methods=["POST"])
def run_builder():
    payload = request.get_json(silent=True) or {}
    task = payload.get("task", "Draft a charter update")
    context = payload.get("context", "Open orchestration")

    plan_result = planner.plan(task, context)
    model_result = model_router.route(task)
    review_result = review_engine.submit(f"Review plan for {task}", "builder")
    decision_result = decision_registry.record(
        f"Run {task}",
        context,
        f"Accepted a builder run for {task}",
    )
    artifact_result = artifact_registry.create(
        task.lower().replace(" ", "-"),
        "plan",
        "draft",
    )
    artifact_registry.update_status(artifact_result["name"], "ready")
    decision_registry.update(f"Run {task}", f"Accepted a builder run for {task} and marked artifact ready")

    return jsonify(
        {
            "task": task,
            "plan": plan_result,
            "model": model_result,
            "state": state_snapshot.snapshot(),
            "review": review_result,
            "decision": decision_result,
            "artifact": artifact_registry.list()[-1],
            "dashboard": dashboard.summary(),
        }
    )


@app.route("/builder/trace", methods=["GET"])
def builder_trace():
    return jsonify(
        {
            "state": state_snapshot.snapshot(),
            "decisions": decision_registry.list(),
            "artifacts": artifact_registry.list(),
            "dashboard": dashboard.summary(),
        }
    )


@app.route("/plugins", methods=["POST"])
def register_plugin():
    payload = request.get_json(silent=True) or {}
    name = payload.get("name", "")
    capabilities = payload.get("capabilities", [])
    builtin = payload.get("builtin", False)
    builtin_name = payload.get("builtin_name")
    config = {"capabilities": capabilities, "builtin": bool(builtin)}
    if builtin_name:
        config["builtin_name"] = builtin_name
    ok, resp = _require_api_key(request)
    if not ok:
        return resp
    return jsonify(service.register_plugin(name, config))


@app.route("/plugins/<name>", methods=["PUT"])
def update_plugin(name: str):
    payload = request.get_json(silent=True) or {}
    ok, resp = _require_api_key(request)
    if not ok:
        return resp
    # allow updating capabilities, schema, builtin flags
    capabilities = payload.get("capabilities", [])
    builtin = payload.get("builtin", False)
    builtin_name = payload.get("builtin_name")
    config = {"capabilities": capabilities, "builtin": bool(builtin)}
    if builtin_name:
        config["builtin_name"] = builtin_name
    if "schema" in payload:
        config["schema"] = payload.get("schema")
    return jsonify(service.update_plugin(name, config))


@app.route("/plugins/<name>", methods=["DELETE"])
def delete_plugin(name: str):
    ok, resp = _require_api_key(request)
    if not ok:
        return resp
    return jsonify(service.unregister_plugin(name))


@app.route("/plugins", methods=["GET"])
def list_plugins():
    return jsonify(service.list_plugins())


@app.route("/plugins/audit", methods=["GET"])
def list_plugin_audit():
    ok, resp = _require_api_key(request)
    if not ok:
        return resp
    limit = request.args.get("limit")
    try:
        l = int(limit) if limit else 100
    except Exception:
        l = 100
    name = request.args.get("name")
    action = request.args.get("action")
    return jsonify(service.list_plugin_audit(l, name=name, action=action))


@app.route("/plugins/audit.csv", methods=["GET"])
def download_plugin_audit_csv():
    ok, resp = _require_api_key(request)
    if not ok:
        return resp
    limit = request.args.get("limit")
    try:
        l = int(limit) if limit else 100
    except Exception:
        l = 100
    name = request.args.get("name")
    action = request.args.get("action")
    entries = service.list_plugin_audit(l, name=name, action=action)
    # generate CSV
    from io import StringIO
    import csv

    buf = StringIO()
    writer = csv.writer(buf)
    writer.writerow(["id", "name", "action", "actor", "details", "ts"])
    for e in entries:
        writer.writerow([e.get("id"), e.get("name"), e.get("action"), e.get("actor"), json.dumps(e.get("details")) if e.get("details") is not None else "", e.get("ts")])
    csv_text = buf.getvalue()
    return app.response_class(csv_text, mimetype="text/csv")


def main() -> None:
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "5000"))
    debug = os.getenv("FLASK_DEBUG", "1") == "1"
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    main()

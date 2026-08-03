# API and Plugin Specification

OceanicOS should expose a simple, extensible interface for orchestration, memory, and tool integration.

## Core API Endpoints

### Health
- GET /health
  - Returns service status and version.

### Plans
- POST /plans
  - Accepts a task description and returns a structured plan.
- GET /plans/{id}
  - Returns the plan, status, and reasoning summary.

### Memory
- POST /memory
  - Stores a memory entry with source, timestamp, and confidence.
- GET /memory?query={term}
  - Retrieves relevant memory entries.

### Tools
- GET /tools
  - Lists registered tools and capabilities.
- POST /tools/{tool}/invoke
  - Invokes a tool with a payload.

## Plugin Model

Plugins should be modular and capability-based.

### Plugin Contract
- name
- version
- description
- capabilities
- schema
- invoke(payload)

#### Concrete Plugin Contract
Plugins should implement a stable contract so the runtime can discover, validate, and invoke them reliably.

- `name` (string): unique plugin identifier (e.g. `github`, `memory-sql`).
- `version` (string, semver): plugin implementation version.
- `description` (string): human-friendly description of the plugin.
- `capabilities` (array[string]): high-level capability tags such as `memory`, `tool`, `workflow`, `notification`, `model-adapter`.
- `schema` (object|null): optional JSON Schema describing accepted `invoke` payloads and their semantics.
- `invoke(payload)` (callable): the plugin entrypoint. Accepts a validated payload and returns a structured response. Implementations MUST raise clear exceptions for invalid inputs.

Example plugin contract (JSON-like):

```json
{
  "name": "echo",
  "version": "0.0.1",
  "description": "Echo tool for demos",
  "capabilities": ["tool"],
  "schema": {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}
}
```

Example invocation flow:

1. Runtime lists plugins via `GET /tools` and reads `schema` for validation.
2. Caller prepares a payload and validates it against the plugin `schema` (if present).
3. Caller POSTs to `POST /tools/{plugin}/invoke` with the payload.
4. The plugin executes `invoke(payload)` and returns a JSON response containing `result`, optional `explanation`, and `metadata`.

Example response shape:

```json
{
  "result": {"echo": "hello"},
  "explanation": "Echoed input",
  "metadata": {"duration_ms": 2}
}
```

### Plugin Audit
- GET /plugins/audit
  - Query params:
    - `name` (string): filter audit entries by plugin name
    - `action` (string): filter by lifecycle action such as `register`, `update`, or `unregister`
    - `start_ts`/`end_ts` (ISO-8601 datetime): filter entries by timestamp range
    - `page` (integer): page number for offset-based pagination
    - `per_page` (integer): number of entries per page
    - `cursor` (integer): optional cursor id for id-based pagination; returns entries with `id < cursor`
  - Returns:
    - `GET /plugins/audit?page=1&per_page=20` returns paged metadata and a `Link` header for next/prev pages
    - `GET /plugins/audit?per_page=20` returns the first page of entries with a `Link` header containing a `cursor` value for the next batch
  - Response shapes:
    - offset pagination:

```json
{
  "items": [...],
  "page": 1,
  "per_page": 20,
  "total": 124,
  "total_pages": 7
}
```

    - cursor pagination returns a list of entries and a `Link` header such as:

```http
Link: </plugins/audit?cursor=97&per_page=20>; rel="next"
```

- GET /plugins/audit.csv
  - Exports filtered audit entries as CSV

### Mini HTTP Examples

Quick curl examples demonstrating plugin registration, invocation, and lifecycle operations (assumes `X-API-Key` when `API_KEY` is set):

```bash
# Register a builtin plugin named 'mem_demo'
curl -X POST http://127.0.0.1:5000/plugins \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: test-key' \
  -d '{"name":"mem_demo","builtin":true,"builtin_name":"memory_inmem"}'

# Invoke tool to store an entry
curl -X POST http://127.0.0.1:5000/tools/mem_demo \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: test-key' \
  -d '{"action":"store","entry":{"text":"hello","source":"curl"}}'

# You may also use an Authorization Bearer token header instead of `X-API-Key`:
curl -X POST http://127.0.0.1:5000/tools/mem_demo \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer test-key' \
  -d '{"action":"store","entry":{"text":"hello","source":"curl"}}'

# Delete plugin
curl -X DELETE http://127.0.0.1:5000/plugins/mem_demo \
  -H 'X-API-Key: test-key'
```
```

Design notes:

- Backwards compatibility: simple plugins may register with only `name` and `capabilities` while richer plugins should provide `schema` and a class-based implementation exposed via a registry.
- Security: plugin authors should document permissions and any external network access; the runtime enforces safe defaults and explicit allow-lists.
- Observability: every plugin call should be logged with request id, plugin name, inputs (redacted), and duration.

### Supported Plugin Types
- Memory plugins
- Tool plugins
- Model adapters
- Workflow plugins
- Notification plugins

## Design Principles

- Open interfaces over proprietary lock-in.
- Clear schema and logging for every action.
- Human-readable explanations for every major step.
- Safe defaults and explicit permission boundaries.

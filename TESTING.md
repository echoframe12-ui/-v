# Running tests

This project uses `pytest` for the test suite. Instructions below show how to run tests locally and how CI runs them.

## Local (recommended)

1. Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

3. Run the full test suite:

```bash
pytest -q
```

4. Run tests with coverage:

```bash
pip install coverage
coverage run -m pytest
coverage report -m
```

## GitHub Actions CI

A workflow is provided at `.github/workflows/pytest.yml` which runs the test matrix on Python 3.10, 3.11, and 3.12, uploads JUnit XML test reports and an HTML coverage report (if generated).

## Troubleshooting

- If tests fail locally but passed in CI, ensure your Python version and installed deps match the CI matrix.
- To run a single test file: `pytest -q tests/test_somefile.py`

## Mini end-to-end plugin flow (example)

Use this quick flow to exercise the plugin lifecycle and tool invocation over HTTP. It assumes a running local server and an `API_KEY` set; adjust the header or unset `API_KEY` for open access.

```bash
# Start a dev server (in another terminal)
export API_KEY=test-key
FLASK_APP=app.py python -c "from app import app; app.run(port=5050)"

# Register a builtin memory plugin as `mem_e2e`
curl -X POST http://127.0.0.1:5050/plugins \
	-H 'Content-Type: application/json' \
	-H 'X-API-Key: test-key' \
	-d '{"name":"mem_e2e","builtin":true,"builtin_name":"memory_inmem"}'

# Alternative: use `Authorization: Bearer <token>` instead of `X-API-Key`
# Example using Authorization header:
curl -X POST http://127.0.0.1:5050/plugins \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer test-key' \
  -d '{"name":"mem_e2e_bearer","builtin":true,"builtin_name":"memory_inmem"}'

# Store an entry via the tool
curl -X POST http://127.0.0.1:5050/tools/mem_e2e \
	-H 'Content-Type: application/json' \
	-H 'X-API-Key: test-key' \
	-d '{"action":"store","entry":{"text":"mini e2e test","source":"curl"}}'

# Query stored entries
curl -X POST http://127.0.0.1:5050/tools/mem_e2e \
	-H 'Content-Type: application/json' \
	-H 'X-API-Key: test-key' \
	-d '{"action":"query","term":"mini"}'

# Unregister the plugin
curl -X DELETE http://127.0.0.1:5050/plugins/mem_e2e \
	-H 'X-API-Key: test-key'

# Invoking after delete should return 404
curl -i -X POST http://127.0.0.1:5050/tools/mem_e2e \
	-H 'Content-Type: application/json' \
	-H 'X-API-Key: test-key' \
	-d '{"action":"query","term":"mini"}'
```

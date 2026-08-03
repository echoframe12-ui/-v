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

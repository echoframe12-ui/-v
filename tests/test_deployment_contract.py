from pathlib import Path
import sqlite3

from deployment_contract import DEPLOYMENT_SCHEMA, evaluate, to_dict


def test_deployment_contract_requires_database_and_workspace(tmp_path):
    db_path = tmp_path / "deployment.db"
    workspace = tmp_path / "workspace"

    # The readiness contract only needs a valid SQLite database; use the same
    # dependency shape the application verifies at its production boundary.
    sqlite3.connect(db_path).close()
    result = evaluate(db_path=str(db_path), workspace=str(workspace))

    assert result.ready is True
    assert result.required_checks == ("db", "workspace")
    assert result.status_endpoint == "/status.json"


def test_deployment_contract_serialization_is_stable(tmp_path):
    db_path = tmp_path / "deployment.db"
    sqlite3.connect(db_path).close()
    payload = to_dict(evaluate(db_path=str(db_path), workspace=str(tmp_path / "workspace")))

    assert payload == {
        "schema": DEPLOYMENT_SCHEMA,
        "status_endpoint": "/status.json",
        "required_checks": ["db", "workspace"],
        "ready": True,
    }

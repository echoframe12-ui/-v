from pathlib import Path

from app import app, service
from production_smoke import run


def test_production_smoke_contract(tmp_path, monkeypatch):
    db_path = tmp_path / "smoke.db"
    workspace = tmp_path / "workspace"
    monkeypatch.setattr(service, "db_path", Path(db_path))
    with app.test_client() as client:
        result = run(client, db_path=str(db_path), workspace=str(workspace))

    assert result.ready
    assert result.checks["db"] and result.checks["workspace"]
    assert result.checks["status_endpoint"]
    assert result.status_code == 200
    assert result.content_type.startswith("application/json")
    assert result.request_id == "production-smoke"

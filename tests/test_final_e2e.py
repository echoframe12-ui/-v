from app import app, service
from final_e2e import verify


def test_final_e2e_integrity(tmp_path, monkeypatch):
    db_path = tmp_path / "final.db"
    workspace = tmp_path / "workspace"
    monkeypatch.setattr(service, "_db_path", db_path)
    service._init_db()

    with app.test_client() as client:
        result = verify(client, db_path=str(db_path), workspace=str(workspace))

    assert result.integrity is True
    assert result.smoke_ready is True
    assert result.status_code == 200
    assert result.request_id == "production-smoke"
    assert result.deployment["ready"] is True
    assert result.deployment["required_checks"] == ["db", "workspace"]
    assert result.contract_stack is not None
    assert result.contract_stack["ok"] is True

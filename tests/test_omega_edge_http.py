from __future__ import annotations

from flask import Flask

from attestation_protocol import attest_cycle, generate_keypair
from oceanic_cycle import CycleEvent, DecisionRoute, VerificationStatus
from omega_edge_http import edge_blueprint


def attestation() -> dict:
    event = CycleEvent(
        cycle_id="edge-http-cycle",
        state_id="state-1",
        contract_id="contract-1",
        observer="edge-http-test",
        evidence=("evidence-1",),
        verification=VerificationStatus.VERIFIED,
        confidence=0.99,
        dissent=(),
        decision=DecisionRoute.ACCEPT,
        action="observe",
        consequence="advance",
        next_state="observe",
        provenance_hash="sha256:provenance",
        timestamp="2026-08-04T00:00:00+00:00",
    )
    private, _ = generate_keypair()
    return attest_cycle(
        event,
        prompt="input",
        final_output="output",
        schema_digest="sha256:schema-v1",
        private_key=private,
    ).to_dict()


def client():
    app = Flask(__name__)
    app.register_blueprint(edge_blueprint)
    return app.test_client()


def test_edge_http_accepts_valid_attestation():
    payload = attestation()
    payload["expected_schema_digest"] = "sha256:schema-v1"
    response = client().post("/omega/edge/verify", json=payload)
    assert response.status_code == 200
    assert response.get_json()["valid"] is True


def test_edge_http_rejects_tampering():
    payload = attestation()
    payload["final_output"] = "tampered"
    response = client().post("/omega/edge/verify", json=payload)
    assert response.status_code == 422
    assert response.get_json()["valid"] is False


def test_edge_http_rejects_non_json_body():
    response = client().post("/omega/edge/verify", data="not-json", content_type="text/plain")
    assert response.status_code == 400

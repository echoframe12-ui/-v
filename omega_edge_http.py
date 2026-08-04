from __future__ import annotations

"""HTTP adapter for the Ω∞v Edge verifier."""

from flask import Blueprint, jsonify, request

from omega_edge import verify_edge_attestation


edge_blueprint = Blueprint("omega_edge", __name__, url_prefix="/omega/edge")


@edge_blueprint.post("/verify")
def verify():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "body must be a JSON attestation object"}), 400

    expected_schema_digest = payload.pop("expected_schema_digest", None)
    result = verify_edge_attestation(
        payload,
        expected_schema_digest=expected_schema_digest,
    )
    return jsonify(result.to_dict()), (200 if result.valid else 422)

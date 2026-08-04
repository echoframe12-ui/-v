"""Ω∞v cryptographic attestation envelope v0.1 tests."""

import json

import pytest

from attestation_protocol import SCHEMA, attest_cycle, evolve_attestation, generate_keypair, verify_attestation
from oceanic_cycle import Contract, OceanicCycle, Observation, VerificationResult, VerificationStatus


def _event(status=VerificationStatus.VERIFIED):
    cycle = OceanicCycle()
    return cycle.execute(
        Observation(observer="test", what="vertical slice", evidence=("evidence:1",)),
        Contract(contract_id="C-001", clauses=("output must match observation",)),
        VerificationResult(
            status=status,
            confidence=0.99 if status == VerificationStatus.VERIFIED else 0.5,
            evidence_hash="sha256:evidence",
            checks_passed=1,
            checks_total=1,
            dissent=("independent verifier disagrees",) if status == VerificationStatus.DISSENT else (),
        ),
    )


def _signed(**kwargs):
    private_key, _ = generate_keypair()
    return attest_cycle(
        _event(kwargs.pop("status", VerificationStatus.VERIFIED)),
        prompt="input",
        final_output="output",
        schema_digest="sha256:schema-v01",
        private_key=private_key,
        **kwargs,
    )


def test_sign_and_independently_verify_attestation():
    attestation = _signed()
    report = verify_attestation(json.loads(attestation.to_json()), expected_schema_digest="sha256:schema-v01")

    assert report["valid"] is True
    assert report["signature_valid"] is True
    assert report["key_id_valid"] is True
    assert report["output_intact"] is True
    assert report["schema_valid"] is True
    assert report["schema_digest_valid"] is True
    assert attestation.document["schema"] == SCHEMA


def test_tampering_signed_document_is_detected():
    tampered = json.loads(_signed().to_json())
    tampered["final_output"] = "tampered"
    assert verify_attestation(tampered)["valid"] is False


def test_tampering_output_hash_is_detected():
    tampered = json.loads(_signed().to_json())
    tampered["output_hash"] = "sha256:forged"
    assert verify_attestation(tampered)["valid"] is False


def test_wrong_resolved_schema_digest_is_rejected():
    attestation = _signed()
    report = verify_attestation(
        json.loads(attestation.to_json()),
        expected_schema_digest="sha256:wrong-schema",
    )
    assert report["signature_valid"] is True
    assert report["schema_digest_valid"] is False
    assert report["valid"] is False


def test_dissent_is_preserved_and_not_attested_as_verified():
    attestation = _signed(status=VerificationStatus.DISSENT)
    assert attestation.document["attestation_status"] == "DISSENT_FLAGGED"
    assert attestation.document["consensus"] is False
    assert attestation.document["dissent"] == ["independent verifier disagrees"]


def test_round_trip_is_canonical_and_json_serializable():
    first = json.loads(_signed().to_json())
    second = json.loads(json.dumps(first, sort_keys=True, separators=(",", ":")))
    assert first == second


def test_evolution_creates_new_signed_attestation_with_immutable_parent():
    parent = _signed()
    parent_snapshot = json.loads(parent.to_json())
    child_key, _ = generate_keypair()
    child = evolve_attestation(
        parent,
        _event(),
        prompt="next input",
        final_output="next output",
        schema_digest="sha256:schema-v01",
        private_key=child_key,
        expected_parent_schema_digest="sha256:schema-v01",
    )

    assert child.document["attestation_id"] != parent.document["attestation_id"]
    assert child.document["parent_attestation_id"] == parent.document["attestation_id"]
    assert json.loads(parent.to_json()) == parent_snapshot
    assert verify_attestation(parent_snapshot, expected_schema_digest="sha256:schema-v01")["valid"] is True
    assert verify_attestation(json.loads(child.to_json()), expected_schema_digest="sha256:schema-v01")["valid"] is True


def test_evolution_rejects_invalid_parent():
    parent = _signed()
    tampered = json.loads(parent.to_json())
    tampered["final_output"] = "tampered"
    invalid_parent = type(parent)(
        document={k: v for k, v in tampered.items() if k not in {"signature", "verifier"}},
        signature=tampered["signature"],
        public_key=tampered["verifier"]["public_key"],
    )
    child_key, _ = generate_keypair()

    with pytest.raises(ValueError, match="invalid parent"):
        evolve_attestation(
            invalid_parent,
            _event(),
            prompt="next input",
            final_output="next output",
            schema_digest="sha256:schema-v01",
            private_key=child_key,
        )


def test_drift_recompile_state_is_signed_into_new_lineage():
    parent = _signed()
    child_key, _ = generate_keypair()
    child = evolve_attestation(
        parent,
        _event(),
        prompt="recompiled input",
        final_output="recompiled output",
        schema_digest="sha256:schema-v01",
        private_key=child_key,
        drift_state="detected",
        recompile_state="recompiled",
    )

    assert child.document["parent_attestation_id"] == parent.document["attestation_id"]
    assert child.document["drift_state"] == "detected"
    assert child.document["recompile_state"] == "recompiled"
    assert verify_attestation(json.loads(child.to_json()), expected_schema_digest="sha256:schema-v01")["valid"] is True

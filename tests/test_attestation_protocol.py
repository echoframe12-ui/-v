"""Ω∞v cryptographic attestation envelope v0.1 tests."""

import json

from attestation_protocol import SCHEMA, attest_cycle, generate_keypair, verify_attestation
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

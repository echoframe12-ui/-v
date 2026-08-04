"""Ω∞v Attestation Protocol v0.1 tests."""

import copy
import json

from attestation_protocol import (
    SCHEMA,
    attest_cycle,
    generate_keypair,
    verify_attestation,
)
from oceanic_cycle import Contract, OceanicCycle, Observation, VerificationResult, VerificationStatus


def _event():
    cycle = OceanicCycle()
    return cycle.execute(
        Observation(observer="test", what="vertical slice", evidence=("evidence:1",)),
        Contract(contract_id="C-001", clauses=("output must match observation",)),
        VerificationResult(
            status=VerificationStatus.VERIFIED,
            confidence=0.99,
            evidence_hash="sha256:evidence",
            checks_passed=1,
            checks_total=1,
        ),
    )


def test_sign_and_independently_verify_attestation():
    private_key, _ = generate_keypair()
    attestation = attest_cycle(
        _event(),
        prompt="return the verified value",
        final_output="verified value",
        schema_digest="sha256:schema-v01",
        private_key=private_key,
    )

    report = verify_attestation(json.loads(attestation.to_json()))

    assert report["valid"] is True
    assert report["signature_valid"] is True
    assert report["output_intact"] is True
    assert report["schema_valid"] is True
    assert attestation.document["schema"] == SCHEMA


def test_tampering_signed_document_is_detected():
    private_key, _ = generate_keypair()
    attestation = attest_cycle(
        _event(),
        prompt="input",
        final_output="original",
        schema_digest="sha256:schema-v01",
        private_key=private_key,
    )
    tampered = json.loads(attestation.to_json())
    tampered["final_output"] = "tampered"

    report = verify_attestation(tampered)
    assert report["valid"] is False


def test_tampering_output_hash_without_signature_is_detected():
    private_key, _ = generate_keypair()
    attestation = attest_cycle(
        _event(),
        prompt="input",
        final_output="original",
        schema_digest="sha256:schema-v01",
        private_key=private_key,
    )
    tampered = json.loads(attestation.to_json())
    tampered["output_hash"] = "sha256:forged"

    report = verify_attestation(tampered)
    assert report["valid"] is False


def test_dissent_is_preserved_and_not_attested_as_verified():
    cycle = OceanicCycle()
    event = cycle.execute(
        Observation(observer="test", what="dissent", evidence=("evidence:2",)),
        Contract(contract_id="C-002", clauses=("check dissent",)),
        VerificationResult(
            status=VerificationStatus.DISSENT,
            confidence=0.5,
            evidence_hash="sha256:evidence",
            dissent=("independent verifier disagrees",),
        ),
    )
    private_key, _ = generate_keypair()
    attestation = attest_cycle(
        event,
        prompt="input",
        final_output="held",
        schema_digest="sha256:schema-v01",
        private_key=private_key,
    )

    assert attestation.document["attestation_status"] == "DISSENT_FLAGGED"
    assert attestation.document["consensus"] is False
    assert attestation.document["dissent"] == ["independent verifier disagrees"]


def test_round_trip_is_canonical_and_json_serializable():
    private_key, _ = generate_keypair()
    attestation = attest_cycle(
        _event(),
        prompt="input",
        final_output="output",
        schema_digest="sha256:schema-v01",
        private_key=private_key,
    )
    first = json.loads(attestation.to_json())
    second = json.loads(json.dumps(first, sort_keys=True, separators=(",", ":")))
    assert first == second

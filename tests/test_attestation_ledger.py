"""Integration tests for signed attestations and the existing event ledger."""

import json

from attestation_protocol import attest_cycle, generate_keypair, verify_attestation
from oceanic_cycle import Contract, OceanicCycle, Observation, VerificationResult, VerificationStatus
from oceanic_event_ledger import EventLedger


def _signed():
    cycle = OceanicCycle()
    event = cycle.execute(
        Observation(observer="test", what="ledger slice", evidence=("evidence:1",)),
        Contract(contract_id="C-LEDGER", clauses=("output must match observation",)),
        VerificationResult(
            status=VerificationStatus.VERIFIED,
            confidence=0.99,
            evidence_hash="sha256:evidence",
            checks_passed=1,
            checks_total=1,
        ),
    )
    private_key, _ = generate_keypair()
    return attest_cycle(
        event,
        prompt="input",
        final_output="output",
        schema_digest="sha256:schema-v01",
        private_key=private_key,
    )


def test_signed_attestation_persists_and_verifies_independently(tmp_path):
    ledger = EventLedger(tmp_path / "events.jsonl")
    attestation = _signed()

    event = ledger.append_attestation(attestation)
    stored = ledger.get_attestation(attestation.document["attestation_id"])

    assert event.event_type == "ATTESTATION_ISSUED"
    assert stored == json.loads(attestation.to_json())
    assert ledger.verify_chain() is True
    assert verify_attestation(stored, expected_schema_digest="sha256:schema-v01")["valid"] is True


def test_tampering_stored_attestation_breaks_ledger_chain(tmp_path):
    path = tmp_path / "events.jsonl"
    ledger = EventLedger(path)
    ledger.append_attestation(_signed())

    record = json.loads(path.read_text(encoding="utf-8").splitlines()[0])
    record["payload"]["final_output"] = "tampered"
    path.write_text(json.dumps(record, sort_keys=True) + "\n", encoding="utf-8")

    assert ledger.verify_chain() is False


def test_tampering_attestation_payload_is_detected_independently(tmp_path):
    ledger = EventLedger(tmp_path / "events.jsonl")
    attestation = _signed()
    ledger.append_attestation(attestation)
    stored = ledger.get_attestation(attestation.document["attestation_id"])
    assert stored is not None

    stored["final_output"] = "tampered"
    assert verify_attestation(stored, expected_schema_digest="sha256:schema-v01")["valid"] is False

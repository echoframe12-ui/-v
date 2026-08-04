"""Tests for the Oceanic Event Ledger — append-only, hash-chained record."""
import json
import tempfile
import unittest
from pathlib import Path

from attestation_protocol import attest_cycle, evolve_attestation, generate_keypair, verify_attestation
from oceanic_cycle import Contract, OceanicCycle, Observation, VerificationResult, VerificationStatus
from oceanic_event_ledger import EventLedger, LedgerEvent


def _signed_attestation(final_output="ledger output", parent_attestation_id=None):
    cycle = OceanicCycle()
    event = cycle.execute(
        Observation(observer="test", what="ledger vertical slice", evidence=("evidence:ledger",)),
        Contract(contract_id="C-LEDGER", clauses=("signed output is persisted",)),
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
        prompt="ledger input",
        final_output=final_output,
        schema_digest="sha256:schema-v01",
        private_key=private_key,
        parent_attestation_id=parent_attestation_id,
    )


def _evolved_attestation(parent, final_output="state-1"):
    cycle = OceanicCycle()
    event = cycle.execute(
        Observation(observer="test", what="evolved ledger state", evidence=("evidence:evolved",)),
        Contract(contract_id="C-LEDGER", clauses=("signed output is persisted",)),
        VerificationResult(
            status=VerificationStatus.VERIFIED,
            confidence=0.98,
            evidence_hash="sha256:evidence-evolved",
            checks_passed=1,
            checks_total=1,
        ),
    )
    private_key, _ = generate_keypair()
    return evolve_attestation(
        parent,
        event,
        prompt="ledger evolution",
        final_output=final_output,
        schema_digest="sha256:schema-v01",
        private_key=private_key,
    )


class OceanicEventLedgerTests(unittest.TestCase):

    def test_append_and_verify_hash_chain(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger = EventLedger(Path(directory) / "events.jsonl")
            first = ledger.append("attestation.created", "att_1", {"status": "proved"})
            second = ledger.append("authorization.granted", "att_1", {"reviewer": "human"})

            self.assertEqual(first.sequence, 1)
            self.assertEqual(second.sequence, 2)
            self.assertEqual(second.previous_digest, first.event_digest)
            self.assertTrue(ledger.verify_chain())

    def test_real_signed_attestation_persists_and_independently_verifies(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger = EventLedger(Path(directory) / "events.jsonl")
            attestation = _signed_attestation()
            event = ledger.append_attestation(attestation)
            stored = ledger.get_attestation(attestation.document["attestation_id"])

            self.assertEqual(event.event_type, "ATTESTATION_ISSUED")
            self.assertEqual(event.entity_id, attestation.document["attestation_id"])
            self.assertIsNotNone(stored)
            report = verify_attestation(stored, expected_schema_digest="sha256:schema-v01")
            self.assertTrue(report["valid"])
            self.assertTrue(ledger.verify_chain())

    def test_persisted_parent_child_lineage_resolves_and_verifies(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger = EventLedger(Path(directory) / "events.jsonl")
            parent = _signed_attestation("state-0")
            child = _signed_attestation("state-1", parent.document["attestation_id"])
            ledger.append_attestation(parent)
            ledger.append_attestation(child)

            lineage = ledger.get_attestation_lineage(child.document["attestation_id"])
            self.assertEqual(len(lineage), 2)
            self.assertEqual(lineage[0]["attestation_id"], parent.document["attestation_id"])
            self.assertEqual(lineage[1]["attestation_id"], child.document["attestation_id"])
            self.assertEqual(lineage[1]["parent_attestation_id"], lineage[0]["attestation_id"])
            self.assertTrue(verify_attestation(lineage[0], expected_schema_digest="sha256:schema-v01")["valid"])
            self.assertTrue(verify_attestation(lineage[1], expected_schema_digest="sha256:schema-v01")["valid"])
            self.assertTrue(ledger.verify_chain())

    def test_real_evolution_persists_parent_child_lineage(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger = EventLedger(Path(directory) / "events.jsonl")
            parent = _signed_attestation("state-0")
            ledger.append_attestation(parent)
            parent_before = parent.to_json()

            child = _evolved_attestation(parent, "state-1")
            ledger.append_attestation(child)

            self.assertEqual(parent.to_json(), parent_before)
            self.assertNotEqual(parent.document["attestation_id"], child.document["attestation_id"])
            self.assertEqual(child.document["parent_attestation_id"], parent.document["attestation_id"])

            reloaded_parent = ledger.get_attestation(parent.document["attestation_id"])
            reloaded_child = ledger.get_attestation(child.document["attestation_id"])
            self.assertTrue(verify_attestation(reloaded_parent, expected_schema_digest="sha256:schema-v01")["valid"])
            self.assertTrue(verify_attestation(reloaded_child, expected_schema_digest="sha256:schema-v01")["valid"])

            lineage = ledger.get_attestation_lineage(child.document["attestation_id"])
            self.assertEqual(
                tuple(item["attestation_id"] for item in lineage),
                (parent.document["attestation_id"], child.document["attestation_id"]),
            )
            self.assertTrue(ledger.verify_chain())

    def test_missing_parent_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger = EventLedger(Path(directory) / "events.jsonl")
            child = _signed_attestation("state-1", "att_missing")
            ledger.append_attestation(child)
            with self.assertRaisesRegex(ValueError, "missing parent attestation"):
                ledger.get_attestation_lineage(child.document["attestation_id"])

    def test_unsigned_attestation_is_rejected(self):
        class Unsigned:
            def to_dict(self):
                return {"attestation_id": "att_unsigned"}

        with tempfile.TemporaryDirectory() as directory:
            ledger = EventLedger(Path(directory) / "events.jsonl")
            with self.assertRaises(ValueError):
                ledger.append_attestation(Unsigned())

    def test_tampering_with_signed_attestation_is_detected_by_ledger_chain(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "events.jsonl"
            ledger = EventLedger(path)
            ledger.append_attestation(_signed_attestation())
            lines = path.read_text(encoding="utf-8").splitlines()
            data = json.loads(lines[0])
            data["payload"]["signature"] = "tampered"
            path.write_text(json.dumps(data) + "\n", encoding="utf-8")

            self.assertFalse(ledger.verify_chain())

    def test_tampering_is_detected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "events.jsonl"
            ledger = EventLedger(path)
            ledger.append("observation.completed", "att_1", {"status": "matched"})
            path.write_text(
                path.read_text(encoding="utf-8").replace("matched", "deviated"),
                encoding="utf-8",
            )
            self.assertFalse(ledger.verify_chain())

    def test_empty_ledger_chain_is_intact(self):
        with tempfile.TemporaryDirectory() as d:
            ledger = EventLedger(Path(d) / "events.jsonl")
            self.assertTrue(ledger.verify_chain())

    def test_single_entry_chain_is_intact(self):
        with tempfile.TemporaryDirectory() as d:
            ledger = EventLedger(Path(d) / "events.jsonl")
            event = ledger.append("contract.created", "c_1", {"intent": "test"})
            self.assertEqual(event.sequence, 1)
            self.assertTrue(ledger.verify_chain())

    def test_event_fields_are_populated(self):
        with tempfile.TemporaryDirectory() as d:
            ledger = EventLedger(Path(d) / "events.jsonl")
            event = ledger.append("verification.completed", "c_1", {"adapter_count": 3})
            self.assertEqual(event.event_type, "verification.completed")
            self.assertEqual(event.entity_id, "c_1")
            self.assertEqual(event.payload["adapter_count"], 3)
            self.assertTrue(event.timestamp)
            self.assertTrue(event.event_digest.startswith("sha256:"))

    def test_history_is_in_sequence_order(self):
        with tempfile.TemporaryDirectory() as d:
            ledger = EventLedger(Path(d) / "events.jsonl")
            for i in range(5):
                ledger.append(f"event.{i}", f"e_{i}", {"i": i})
            history = ledger.history()
            self.assertIsInstance(history, tuple)
            self.assertEqual(len(history), 5)
            for i, event in enumerate(history):
                self.assertEqual(event.sequence, i + 1)

    def test_empty_ledger_history_is_empty(self):
        with tempfile.TemporaryDirectory() as d:
            ledger = EventLedger(Path(d) / "events.jsonl")
            self.assertEqual(ledger.history(), ())

    def test_corrupt_sequence_detected(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "events.jsonl"
            ledger = EventLedger(path)
            ledger.append("ev1", "id1", {})
            ledger.append("ev2", "id2", {})

            lines = path.read_text(encoding="utf-8").splitlines()
            data2 = json.loads(lines[1])
            data2["sequence"] = 99
            path.write_text(lines[0] + "\n" + json.dumps(data2) + "\n", encoding="utf-8")
            self.assertFalse(ledger.verify_chain())

    def test_corrupt_previous_digest_detected(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "events.jsonl"
            ledger = EventLedger(path)
            ledger.append("ev1", "id1", {})
            ledger.append("ev2", "id2", {})

            lines = path.read_text(encoding="utf-8").splitlines()
            data2 = json.loads(lines[1])
            data2["previous_digest"] = "sha256:badhash"
            path.write_text(lines[0] + "\n" + json.dumps(data2) + "\n", encoding="utf-8")
            self.assertFalse(ledger.verify_chain())

    def test_ledger_event_dataclass(self):
        e = LedgerEvent(1, "t", "id", "ts", {}, None, "sha256:abc")
        self.assertEqual(e.sequence, 1)
        self.assertEqual(e.event_type, "t")
        self.assertEqual(e.entity_id, "id")
        self.assertIsNone(e.previous_digest)


if __name__ == "__main__":
    unittest.main()

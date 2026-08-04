"""Tests for the Oceanic Event Ledger — append-only, hash-chained record."""
import json
import tempfile
import unittest
from pathlib import Path

from oceanic_event_ledger import EventLedger, LedgerEvent


class _SignedAttestationStub:
    def __init__(self, payload):
        self._payload = payload

    def to_dict(self):
        return dict(self._payload)


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

    def test_signed_attestation_is_persisted_and_retrievable(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger = EventLedger(Path(directory) / "events.jsonl")
            payload = {
                "attestation_id": "att_signed_1",
                "schema": "oceanic.attestation/v0.1",
                "signature": "signed-by-ed25519",
                "verifier": {"algorithm": "Ed25519", "key_id": "sha256:key"},
                "output_hash": "sha256:output",
            }
            event = ledger.append_attestation(_SignedAttestationStub(payload))

            self.assertEqual(event.event_type, "ATTESTATION_ISSUED")
            self.assertEqual(event.entity_id, "att_signed_1")
            self.assertEqual(ledger.get_attestation("att_signed_1"), payload)
            self.assertTrue(ledger.verify_chain())

    def test_tampering_with_signed_attestation_is_detected_by_ledger_chain(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "events.jsonl"
            ledger = EventLedger(path)
            ledger.append_attestation(_SignedAttestationStub({
                "attestation_id": "att_signed_1",
                "signature": "signed-by-ed25519",
                "verifier": {"algorithm": "Ed25519", "key_id": "sha256:key"},
            }))
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

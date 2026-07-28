"""Tests for the Oceanic Event Ledger — append-only, hash-chained record.

Covers:
  - Append and hash-chain verification (2-event)
  - Tampering detection
  - Empty ledger chain is intact
  - Single entry chain is intact
  - Event fields are populated correctly
  - History is returned in sequence order
  - Empty ledger history is empty
"""
import tempfile
import unittest
from pathlib import Path

from oceanic_event_ledger import EventLedger


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
            history = list(ledger.history())
            self.assertEqual(len(history), 5)
            for i, event in enumerate(history):
                self.assertEqual(event.sequence, i + 1)

    def test_empty_ledger_history_is_empty(self):
        with tempfile.TemporaryDirectory() as d:
            ledger = EventLedger(Path(d) / "events.jsonl")
            self.assertEqual(list(ledger.history()), [])


if __name__ == "__main__":
    unittest.main()


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
            path.write_text(path.read_text(encoding="utf-8").replace("matched", "deviated"), encoding="utf-8")

            self.assertFalse(ledger.verify_chain())


if __name__ == "__main__":
    unittest.main()

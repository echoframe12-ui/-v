import json
import os
import tempfile
import unittest

from oceanic_attestation_engine import AutonomousAttestationEngine
from oceanic_event_ledger import EventLedger


class AutonomousAttestationEngineTests(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp_dir.name, "test_attest.db")
        self.ledger_path = os.path.join(self.tmp_dir.name, "test_ledger.jsonl")
        self.engine = AutonomousAttestationEngine(
            db_path=self.db_path,
            ledger_path=self.ledger_path,
            secret_key="test-secret-key",
        )

    def tearDown(self):
        self.engine.stop_daemon()
        try:
            self.tmp_dir.cleanup()
        except Exception:
            pass


    def test_run_verification_cycle_intact(self):
        proof = self.engine.run_verification_cycle()
        self.assertIn("proof_id", proof)
        self.assertIn("signature", proof)

        data = proof["data"]
        self.assertEqual(data["status"], "clear")
        self.assertTrue(data["event_ledger"]["valid"])
        self.assertTrue(data["attestation_ledger"]["valid"])

        # Check ledger recorded event
        ledger = EventLedger(self.ledger_path)
        events = ledger.history()
        self.assertGreaterEqual(len(events), 1)
        self.assertEqual(events[-1].event_type, "attestation.daemon_verified")

    def test_verify_proof_valid(self):
        proof = self.engine.run_verification_cycle()
        verification = self.engine.verify_proof(proof)
        self.assertTrue(verification["valid"])
        self.assertTrue(verification["intact"])

    def test_verify_proof_tampered_signature(self):
        proof = self.engine.run_verification_cycle()
        proof["signature"] = "0" * 64
        verification = self.engine.verify_proof(proof)
        self.assertFalse(verification["valid"])
        self.assertIn("Signature mismatch", verification["reason"])

    def test_daemon_lifecycle(self):
        self.engine.start_daemon(interval_seconds=1)
        status = self.engine.get_daemon_status()
        self.assertTrue(status["running"])

        self.engine.stop_daemon()
        status_stopped = self.engine.get_daemon_status()
        self.assertFalse(status_stopped["running"])

    def test_tampered_event_ledger_triggers_dissent(self):
        # 1. Add some valid events
        ledger = EventLedger(self.ledger_path)
        ledger.append("test.event", "entity-1", {"key": "val1"})
        ledger.append("test.event", "entity-2", {"key": "val2"})

        # 2. Run clean cycle
        proof1 = self.engine.run_verification_cycle()
        self.assertEqual(proof1["data"]["status"], "clear")

        # 3. Tamper with the ledger file
        lines = open(self.ledger_path, "r", encoding="utf-8").readlines()
        if lines:
            tampered_first = json.loads(lines[0])
            tampered_first["entity_id"] = "TAMPERED"
            lines[0] = json.dumps(tampered_first) + "\n"
            with open(self.ledger_path, "w", encoding="utf-8") as f:
                f.writelines(lines)

        # 4. Run cycle again -> should detect tamper & emit dissent
        proof2 = self.engine.run_verification_cycle()
        self.assertEqual(proof2["data"]["status"], "dissent")
        self.assertFalse(proof2["data"]["event_ledger"]["valid"])


if __name__ == "__main__":
    unittest.main()

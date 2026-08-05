import unittest
from pathlib import Path

from cross_repo_handoff import CrossRepoHandoffEngine, HandoffPacket
from oceanic_event_ledger import EventLedger


class CrossRepoHandoffTests(unittest.TestCase):
    def setUp(self):
        self.ledger_path = Path("test_handoff_ledger.jsonl")
        if self.ledger_path.exists():
            self.ledger_path.unlink()
        self.ledger = EventLedger(self.ledger_path)
        self.engine = CrossRepoHandoffEngine(ledger=self.ledger)

    def tearDown(self):
        if self.ledger_path.exists():
            self.ledger_path.unlink()

    def test_export_and_import_handoff(self):
        payload = {"contract_id": "test.c1", "status": "verified"}
        packet = self.engine.export_handoff("repo_A", "repo_B", payload, sequence=1)

        self.assertEqual(packet.source_repo, "repo_A")
        self.assertEqual(packet.target_repo, "repo_B")
        self.assertEqual(packet.sequence, 1)
        self.assertTrue(packet.state_hash)

        import_res = self.engine.import_handoff(packet, expected_sequence=1)
        self.assertTrue(import_res["valid"])
        self.assertEqual(import_res["source_repo"], "repo_A")
        self.assertEqual(import_res["target_repo"], "repo_B")
        self.assertEqual(import_res["transition"]["action"], "continue_becoming")

        events = self.ledger.history()
        event_types = [e.event_type for e in events]
        self.assertIn("handoff.exported", event_types)
        self.assertIn("handoff.imported", event_types)
        self.assertIn("handoff.verified", event_types)


    def test_import_detects_corrupted_payload(self):
        payload = {"data": "original"}
        packet = self.engine.export_handoff("repo_A", "repo_B", payload)

        corrupted_dict = packet.to_dict()
        corrupted_dict["payload"] = {"data": "tampered"}

        with self.assertRaises(ValueError) as ctx:
            self.engine.import_handoff(corrupted_dict)
        self.assertIn("hash mismatch", str(ctx.exception).lower())

    def test_verify_continuous_cycle_A_B_C_A(self):
        p1 = self.engine.export_handoff("repo_A", "repo_B", {"step": 1}, sequence=1)
        p2 = self.engine.export_handoff("repo_B", "repo_C", {"step": 2}, sequence=2)
        p3 = self.engine.export_handoff("repo_C", "repo_A", {"step": 3}, sequence=3)

        cycle_res = self.engine.verify_cycle([p1, p2, p3])
        self.assertTrue(cycle_res["valid"])
        self.assertTrue(cycle_res["is_closed_loop"])
        self.assertEqual(cycle_res["flow"], "repo_A -> repo_B -> repo_C -> repo_A")

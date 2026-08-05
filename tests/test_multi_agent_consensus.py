import os
import unittest
from pathlib import Path

from multi_agent_consensus import MultiAgentConsensusEngine, MultiAgentConsensusResult
from oceanic_event_ledger import EventLedger
from perspectives import MockPerspectiveAdapter, PerspectiveRegistry


class MultiAgentConsensusTests(unittest.TestCase):
    def setUp(self):
        self.ledger_path = Path("test_consensus_ledger.jsonl")
        self.db_path = Path("test_consensus.db")
        try:
            if self.ledger_path.exists():
                self.ledger_path.unlink()
            if self.db_path.exists():
                self.db_path.unlink()
        except OSError:
            pass

    def tearDown(self):
        try:
            if self.ledger_path.exists():
                self.ledger_path.unlink()
            if self.db_path.exists():
                self.db_path.unlink()
        except OSError:
            pass


    def test_unanimous_consensus_converges(self):
        registry = PerspectiveRegistry()
        registry.register(MockPerspectiveAdapter("mock_unanimous", "v1", response="approve"))

        engine = MultiAgentConsensusEngine(registry=registry, db_path=str(self.db_path))
        result = engine.run_loop("Verify safety", max_iterations=3)

        self.assertTrue(result.converged)
        self.assertEqual(result.final_dissent_score, 0.0)
        self.assertEqual(result.assessment.status, "clear")
        self.assertEqual(result.transition.action, "continue_becoming")

    def test_dissent_fails_convergence(self):
        registry = PerspectiveRegistry()
        registry.register(MockPerspectiveAdapter("mock_unanimous", "v1", response="approve"))
        registry.register(MockPerspectiveAdapter("mock_dissenting", "v1", response="revise"))


        ledger = EventLedger(self.ledger_path)
        engine = MultiAgentConsensusEngine(registry=registry, db_path=str(self.db_path), ledger=ledger)
        result = engine.run_loop("Verify controversial change", max_iterations=2)

        self.assertFalse(result.converged)
        self.assertGreater(result.final_dissent_score, 0.0)
        self.assertEqual(result.assessment.status, "dissent")
        self.assertEqual(result.transition.action, "await_human")

        events = ledger.history()
        event_types = [e.event_type for e in events]
        self.assertIn("mood.dissent", event_types)


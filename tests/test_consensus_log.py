import os
import tempfile
import unittest

from consensus_log import ConsensusLog, dissent_score
try:
    from tests.test_helpers import safe_remove
except ImportError:
    from test_helpers import safe_remove


class DissentScoreTests(unittest.TestCase):
    def test_unanimous_opinion_is_zero(self):
        self.assertEqual(dissent_score(["approve", "approve", "approve"]), 0.0)

    def test_even_split_is_half(self):
        self.assertEqual(dissent_score(["approve", "approve", "revise", "revise"]), 0.5)

    def test_abstentions_are_ignored(self):
        # two opinions, both approve -> unanimous among opinions
        self.assertEqual(dissent_score(["approve", "approve", "abstain"]), 0.0)

    def test_all_abstain_is_zero(self):
        self.assertEqual(dissent_score(["abstain", "abstain"]), 0.0)


class ConsensusLogTests(unittest.TestCase):
    def setUp(self):
        handle = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        handle.close()
        self.db_path = handle.name
        self.log = ConsensusLog(self.db_path)

    def tearDown(self):
        safe_remove(self.db_path)

    def _result(self, verdicts, majority, dissent):
        return {"adapters": ["a"] * len(verdicts), "verdicts": verdicts,
                "majority": majority, "dissent": dissent}

    def test_record_hashes_prompt_and_scores_dissent(self):
        entry = self.log.record("plan the charter", self._result(
            ["approve", "revise"], "approve", True))
        self.assertEqual(len(entry["prompt_sha256"]), 64)
        self.assertNotIn("plan the charter", entry["prompt_sha256"])
        self.assertEqual(entry["dissent_score"], 0.5)
        self.assertTrue(entry["dissent"])

    def test_history_is_newest_first_and_capped(self):
        for i in range(3):
            self.log.record(f"p{i}", self._result(["approve"], "approve", False))
        history = self.log.list(limit=2)
        self.assertEqual(len(history), 2)
        self.assertGreater(history[0]["id"], history[1]["id"])

    def test_stats_aggregate_dissent(self):
        self.log.record("a", self._result(["approve", "approve"], "approve", False))
        self.log.record("b", self._result(["approve", "revise"], "approve", True))
        stats = self.log.stats()
        self.assertEqual(stats["evaluations"], 2)
        self.assertEqual(stats["dissent_count"], 1)
        self.assertEqual(stats["dissent_rate"], 0.5)
        # mean of 0.0 and 0.5
        self.assertEqual(stats["mean_dissent_score"], 0.25)

    def test_empty_stats(self):
        stats = self.log.stats()
        self.assertEqual(stats["evaluations"], 0)
        self.assertEqual(stats["dissent_rate"], 0.0)

    def _named(self, pairs, majority, dissent):
        # pairs: list of (adapter, verdict) aligned by index
        return {
            "adapters": [a for a, _ in pairs],
            "verdicts": [v for _, v in pairs],
            "majority": majority,
            "dissent": dissent,
        }

    def test_record_retains_aligned_adapter_names(self):
        entry = self.log.record("p", self._named(
            [("optimist", "approve"), ("skeptic", "revise")], "approve", True))
        self.assertEqual(entry["adapter_names"], ["optimist", "skeptic"])
        self.assertEqual(self.log.list()[0]["adapter_names"], ["optimist", "skeptic"])

    def test_by_adapter_tracks_each_perspective(self):
        # skeptic is the outlier: it dissents in 2 of 3 evaluations
        self.log.record("1", self._named(
            [("optimist", "approve"), ("skeptic", "revise"), ("rules-engine", "approve")], "approve", True))
        self.log.record("2", self._named(
            [("optimist", "approve"), ("skeptic", "revise"), ("rules-engine", "approve")], "approve", True))
        self.log.record("3", self._named(
            [("optimist", "approve"), ("skeptic", "approve"), ("rules-engine", "approve")], "approve", False))
        by = {row["adapter"]: row for row in self.log.by_adapter()}
        self.assertEqual(by["optimist"]["agreement_rate"], 1.0)
        self.assertEqual(by["rules-engine"]["agreement_rate"], 1.0)
        # skeptic agreed once in three -> the outlier
        self.assertEqual(by["skeptic"]["evaluations"], 3)
        self.assertEqual(by["skeptic"]["dissented"], 2)
        self.assertEqual(by["skeptic"]["agreement_rate"], round(1 / 3, 3))

    def test_by_adapter_excludes_rows_without_names(self):
        # a row with mismatched/absent names is skipped, not guessed
        self.log.record("named", self._named([("optimist", "approve")], "approve", False))
        # simulate a pre-migration row: names absent
        legacy = {"adapters": ["x", "y"], "verdicts": ["approve", "revise"], "majority": "approve", "dissent": True}
        entry = self.log.record("legacy", legacy)
        import sqlite3
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("UPDATE consensus_evaluations SET adapter_names = NULL WHERE id = ?", (entry["id"],))
        by = {row["adapter"]: row for row in self.log.by_adapter()}
        self.assertIn("optimist", by)
        self.assertNotIn("x", by)  # the nulled legacy row is excluded

    def test_migration_adds_column_to_existing_table(self):
        # build a table WITHOUT adapter_names, then open with ConsensusLog (migration)
        import sqlite3
        path = self.db_path + ".legacy"
        try:
            with sqlite3.connect(path) as conn:
                conn.execute(
                    "CREATE TABLE consensus_evaluations (id INTEGER PRIMARY KEY AUTOINCREMENT, "
                    "prompt_sha256 TEXT NOT NULL, adapters INTEGER NOT NULL, majority TEXT, "
                    "dissent INTEGER NOT NULL, dissent_score REAL NOT NULL, verdicts TEXT NOT NULL, "
                    "created_at TEXT NOT NULL)"
                )
            log = ConsensusLog(path)  # should ALTER TABLE ADD COLUMN, not crash
            log.record("p", self._named([("optimist", "approve")], "approve", False))
            self.assertEqual(log.list()[0]["adapter_names"], ["optimist"])
        finally:
            if os.path.exists(path):
                os.remove(path)


if __name__ == "__main__":
    unittest.main()

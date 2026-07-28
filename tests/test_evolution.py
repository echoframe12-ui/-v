"""Tests for evolution.py — the platform's compounding append-only footprint.

Covers:
  - compounding() with multiple ledgers: records_total, ledger_count
  - Each ledger has count and accrues fields
  - Empty footprint is zeroed
  - status is 'continues'
  - append_only is True
  - note field is present and non-empty
  - Single ledger edge case
  - Unknown ledger name gets empty accrues string
  - LEDGER_NOTES values are non-empty strings
"""
import unittest

import evolution


class CompoundingTests(unittest.TestCase):

    def test_structures_counts_with_totals(self):
        result = evolution.compounding({"attestations": 3, "decisions": 60})
        self.assertEqual(result["records_total"], 63)
        self.assertEqual(result["ledger_count"], 2)
        self.assertTrue(result["append_only"])
        self.assertEqual(result["invariant"], "Continuous Becoming")

    def test_each_ledger_carries_a_count_and_note(self):
        result = evolution.compounding({"attestations": 5})
        entry = result["ledgers"]["attestations"]
        self.assertEqual(entry["count"], 5)
        self.assertTrue(entry["accrues"])  # a human-facing description

    def test_empty_footprint_is_zeroed(self):
        result = evolution.compounding({})
        self.assertEqual(result["records_total"], 0)
        self.assertEqual(result["ledger_count"], 0)

    def test_status_is_continues(self):
        result = evolution.compounding({"attestations": 1})
        self.assertEqual(result["status"], "continues")

    def test_append_only_is_true(self):
        result = evolution.compounding({"decisions": 10})
        self.assertTrue(result["append_only"])

    def test_note_field_is_present_and_non_empty(self):
        result = evolution.compounding({"attestations": 2})
        self.assertIn("note", result)
        self.assertTrue(result["note"].strip())

    def test_single_ledger_edge_case(self):
        result = evolution.compounding({"drift_audits": 7})
        self.assertEqual(result["records_total"], 7)
        self.assertEqual(result["ledger_count"], 1)
        self.assertEqual(result["ledgers"]["drift_audits"]["count"], 7)

    def test_unknown_ledger_gets_empty_accrues_string(self):
        result = evolution.compounding({"unknown_ledger": 3})
        entry = result["ledgers"]["unknown_ledger"]
        self.assertEqual(entry["count"], 3)
        self.assertEqual(entry["accrues"], "")

    def test_ledger_notes_are_non_empty_strings(self):
        for key, value in evolution.LEDGER_NOTES.items():
            self.assertIsInstance(key, str)
            self.assertIsInstance(value, str)
            self.assertTrue(value.strip(), f"LEDGER_NOTES['{key}'] should be non-empty")


if __name__ == "__main__":
    unittest.main()


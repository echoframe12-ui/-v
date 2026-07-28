"""Tests for friction.py — the honest (1-confidence) scrutiny term.

Covers:
  - High confidence → low friction, clear of bar, gap=0
  - Low confidence → high friction, held, gap calculated
  - Exactly at threshold → not below, gap=0
  - Just above threshold → some friction phrase
  - Clamping: >1.0, <0.0, None → clamped, never errors
  - Custom threshold override
  - friction + confidence = 1.0 (complementary)
  - threshold key present in return dict
  - Zero confidence is maximum friction (1.0)
  - confidence=1.0 → friction=0.0
  - note is always the 'measured — never charged' string
  - gap is 0.0 when above or at threshold
"""
import unittest

import friction
from attestation import CONFIDENCE_THRESHOLD


class FrictionReadingTests(unittest.TestCase):

    def test_high_confidence_is_low_friction_and_clear(self):
        r = friction.reading(0.95)
        self.assertEqual(r["friction"], 0.05)
        self.assertFalse(r["below_threshold"])
        self.assertEqual(r["gap"], 0.0)
        self.assertIn("clear of the bar", r["phrase"])
        self.assertIn("never charged", r["note"])

    def test_held_low_confidence_is_high_friction_with_the_gap(self):
        r = friction.reading(0.40)
        self.assertEqual(r["friction"], 0.60)
        self.assertTrue(r["below_threshold"])
        self.assertEqual(r["gap"], round(CONFIDENCE_THRESHOLD - 0.40, 2))
        self.assertIn("held", r["phrase"])
        self.assertIn("below the 0.74 bar", r["phrase"])

    def test_exactly_at_threshold_is_not_below(self):
        r = friction.reading(CONFIDENCE_THRESHOLD)
        self.assertFalse(r["below_threshold"])
        self.assertEqual(r["gap"], 0.0)

    def test_just_above_threshold_still_reads_some_friction(self):
        r = friction.reading(0.76)
        self.assertFalse(r["below_threshold"])
        self.assertIn("some friction", r["phrase"])

    def test_values_clamp_and_bad_input_is_max_friction(self):
        self.assertEqual(friction.reading(1.5)["friction"], 0.0)
        self.assertEqual(friction.reading(-1.0)["friction"], 1.0)
        self.assertEqual(friction.reading(None)["friction"], 1.0)

    def test_a_custom_threshold_is_honoured(self):
        r = friction.reading(0.80, threshold=0.90)
        self.assertTrue(r["below_threshold"])
        self.assertEqual(r["gap"], 0.10)

    def test_friction_and_confidence_are_complementary(self):
        for conf in (0.0, 0.25, 0.5, CONFIDENCE_THRESHOLD, 0.8, 1.0):
            r = friction.reading(conf)
            self.assertAlmostEqual(r["friction"] + conf, 1.0, places=5,
                                   msg=f"friction+confidence != 1.0 for confidence={conf}")

    def test_threshold_key_in_return_dict(self):
        r = friction.reading(0.8)
        self.assertIn("threshold", r)
        self.assertAlmostEqual(r["threshold"], CONFIDENCE_THRESHOLD, places=5)

    def test_zero_confidence_is_maximum_friction(self):
        r = friction.reading(0.0)
        self.assertEqual(r["friction"], 1.0)
        self.assertTrue(r["below_threshold"])

    def test_full_confidence_is_zero_friction(self):
        r = friction.reading(1.0)
        self.assertEqual(r["friction"], 0.0)
        self.assertFalse(r["below_threshold"])
        self.assertEqual(r["gap"], 0.0)

    def test_note_is_always_measured_never_charged(self):
        for conf in (0.0, 0.5, 1.0):
            r = friction.reading(conf)
            self.assertIn("measured", r["note"])
            self.assertIn("never charged", r["note"])

    def test_gap_is_zero_when_above_threshold(self):
        r = friction.reading(0.90)
        self.assertEqual(r["gap"], 0.0)


if __name__ == "__main__":
    unittest.main()


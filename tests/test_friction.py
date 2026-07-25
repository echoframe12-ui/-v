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


if __name__ == "__main__":
    unittest.main()

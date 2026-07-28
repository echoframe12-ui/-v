"""Tests for quotas.py — VaaS tier-based build quota enforcement.

Covers:
  - limit_for: known tiers, unknown tier falls back to DEFAULT_TIER limit
  - sovereign is unlimited (None)
  - quota_status: under, at, over for finite tier
  - sovereign is never exceeded with unlimited usage
  - is_tier: known and unknown tiers
  - quota_status carries window_seconds and resets_at fields
  - DEFAULT_TIER is 'attestor'
  - TIER_LIMITS has all 3 tiers
  - used=0 → remaining equals limit
  - quota_status.tier matches input tier
  - arbiter quota at boundary
  - WINDOW_SECONDS is positive integer
  - quota_status dict has all 7 required keys
"""
import unittest

import quotas


class LimitForTests(unittest.TestCase):

    def test_limit_for_known_and_unknown_tiers(self):
        self.assertEqual(quotas.limit_for("attestor"), 10)
        self.assertEqual(quotas.limit_for("arbiter"), 50)
        self.assertIsNone(quotas.limit_for("sovereign"))
        # unknown tier falls back to the default tier's limit
        self.assertEqual(quotas.limit_for("mystery"), quotas.limit_for(quotas.DEFAULT_TIER))

    def test_default_tier_is_attestor(self):
        self.assertEqual(quotas.DEFAULT_TIER, "attestor")

    def test_tier_limits_has_all_three_tiers(self):
        self.assertIn("attestor", quotas.TIER_LIMITS)
        self.assertIn("arbiter", quotas.TIER_LIMITS)
        self.assertIn("sovereign", quotas.TIER_LIMITS)

    def test_window_seconds_is_positive_integer(self):
        self.assertIsInstance(quotas.WINDOW_SECONDS, int)
        self.assertGreater(quotas.WINDOW_SECONDS, 0)


class IsTierTests(unittest.TestCase):

    def test_is_tier_for_known_tiers(self):
        for tier in ("attestor", "arbiter", "sovereign"):
            self.assertTrue(quotas.is_tier(tier), f"{tier} should be a valid tier")

    def test_is_tier_for_unknown_tier(self):
        self.assertFalse(quotas.is_tier("platinum"))
        self.assertFalse(quotas.is_tier(""))
        self.assertFalse(quotas.is_tier("mystery"))


class QuotaStatusTests(unittest.TestCase):

    def test_quota_status_under_at_and_over(self):
        under = quotas.quota_status("attestor", 3)
        self.assertEqual(under["remaining"], 7)
        self.assertFalse(under["exceeded"])

        at = quotas.quota_status("attestor", 10)
        self.assertEqual(at["remaining"], 0)
        self.assertTrue(at["exceeded"])

        over = quotas.quota_status("attestor", 12)
        self.assertEqual(over["remaining"], 0)
        self.assertTrue(over["exceeded"])

    def test_sovereign_is_unlimited(self):
        status = quotas.quota_status("sovereign", 9999)
        self.assertIsNone(status["limit"])
        self.assertIsNone(status["remaining"])
        self.assertFalse(status["exceeded"])

    def test_quota_status_carries_window_fields(self):
        scoped = quotas.quota_status(
            "attestor", 3, window_seconds=3600, resets_at="2026-01-01T00:00:00+00:00"
        )
        self.assertEqual(scoped["window_seconds"], 3600)
        self.assertEqual(scoped["resets_at"], "2026-01-01T00:00:00+00:00")

        bare = quotas.quota_status("attestor", 3)
        self.assertIsNone(bare["window_seconds"])
        self.assertIsNone(bare["resets_at"])

    def test_used_zero_gives_full_remaining(self):
        status = quotas.quota_status("attestor", 0)
        self.assertEqual(status["remaining"], quotas.limit_for("attestor"))
        self.assertFalse(status["exceeded"])

    def test_tier_key_matches_input_tier(self):
        for tier in ("attestor", "arbiter", "sovereign"):
            status = quotas.quota_status(tier, 0)
            self.assertEqual(status["tier"], tier)

    def test_arbiter_at_limit_boundary(self):
        at_limit = quotas.quota_status("arbiter", 50)
        self.assertEqual(at_limit["remaining"], 0)
        self.assertTrue(at_limit["exceeded"])

        one_under = quotas.quota_status("arbiter", 49)
        self.assertEqual(one_under["remaining"], 1)
        self.assertFalse(one_under["exceeded"])

    def test_quota_status_dict_has_all_seven_keys(self):
        status = quotas.quota_status("attestor", 5)
        expected_keys = {"tier", "limit", "used", "remaining", "exceeded", "window_seconds", "resets_at"}
        self.assertEqual(set(status.keys()), expected_keys)


if __name__ == "__main__":
    unittest.main()


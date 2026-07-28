"""Tests for requestlog.py — request tracing and structured access logging.

Covers:
  - clean_request_id: mints 16-char hex on None, preserves valid id
  - Strips log injection characters (newlines, spaces, tabs)
  - Caps length at 64 chars
  - All-invalid input falls back to minted id
  - Minted id is valid hex (lowercase)
  - Special chars (dots, dashes, underscores) preserved
  - Empty string treated like None → minted
  - access_record: shape, actor=None, latency as float
  - access_record keys are exactly the 6 expected
  - method is preserved as-given (caller responsibility)
"""
import unittest

import requestlog


class CleanRequestIdTests(unittest.TestCase):

    def test_mints_an_id_when_absent(self):
        rid = requestlog.clean_request_id(None)
        self.assertTrue(rid)
        self.assertEqual(len(rid), 16)

    def test_preserves_a_valid_id(self):
        self.assertEqual(requestlog.clean_request_id("trace-abc.123_XYZ"), "trace-abc.123_XYZ")

    def test_strips_log_injection_characters(self):
        # newlines / spaces / control chars must not survive into the log line
        rid = requestlog.clean_request_id("abc\n injected LINE\t123")
        self.assertNotIn("\n", rid)
        self.assertNotIn(" ", rid)
        self.assertEqual(rid, "abcinjectedLINE123")

    def test_caps_length(self):
        self.assertEqual(len(requestlog.clean_request_id("x" * 500)), 64)

    def test_all_invalid_falls_back_to_a_minted_id(self):
        rid = requestlog.clean_request_id("\n\n   \t")
        self.assertEqual(len(rid), 16)  # sanitized to empty → minted

    def test_minted_id_is_lowercase_hex(self):
        rid = requestlog.clean_request_id(None)
        # uuid4().hex is lowercase hexadecimal
        int(rid, 16)  # must parse as hex without error
        self.assertEqual(rid, rid.lower())

    def test_special_chars_dots_dashes_underscores_preserved(self):
        rid = requestlog.clean_request_id("req-id_1.2.3")
        self.assertEqual(rid, "req-id_1.2.3")

    def test_empty_string_is_treated_like_none(self):
        rid = requestlog.clean_request_id("")
        self.assertEqual(len(rid), 16)


class AccessRecordTests(unittest.TestCase):

    def test_record_shape(self):
        rec = requestlog.access_record("rid1", "GET", "/cvi", 200, "alice", 12.5)
        self.assertEqual(
            rec,
            {
                "request_id": "rid1",
                "method": "GET",
                "path": "/cvi",
                "status": 200,
                "actor": "alice",
                "latency_ms": 12.5,
            },
        )

    def test_actor_can_be_none(self):
        rec = requestlog.access_record("rid2", "POST", "/attestations", 201, None, 7.3)
        self.assertIsNone(rec["actor"])
        self.assertEqual(rec["status"], 201)

    def test_latency_ms_preserved_as_float(self):
        rec = requestlog.access_record("rid3", "GET", "/health", 200, None, 0.123)
        self.assertAlmostEqual(rec["latency_ms"], 0.123, places=5)

    def test_access_record_has_exactly_six_keys(self):
        rec = requestlog.access_record("rid4", "DELETE", "/x", 204, None, 1.0)
        self.assertEqual(
            set(rec.keys()),
            {"request_id", "method", "path", "status", "actor", "latency_ms"},
        )

    def test_method_is_preserved_as_given(self):
        rec = requestlog.access_record("r", "PATCH", "/y", 200, None, 0.0)
        self.assertEqual(rec["method"], "PATCH")


if __name__ == "__main__":
    unittest.main()


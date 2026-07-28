"""Tests for anchor.py — The Anchor of Last Resort (2019 offline dataset).

Covers:
  - Anchor file presence and row count (365 rows)
  - Recorded sha256 matches recomputed body sha256 (integrity_ok)
  - Lookup returns correct 2019 weekdays cross-checked with stdlib calendar
  - Missing/invalid date returns None
  - Absent anchor file reports present: False without raising
  - Tampered anchor body fails integrity (integrity_ok: False)
  - anchor_line on missing anchor file returns None
  - load_anchor dict contains expected keys (present, source, rows, sha256, integrity_ok, header)
  - load_anchor source path matches input or default
"""
import calendar
import hashlib
import os
import tempfile
import unittest

import anchor
try:
    from tests.test_helpers import safe_remove
except ImportError:
    from test_helpers import safe_remove


class AnchorTests(unittest.TestCase):

    def test_the_anchor_file_ships_and_is_present(self):
        state = anchor.load_anchor()
        self.assertTrue(state["present"])
        self.assertEqual(state["rows"], 365)  # 2019 is not a leap year

    def test_recorded_sha256_matches_the_body(self):
        # the header records the sha256 of the body; load_anchor recomputes it
        state = anchor.load_anchor()
        self.assertTrue(state["integrity_ok"])

    def test_lookup_returns_the_correct_2019_weekday(self):
        # cross-check a few dates against the stdlib calendar
        names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for month, day in ((1, 1), (7, 4), (12, 25)):
            row = anchor.anchor_line(f"2019-{month:02d}-{day:02d}")
            self.assertIsNotNone(row)
            expected = names[calendar.weekday(2019, month, day)]
            self.assertIn(expected, row)

    def test_missing_date_returns_none(self):
        self.assertIsNone(anchor.anchor_line("2019-13-40"))

    def test_absent_anchor_reports_not_present_without_raising(self):
        path = tempfile.mktemp(suffix=".txt")
        state = anchor.load_anchor(path=path)
        self.assertFalse(state["present"])
        self.assertEqual(state["source"], path)

    def test_anchor_line_on_missing_file_returns_none(self):
        path = tempfile.mktemp(suffix=".txt")
        self.assertIsNone(anchor.anchor_line("2019-01-01", path=path))

    def test_tampered_anchor_fails_integrity(self):
        handle = tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode="w")
        good_body = "2019-01-01\tTue\tJanuary\n"
        sha = hashlib.sha256(good_body.encode()).hexdigest()
        # record a sha for the good body, then write a different body
        handle.write(f"sha256: {sha}\n---\n2019-01-01\tWed\tJanuary\n")
        handle.close()
        try:
            from pathlib import Path

            state = anchor.load_anchor(path=Path(handle.name))
            self.assertTrue(state["present"])
            self.assertFalse(state["integrity_ok"])
        finally:
            safe_remove(handle.name)

    def test_load_anchor_dict_keys(self):
        state = anchor.load_anchor()
        expected_keys = {"present", "source", "rows", "sha256", "integrity_ok", "header"}
        self.assertEqual(set(state.keys()), expected_keys)

    def test_anchor_path_constant_exists(self):
        self.assertTrue(anchor.ANCHOR_PATH.name.endswith(".txt"))


if __name__ == "__main__":
    unittest.main()


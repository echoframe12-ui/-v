"""Tests for adr.py — Architecture Decision Records at runtime.

Covers:
  - list_adr(): ordered by number, titles stripped, filenames present
  - get_adr(): full content with ## sections, missing returns None
  - Custom directory override for list_adr and get_adr
  - Empty directory returns empty list
  - Non-numeric .md files are excluded
  - _title() strips heading markers correctly
"""
import re
import tempfile
import unittest
from pathlib import Path

import adr


_HEADING_PATTERN = re.compile(r"^\d+-.+\.md$")


def _write_adr(directory: Path, number: int, slug: str, content: str) -> None:
    filename = f"{number:04d}-{slug}.md"
    (directory / filename).write_text(content, encoding="utf-8")


class AdrLiveTests(unittest.TestCase):
    """Tests against the real DECISIONS/ directory."""

    def test_lists_all_records_in_order(self):
        records = adr.list_adr()
        self.assertGreaterEqual(len(records), 30)
        numbers = [r["number"] for r in records]
        self.assertEqual(numbers, sorted(numbers))
        self.assertEqual(numbers[0], 1)

    def test_each_record_has_a_title(self):
        for record in adr.list_adr():
            self.assertTrue(record["title"])
            self.assertNotIn("#", record["title"])  # heading stripped

    def test_title_strips_the_number_prefix(self):
        # 0001 heading is "# Decision 0001: Adopt the Validated Hesitation ..."
        first = adr.get_adr(1)
        self.assertNotIn("0001", first["title"])
        self.assertNotIn("Decision", first["title"].split()[0])
        self.assertIn("Hesitation", first["title"])

    def test_get_returns_full_content(self):
        record = adr.get_adr(12)  # signed checkpoints
        self.assertEqual(record["number"], 12)
        self.assertIn("## Context", record["content"])
        self.assertIn("checkpoint", record["content"].lower())

    def test_missing_number_returns_none(self):
        self.assertIsNone(adr.get_adr(9999))

    def test_each_record_has_filename_key(self):
        for record in adr.list_adr():
            self.assertIn("filename", record)
            self.assertRegex(record["filename"], r"^\d+-.+\.md$")


class AdrCustomDirectoryTests(unittest.TestCase):
    """Tests using a temporary isolated directory."""

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.d = Path(self._tmpdir.name)

    def tearDown(self):
        self._tmpdir.cleanup()

    def test_list_adr_with_custom_directory(self):
        _write_adr(self.d, 1, "first-decision", "# First Decision\n\n## Context\nSome context.")
        _write_adr(self.d, 2, "second-decision", "# Second Decision\n\n## Context\nMore context.")
        records = adr.list_adr(self.d)
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]["number"], 1)
        self.assertEqual(records[1]["number"], 2)

    def test_empty_directory_returns_empty_list(self):
        self.assertEqual(adr.list_adr(self.d), [])

    def test_get_adr_with_custom_directory(self):
        _write_adr(self.d, 5, "custom-decision", "# Custom Decision\n\n## Context\nContext here.\n\n## Decision\nDone.")
        record = adr.get_adr(5, self.d)
        self.assertIsNotNone(record)
        self.assertEqual(record["number"], 5)
        self.assertIn("## Context", record["content"])
        self.assertEqual(record["filename"], "0005-custom-decision.md")

    def test_get_adr_missing_in_custom_directory_returns_none(self):
        _write_adr(self.d, 1, "only-one", "# Only One\n")
        self.assertIsNone(adr.get_adr(99, self.d))

    def test_non_numeric_md_files_are_excluded(self):
        _write_adr(self.d, 1, "valid", "# Valid\n")
        (self.d / "README.md").write_text("# Not an ADR\n", encoding="utf-8")
        (self.d / "template.md").write_text("# Template\n", encoding="utf-8")
        records = adr.list_adr(self.d)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["number"], 1)

    def test_title_without_heading_uses_slug_fallback(self):
        _write_adr(self.d, 3, "slug-fallback", "No heading here, just body text.")
        records = adr.list_adr(self.d)
        self.assertEqual(len(records), 1)
        # Falls back to slug with hyphens replaced by spaces
        self.assertEqual(records[0]["title"], "slug fallback")


if __name__ == "__main__":
    unittest.main()


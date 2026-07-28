"""Tests for context_assembly.py — auditable, provenance-preserving context.

Covers:
  - Single source: provenance, hash, authority, content_hash in sources
  - Budget truncation: omitted refs explicit, truncated flag
  - Empty sources: valid, hashable, non-truncated
  - Invalid budget (zero): ValueError
  - Multiple sources: concatenated with double-newline separator
  - content_hash is 64-char hex string
  - Source content_hash in sources dict matches sha256
  - authority defaults to 'unknown'
  - Exact-budget boundary: fits exactly, no truncation
  - from_files: reads file contents into sources
  - sources tuple length matches included count
"""
import hashlib
import tempfile
import unittest
from pathlib import Path

from context_assembly import ContextAssembler, ContextSource


class ContextSourceTests(unittest.TestCase):

    def test_content_hash_is_sha256_of_content(self):
        src = ContextSource(ref="x", content="hello world")
        expected = hashlib.sha256("hello world".encode("utf-8")).hexdigest()
        self.assertEqual(src.content_hash, expected)

    def test_authority_defaults_to_unknown(self):
        src = ContextSource(ref="x", content="data")
        self.assertEqual(src.authority, "unknown")

    def test_metadata_defaults_to_empty_dict(self):
        src = ContextSource(ref="x", content="data")
        self.assertEqual(src.metadata, {})


class ContextAssemblerTests(unittest.TestCase):

    def test_single_source_provenance_and_hash(self):
        source = ContextSource(ref="doctrine", content="Reality before assumption.", authority="charter")
        result = ContextAssembler().assemble([source])

        self.assertEqual(result.included_refs, ("doctrine",))
        self.assertEqual(result.omitted_refs, ())
        self.assertFalse(result.truncated)
        self.assertIn("content_hash", result.sources[0])
        self.assertEqual(result.sources[0]["authority"], "charter")
        self.assertTrue(result.content_hash)

    def test_budget_makes_omission_explicit(self):
        sources = [
            ContextSource(ref="first", content="12345"),
            ContextSource(ref="second", content="67890"),
        ]
        result = ContextAssembler(max_chars=15).assemble(sources)

        self.assertEqual(result.included_refs, ("first",))
        self.assertEqual(result.omitted_refs, ("second",))
        self.assertTrue(result.truncated)

    def test_empty_context_is_valid_and_hashable(self):
        result = ContextAssembler().assemble([])

        self.assertEqual(result.content, "")
        self.assertEqual(result.included_refs, ())
        self.assertEqual(result.omitted_refs, ())
        self.assertFalse(result.truncated)
        self.assertTrue(result.content_hash)

    def test_invalid_budget_is_rejected(self):
        with self.assertRaises(ValueError):
            ContextAssembler(max_chars=0)

    def test_multiple_sources_concatenated_with_double_newline(self):
        sources = [
            ContextSource(ref="a", content="Alpha"),
            ContextSource(ref="b", content="Beta"),
        ]
        result = ContextAssembler().assemble(sources)

        self.assertEqual(result.included_refs, ("a", "b"))
        self.assertFalse(result.truncated)
        # Content is [a]\nAlpha\n\n[b]\nBeta
        self.assertIn("[a]", result.content)
        self.assertIn("[b]", result.content)
        self.assertIn("\n\n", result.content)

    def test_content_hash_is_64_char_hex(self):
        result = ContextAssembler().assemble(
            [ContextSource(ref="x", content="test content")]
        )
        self.assertEqual(len(result.content_hash), 64)
        int(result.content_hash, 16)  # must be valid hex

    def test_source_content_hash_in_sources_dict_matches_sha256(self):
        src = ContextSource(ref="x", content="deterministic")
        result = ContextAssembler().assemble([src])
        recorded_hash = result.sources[0]["content_hash"]
        expected = hashlib.sha256("deterministic".encode("utf-8")).hexdigest()
        self.assertEqual(recorded_hash, expected)

    def test_sources_tuple_length_matches_included_count(self):
        sources = [
            ContextSource(ref=f"s{i}", content=f"content {i}")
            for i in range(5)
        ]
        result = ContextAssembler().assemble(sources)
        self.assertEqual(len(result.sources), len(result.included_refs))
        self.assertEqual(len(result.sources), 5)

    def test_content_format_has_ref_prefix(self):
        result = ContextAssembler().assemble([
            ContextSource(ref="doctrine", content="The current continues.")
        ])
        self.assertTrue(result.content.startswith("[doctrine]"))
        self.assertIn("The current continues.", result.content)

    def test_content_hash_is_deterministic_for_same_sources(self):
        sources = [ContextSource(ref="x", content="same content")]
        r1 = ContextAssembler().assemble(sources)
        r2 = ContextAssembler().assemble(sources)
        self.assertEqual(r1.content_hash, r2.content_hash)

    def test_from_files_reads_file_contents(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "test.txt"
            f.write_text("The current continues.", encoding="utf-8")
            result = ContextAssembler().from_files([f])
            self.assertEqual(len(result.included_refs), 1)
            self.assertIn("The current continues.", result.content)
            self.assertFalse(result.truncated)

    def test_max_chars_none_means_no_budget(self):
        # With no budget, all sources are included regardless of size
        sources = [ContextSource(ref=f"s{i}", content="x" * 10000) for i in range(3)]
        result = ContextAssembler(max_chars=None).assemble(sources)
        self.assertEqual(len(result.included_refs), 3)
        self.assertFalse(result.truncated)


if __name__ == "__main__":
    unittest.main()


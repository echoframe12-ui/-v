"""Tests for report.py — trust report rendering.

Covers:
  - render() includes posture, chain, CVI, source coverage, dissent
  - at-peak note when cvi equals cvi_peak
  - broken chain and missing seal/audit
  - held queue rendering
  - generated_at and threshold in header
  - ledger table rows from footprint
  - report contains 'Exit 0. Continues'
"""
import unittest

import report


SNAPSHOT = {
    "posture": "TRUSTWORTHY",
    "verify": {"intact": True, "trustworthy": True, "length": 4},
    "cvi": {"cvi": 0.80, "confidence_interval": [0.61, 0.94]},
    "cvi_peak": 0.95,
    "sourced_ratio": 0.75,
    "held_pending": 1,
    "held_breached": 0,
    "checkpoint": {"length": 4, "created_at": "2026-07-23T00:00:00+00:00"},
    "audit": {"intact": True, "checked_at": "2026-07-23T00:00:00+00:00"},
    "threshold": 0.74,
    "generated_at": "2026-07-23T00:00:00+00:00",
}
FOOTPRINT = {
    "ledgers": {"attestations": {"count": 4}, "decisions": {"count": 60}},
    "records_total": 64,
    "ledger_count": 2,
}
DISSENT = {"evaluations": 4, "dissent_rate": 1.0, "mean_dissent_score": 0.25}


class ReportRenderTests(unittest.TestCase):

    def test_renders_posture_and_signals(self):
        text = report.render(SNAPSHOT, FOOTPRINT, DISSENT)
        self.assertIn("# OceanicOS Trust Report", text)
        self.assertIn("## Posture: TRUSTWORTHY", text)
        self.assertIn("intact · 4 links · sealed head reproduced & signed", text)
        # CVI with the confidence spread and the regression note
        self.assertIn("0.80 · confidence 0.61–0.94 · peak 0.95 (▼0.15)", text)
        self.assertIn("Source coverage | 75%", text)
        self.assertIn("rate 100% · mean split 0.25", text)
        self.assertIn("64 records across 2 append-only ledgers", text)
        self.assertIn("Exit 0. Continues", text)

    def test_at_peak_when_no_drop(self):
        snap = {**SNAPSHOT, "cvi_peak": 0.80}
        self.assertIn("at peak", report.render(snap, FOOTPRINT, DISSENT))

    def test_broken_chain_and_missing_seal(self):
        snap = {
            **SNAPSHOT,
            "posture": "BROKEN",
            "verify": {"intact": False, "broken_at": 2, "length": 4},
            "checkpoint": None,
            "audit": None,
        }
        text = report.render(snap, FOOTPRINT, DISSENT)
        self.assertIn("## Posture: BROKEN", text)
        self.assertIn("BROKEN at #2", text)
        self.assertIn("none sealed yet", text)
        self.assertIn("none recorded yet", text)

    def test_held_queue_rendering(self):
        text = report.render(SNAPSHOT, FOOTPRINT, DISSENT)
        self.assertIn("1 pending · 0 past SLA", text)

    def test_generated_at_and_threshold_in_header(self):
        text = report.render(SNAPSHOT, FOOTPRINT, DISSENT)
        self.assertIn("2026-07-23T00:00:00+00:00", text)
        self.assertIn("threshold 0.74", text)

    def test_ledger_table_rows(self):
        text = report.render(SNAPSHOT, FOOTPRINT, DISSENT)
        self.assertIn("attestations | 4", text)
        self.assertIn("decisions | 60", text)

    def test_intact_not_trustworthy_chain(self):
        snap = {**SNAPSHOT, "verify": {"intact": True, "length": 3}}
        text = report.render(snap, FOOTPRINT, DISSENT)
        self.assertIn("not yet sealed to trustworthy", text)


if __name__ == "__main__":
    unittest.main()


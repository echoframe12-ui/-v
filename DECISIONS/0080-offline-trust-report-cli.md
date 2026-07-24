# 0080 — Offline Trust Report CLI

## Context

"The ground truth survives the system" is the platform's principle, and its
machine-facing tools honour it: `oceanic-os verify`, `gate`, and `digest` all read
the local ledger and produce their answer with no service running. The *human*
trust report — the composed Markdown a stakeholder reads or attaches to a release —
was the exception. It existed only as `/report`, a live endpoint. To get the one
document a person actually reads, you had to boot the whole Flask app.

That is backwards for the surface most likely to be wanted in a cron job, a CI
summary, or a nightly artifact — none of which want a running server. The readable
report should survive the system exactly as the verifiable record does.

## Decision

Add `oceanic-os report` — the human trust report, rendered offline from the ledger.

- The command assembles the same inputs `/report` passes to `report.render`: a
  posture snapshot (`_offline_snapshot`), the compounding footprint
  (`evolution.compounding` over `_offline_ledger_counts`), and the dissent stats
  (`ConsensusLog.stats`) — all read straight from the configured database, with no
  Flask and no engine singletons.
- `_offline_snapshot` mirrors the app's `_status_snapshot` for exactly the fields
  the renderer reads (posture, chain, CVI and its peak, source coverage, held queue,
  checkpoint, last audit, threshold), crediting released held items to the CVI just
  as the service does, so the offline report says what the page would for the same
  ledger.
- `_offline_ledger_counts` mirrors the app's `_ledger_counts` across all eight
  append-only ledgers; `decisions` counts the ADRs present on disk, so a bare
  database with no repo checkout honestly reports none rather than inventing a
  figure.

## Consequences

- The human report now survives the system: verified live, a ledger seeded directly
  (no service) renders a complete report — `Posture: TRUSTWORTHY`, `intact · 3 links
  · sealed head reproduced & signed`, CVI, dissent, held queue, and the eight-ledger
  compounding footprint — from `oceanic-os report` alone. Cron and CI can attach a
  readable trust summary without booting the app.
- The CLI trust surface is now complete and symmetrical: `verify` (chain), `gate`
  (policy), `digest` (signed posture), and `report` (the human page) all work
  offline from the same database, so the operator has the machine *and* the human
  view without a service.
- One renderer, no drift: the command reuses the very `report.render`,
  `evolution.compounding`, and `ConsensusLog.stats` the endpoint uses, and its
  snapshot and ledger-count helpers mirror the app's field for field, so the offline
  document and the served page describe the same ledger the same way. A test asserts
  both carry the same report structure.
- Honest about what a bare database holds: counts that depend on the repo (the ADR
  decision log) reflect what is actually on disk, and derived posture is recomputed
  from the ledger rather than trusted from a stored summary — the report states only
  what the local ground truth can support.

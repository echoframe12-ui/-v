# 0087 — The Evolution Growth History

## Context

*Continuous Becoming* is the platform's stated invariant, and `/evolution` reports the
compounding footprint — how many records the append-only ledgers hold. But it reports
only the total *now*. "The histories compound" was a claim the platform asserted at a
single instant, not a trajectory anyone could watch. The CVI already has a time series
(`cvi_history`) precisely because a headline number with no memory can't show whether
things are moving; the footprint deserved the same treatment, since growth over time
is the literal content of the invariant.

## Decision

Add an append-only history of the footprint's `records_total`, and expose the curve.

- `evolution_history.py` (mirroring `cvi_history.py`): `EvolutionHistory` records the
  `records_total` at each evolution point, **change-only** (`record_if_changed`), so
  the series is real growth rather than a log of identical reads. `growth()` summarizes
  it — first, latest, gain, and the number of points.
- Recorded from `_snapshot_cvi`, which already fires at the moments the record moves —
  a build and a held-review decision — so the trajectory captures the same evolution
  points the CVI trend does, from one hook.
- `GET /evolution/history` returns the `history` series (oldest-first, `?limit=`
  capped) and the `growth` summary. Public and aggregate — totals only, no per-record
  content, like `/evolution` and `/metrics`.
- The growth ledger is deliberately **kept out of `_ledger_counts`**, so recording a
  growth point never changes the total it measures — the observer that does not
  interrupt what it observes, and no feedback loop where a snapshot inflates the next.

## Consequences

- "The histories compound" is now a curve, not a claim: verified live, three builds
  move the trajectory `90 → 94 → 98` with `growth {first 90, latest 98, gain 8, points
  3}`, and the latest point equals the current `/evolution` `records_total` exactly —
  the trend and the snapshot agree. Reading the footprint while nothing new happens
  adds no points, so the series stays a record of real growth.
- The invariant is observable, not asserted: an operator can now answer "is the record
  actually compounding, and how fast" from the platform itself, the same way the CVI
  history answers "is verification quality moving." Continuous Becoming has a shape.
- Consistent by construction: the trajectory's total is the same `records_total`
  `/evolution` reports (`sum(_ledger_counts().values())`), so the curve and the
  footprint can never diverge, and keeping the growth ledger outside the counted
  footprint keeps the measurement honest — it watches the compounding without becoming
  part of it.
- Additive: a new pure ledger and one endpoint, recorded from the existing snapshot
  hook. No new state on any existing surface, and nothing existing changes behaviour.

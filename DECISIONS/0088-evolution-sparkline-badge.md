# 0088 — The Evolution Sparkline Badge

## Context

Round 87 (`DECISIONS/0087`) turned the compounding footprint into a trajectory
(`/evolution/history`) — the record's growth over time, not just its total now. The
badge family (`DECISIONS/0071`, `0084`) makes trust embeddable, but every badge so far
shows a single *value*: a CVI, a posture, one record's verdict. None shows *movement*.
Continuous Becoming is a shape, and the platform could not yet hand a README that
shape.

## Decision

Add `GET /badge/evolution.svg` — the growth trajectory as an embeddable sparkline.

- `badge.sparkline(values, label="records")` renders a compact trend badge in the same
  frame as the flat badges: a grey `label N` cell (the latest total) beside a
  normalized polyline of the series, with a dot at the current point. Deterministic
  geometry so the SVG is byte-stable for caching, and all points are normalized into
  the badge's height so any range fits.
- The route reads `evolution_history.list(limit=…)` (default 30 points), draws the
  `records_total` series, and sends it no-cache. `?label=` overrides the word,
  `?limit=` the point count.
- An empty series renders a flat baseline and `records 0` — honest about having no
  trajectory yet, never a fabricated shape.

## Consequences

- Continuous Becoming is now embeddable: verified live and by screenshot, seven builds
  produce a `records 115` badge with a green upward line (the footprint compounding
  `91 → 115`), sitting naturally beside the CVI and posture badges. A README can show,
  at a glance, that the record is growing — not just claim it.
- The badge family now spans value *and* movement: CVI (an index), posture (a verdict),
  per-attestation (one record), and evolution (the trajectory). Between them they cover
  every headline the platform reports, each as a self-contained SVG with no external
  service.
- Honest by construction, like the rest of the family: the sparkline is the recorded
  `records_total` series and nothing else — normalized to fit, never smoothed or
  extrapolated — and an empty history shows a flat line and a zero rather than an
  invented curve.
- Additive and presentation-only: one pure renderer (`badge.sparkline`) and one route
  over the existing growth history. No new state, and no change to any existing badge
  or endpoint.

# 0071 — Trust Posture Badge

## Context

Round 42 (`DECISIONS/0042`) made the CVI embeddable — a live SVG badge a README can
show. But the CVI is only one axis: an index can read a middling number while the
*record* is fully trustworthy, or read high while the chain is broken. The
whole-record verdict — `TRUSTWORTHY` / `INTACT` / `BROKEN`, the thing the status
board and the signed digest headline — had no embeddable form. A repo could pin
its confidence number but not its integrity posture.

## Decision

Add `GET /badge/posture.svg` — the posture verdict as an SVG badge.

- `badge.posture_color` maps the verdict to a colour: `TRUSTWORTHY` green,
  `INTACT` amber, `BROKEN` red, anything else grey.
- The endpoint computes the posture with `status_digest.posture_of` — the same
  function the board, the JSON twin, and the digest use — and renders the badge
  with the verdict lowercased in the value cell. `?label=` overrides the left cell;
  sent `no-cache` so an embed is never stale, like the CVI badge.

## Consequences

- The record's integrity posture is now embeddable beside its index: verified live,
  an unsealed record renders `intact` in amber, and after a checkpoint the same
  record renders `trustworthy` in green — the exact verdict the board shows, in a
  form a README can pin.
- CVI badge and posture badge are complementary, not redundant: the first answers
  "how confident is the record?", the second "is the record intact and sealed?".
  Together they say what a single badge cannot — a repo can show `verification:
  0.62` (a middling index) beside `verification: trustworthy` (a sound chain), which
  is the honest two-axis reading the platform makes everywhere.
- The verdict comes from the one shared `posture_of`, so the badge cannot disagree
  with the status board, the digest, or the terminal's `/status` — one definition
  of the verdict, rendered in one more place. No new state.
- It reads the same truth even when unflattering: a broken chain renders `broken`
  in red, not a hidden failure. A posture badge that could only be green would be
  the false certainty this platform refuses — the same discipline the CVI badge was
  built on.

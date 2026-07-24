# 0084 — Per-Attestation Proof Badge

## Context

The platform serves two embeddable SVG badges (`DECISIONS/0071`): `/badge/cvi.svg`
and `/badge/posture.svg`. Both describe the *whole record* — the aggregate index and
the aggregate verdict. Neither can vouch for a *single output*. A customer who runs a
specific artifact through the platform and wants to show "this exact output is
verified" — beside it in their docs, a PR, a dashboard — had nothing to embed. The
receipt proves one record, but it is JSON for a verifier, not a glanceable badge for
a reader.

## Decision

Add `GET /badge/attestation/<id>.svg` — one attestation's verdict as an embeddable
badge.

- A pure `badge.attestation_message(receipt)` maps a record's receipt to a message
  and colour: an **attested** record is green with its confidence (`attested 0.95`);
  a **held** record takes the threshold-aligned `cvi_color` of its confidence
  (`held 0.61` yellow, `held 0.35` red) so a below-`0.74` item never reads green; and
  a **tampered** entry — one whose `entry_intact` or `chain_intact` is false — reads
  red as `tampered` regardless of confidence, because the proof is void.
- The route computes the badge from the same `attestation_engine.receipt(id)` the
  receipt endpoint serves, so the badge cannot read green for a record the receipt
  would flag. `?label=` overrides the left cell (e.g. `verified output`). A missing id
  returns a grey `not found` badge with a 404 — honest about the id, and still a
  meaningful image if rendered.

## Consequences

- Proof is now per-output and glanceable: verified live, an attested record renders
  `attested 0.96` in green, a held record `held 0.61` in yellow and `held 0.35` in
  red, and a missing id a grey `not found` at 404 — each pinned beside the specific
  thing it vouches for. The badge family now spans the whole record (CVI, posture)
  and a single record (this).
- The badge tells the same truth as the receipt, by construction. It is derived from
  the receipt, not a separate computation, so it steps down in colour exactly where
  confidence does and turns red the moment the entry or chain no longer verifies — it
  can never present an unverified or tampered record as green.
- Honest about voidness: a tampered entry is not shown with a stale confidence that
  might still look reassuring; it reads `tampered` red, because a broken proof has no
  trustworthy confidence to report.
- Additive and presentation-only: one route and one pure helper over the existing
  receipt, reusing `badge.render`/`cvi_color`. No new state, no change to any existing
  badge or endpoint.

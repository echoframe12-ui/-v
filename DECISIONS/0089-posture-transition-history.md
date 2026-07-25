# 0089 — Posture Transition History

## Context

Two of the platform's three headline signals had a memory: the CVI over time
(`cvi_history`, `/cvi/history`) and the compounding footprint over time
(`evolution_history`, `/evolution/history`). The third — the **posture verdict**
(`TRUSTWORTHY` / `INTACT` / `BROKEN`), the single most operationally important
signal — had none. The drift-audit trail records every integrity check
(`intact`/`trustworthy`/`length`), but it logs *every look*, not the moments the
verdict *changed*, so "when did trust go BROKEN, and when was it sealed back" meant
reading a wall of near-identical audit rows. The most important question about trust
over time was the one the platform answered least directly.

## Decision

Add `GET /posture/history` — the posture verdict's transitions, **derived** from the
existing drift-audit trail, with no new ledger.

- `status_digest.transitions(audits)` (pure, oldest-first) maps each audit to its
  posture via the existing `posture_of` — which already reads an audit's
  `intact`/`trustworthy` fields — and collapses runs of the same verdict into the
  change-points: `{from, to, at, length, audit_id}`, with `from` null at the first
  observed posture.
- The endpoint reads `drift_audit_log.list(limit=…)`, reverses to oldest-first, and
  returns `current` (the live verdict), the `transitions`, and how many audits were
  considered. Public and aggregate, like the other histories.

## Consequences

- The third signal now has a memory, and it is the audit-observed truth: verified
  live, sealing then tampering the chain produces the exact timeline
  `null → INTACT → TRUSTWORTHY → BROKEN`, each change pinned to the audit that
  observed it, with `current: BROKEN`. An operator can answer "when did trust change
  state" from one call instead of scanning the audit log.
- Derived, not duplicated: the transitions come from the drift-audit trail the
  platform already keeps, so there is no second source of truth to drift from the
  first, and no new state to maintain. It is honestly "the posture the record's own
  audits saw" — transitions are observed when the chain is looked at, consistent with
  the drift-audit principle that *drift is caught by looking*.
- Reuses the one posture definition: `posture_of` is the single place the three-way
  verdict is decided (status board, digest, badge), and the transition history reads
  it too, so the timeline can never disagree with the live posture about what
  `TRUSTWORTHY`/`INTACT`/`BROKEN` mean.
- The time-series trio is complete: index (`/cvi/history`), footprint
  (`/evolution/history`), and now verdict (`/posture/history`) — each headline signal
  is watchable over time, not just readable at an instant.
- Additive and presentation-only: one pure function beside `posture_of` and one
  endpoint over the existing audit trail. No new ledger, no new recording hook, and
  nothing existing changed.

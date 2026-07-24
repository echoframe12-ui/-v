# 0074 — Record Build-Time Dissent

## Context

Round 58 (`DECISIONS/0058`) made dissent data — a persistent ledger of panel
evaluations, keyed on the axiom *dissent is data*. But it only recorded explicit
`/models/consensus` calls. Every `/builder/run` also convenes the panel — the
build's `consensus` result carries the same adapters, verdicts, and majority — and
that disagreement was computed, returned, and then dropped on the floor. The most
common way the panel actually runs (a build) was the one way its dissent was never
kept. The ledger was systematically blind to the disagreement that happens where
work is actually done.

## Decision

Record the build's panel evaluation in the dissent ledger too.

- `/builder/run` now calls `consensus_log.record(task, result["consensus"])` after
  the build, when the result carries a `consensus` dict — the same recording path
  `/models/consensus` uses, so build-time and explicit evaluations land in one
  ledger with the same shape (prompt hashed, never stored raw).
- Guarded by an `isinstance(..., dict)` check so a build without a consensus result
  simply records nothing.

## Consequences

- The dissent ledger is now complete: verified live, three builds move the ledger
  from `0` to `3` evaluations with `dissent_rate 1.0` and `mean_dissent_score
  0.25`, each entry carrying the build's majority, dissent flag, and score with the
  task hashed. The disagreement that occurs during real work is now trended and
  observable (`/consensus/history`, `/consensus/stats`, `oceanicos_dissent_rate`)
  exactly like an explicit panel call.
- One recording path, one shape: build-time dissent goes through the same
  `consensus_log.record` as `/models/consensus`, so the two sources cannot produce
  divergent entries, and the same privacy guarantee holds — only the SHA-256 of the
  task is stored, so recording build dissent never exposes what was built.
- The axiom is now honoured where it matters most. *Dissent is data* was true for
  the endpoint a user calls to inspect the panel, but false for the endpoint that
  actually produces the record; this closes that gap so the platform keeps its
  primary signal from its primary action, not only from a diagnostic call.
- No new state or endpoint — the ledger and its recorder already existed; this only
  feeds them from the build path. The change is one guarded call at the point the
  build's consensus is already in hand.

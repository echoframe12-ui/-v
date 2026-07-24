# 0076 — Gate on Dissent (Opt-In)

## Context

Two rounds built the dissent signal into a first-class, portable fact:
`DECISIONS/0074` recorded build-time dissent in the ledger, and `DECISIONS/0075`
put the dissent rate inside the signed status digest. The signal is now recorded,
aggregated, exposed on `/metrics`, rendered in the trust report, and attested. The
one place it did not yet reach is the place trust decisions are actually enforced:
the CI trust gate (`oceanic-os gate`).

The gate is the platform's policy boundary — it fails a build when integrity, seal,
confidence, evidence, or process regresses. It read six dimensions and never looked
at how split the panel had been, even though a fracturing panel is exactly the kind
of trust regression a release owner might want to catch. But dissent is not
failure — the Doctrine holds it as *data* — so the gate must not treat it as a hard
failure by default; that would contradict the axiom the signal exists to serve.

## Decision

Report dissent in every gate run, and let a team opt in to gating on it.

- The gate always computes `dissent_rate` from `ConsensusLog(_db_path()).stats()`
  and prints it in both the text line (`… · dissent 1.0 · …`) and the JSON
  report, and records it under `policy`. Visibility is unconditional.
- `--max-dissent-rate <ceiling>` is a new, optional check. When set, the gate
  fails if the recorded rate exceeds the ceiling, with the reason
  `dissent_rate <r> over ceiling <c>`. When unset (the default), dissent never
  fails a build — it is reported and nothing more.

## Consequences

- The dissent arc is complete: recorded (0074) → attested (0075) → actionable
  (0076). A team that has decided a fracturing panel should block a release can now
  express that as one flag in its pipeline, on the same footing as `--min-cvi` or
  `--no-sla-breach`; a team that treats dissent purely as a diagnostic gets the
  number on every run and no new way to fail. Verified live: with a split panel
  recorded, a bare `gate` PASSes and prints `dissent 1.0`; `--max-dissent-rate 0.5`
  FAILs with the reason and exit 1; `--max-dissent-rate 1.0` PASSes.
- The default honours the axiom. Making the ceiling opt-in, defaulting off, keeps
  "dissent is data, not failure" true of the platform's own gate — the gate reports
  the disagreement but refuses to call it a failure unless a human explicitly asks
  it to. The policy encodes the philosophy rather than quietly overriding it.
- One source, no drift: the gate reads the dissent rate from the same
  `ConsensusLog.stats()` the digest, the report, and `/metrics` already use, so the
  gate cannot disagree with the other surfaces about how split the panel has been.
- Additive and self-consistent: a new optional flag and one reported figure, no
  change to any existing check or default. A pipeline that does not pass
  `--max-dissent-rate` behaves exactly as before, only more informatively.

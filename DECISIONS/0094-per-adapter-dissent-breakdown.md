# 0094 — Per-Adapter Dissent Breakdown

## Context

The Multi-Model layer is the platform's one *shipped* intelligence layer
(`DECISIONS/0093`): a panel whose disagreement is recorded as data, on the axiom
*dissent is data*. But the dissent ledger (`consensus_log`) kept only *how much* the
panel split — the `dissent_score`, the adapter **count**, and the aligned `verdicts`
list — and threw away *which* adapter cast which verdict: `record()` stored
`len(result["adapters"])`, not the names. So the axiom was only half honoured. The
ledger remembered that the panel disagreed and by how much, but not who the outlier
was, and a multi-model verification product could not answer "which perspective tends
to stand apart from the panel."

## Decision

Retain adapter identity in the ledger and expose a per-adapter track record.

- **Migration (additive):** `ConsensusLog.__init__` adds an `adapter_names TEXT` column
  when absent (a `PRAGMA table_info` check then `ALTER TABLE … ADD COLUMN`), so existing
  databases upgrade in place and old rows keep `NULL`.
- **`record()`** now persists the aligned adapter names (`json.dumps(result["adapters"])`),
  which `route_all` already returns index-aligned with `verdicts`. The old integer count
  is unchanged.
- **`by_adapter()`** derives each adapter's record from the rows that retained names:
  for every `(adapter, verdict)` pair, the evaluation counts, and it is an *agreement*
  when the verdict matches that evaluation's `majority`, else a *dissent* — yielding
  `{adapter, evaluations, agreed, dissented, agreement_rate}`. Rows without aligned names
  (pre-migration) are excluded, not guessed.
- **`GET /consensus/by-adapter`** serves it — public and aggregate, counts only, no
  prompt content, beside `/consensus/stats`.

## Consequences

- *Dissent is data* is now whole — the *who*, not only the *how much*: verified live, a
  split panel produces `skeptic` at `agreement_rate 0.333` (dissented 2 of 3) while
  `local`, `reasoning`, and `rules-engine` sit at `1.0`. The outlier perspective is
  legible, which is exactly what a panel exists to surface.
- Complements the existing aggregate: `/consensus/stats` answers "how split has the panel
  been"; `/consensus/by-adapter` answers "which member drives the split," from the same
  ledger, so an operator can see both the magnitude and the source of disagreement.
- Migration is honest and safe: the column is added in place, old rows are kept and simply
  omitted from the per-adapter view rather than back-filled with a guess — the ledger does
  not invent who dissented on evaluations it did not record it for.
- Deepens the one shipped intelligence layer without new dependencies: the panel already
  computed and returned the adapter names; the ledger simply stops discarding them.
  Additive — one column, one derived method, one endpoint, no change to any existing
  surface's behaviour, and the same privacy guarantee (only the prompt's SHA-256 is kept).

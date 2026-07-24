# 0072 — Portable Version Graph

## Context

The export bundle (`DECISIONS/0013`) made the record portable and offline-verifiable
— every attestation and checkpoint, walkable by `verify_ledger.py` with no service.
But since round 66 the record also carries a *version graph*: which attestation
supersedes which, and so which are current. That graph lived only in the running
service. An offline holder of a bundle could prove the chain was intact and signed,
yet could not answer "which of these attestations is the current verified version?"
— the portable record was complete about integrity but silent about currency.

## Decision

Carry the supersession graph in the bundle, and report it offline.

- `GET /attestations/export` now includes a `supersessions` key (the supersession
  log), composed at the endpoint from `supersession_log.list()`.
- `verify_ledger.py` gains a pure `current_ids(bundle)` — the attestation ids no
  supersession replaces, read from the bundle's `attestations` and `supersessions`.
  When the bundle carries a version graph, the offline report adds
  `current_attestations` and `superseded_attestations` counts.

## Consequences

- The whole record now travels, not just its chain: verified live, a bundle of
  three attestations with two supersessions verifies `intact` and `trustworthy`
  and reports `current 1 · superseded 2` — an offline holder can now tell integrity
  *and* currency from the bundle alone, with no service running.
- Verification is deliberately unchanged: `verify_bundle` still checks only the
  hash chain and the signed checkpoint. The supersession graph is *annotation*, not
  chain — it is not hash-covered, so the offline verifier *reports* the version
  graph but never claims to have cryptographically verified it. Conflating the two
  would overstate what a bundle proves.
- Backward compatible both ways: an old bundle without `supersessions` is treated
  as all-current (`current_ids` defaults to every attestation), and a new bundle's
  extra key is ignored by any verifier that doesn't know it — the online twin
  (`/attestations/verify-bundle`) and the offline walker both already skip unknown
  keys, so nothing that consumed the old bundle breaks.
- Composition, not new state: the endpoint reads the same `supersession_log` the
  `/lineage` endpoint serves, so the bundle's version graph cannot disagree with the
  live one, and the engine's `export()` stays unaware of supersession — the
  annotation is added beside the chain, never folded into it.

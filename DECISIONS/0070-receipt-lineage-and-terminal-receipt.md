# 0070 — Receipt Lineage and the Terminal Receipt Command

## Context

Three per-item facts existed but never met in one place. The receipt
(`DECISIONS/0033`, `0043`) proved an attestation's hash, chain position, entry
integrity, and seal. Supersession (`DECISIONS/0066`) recorded whether an
attestation was still the current version. And the verification terminal
(`DECISIONS/0069`) could query the record but not pull a receipt. A consumer
holding an artifact's id had to call one endpoint for its proof and another for
its version, and could do neither from the conversational face.

## Decision

Unify them: put lineage on the receipt, and give the terminal a receipt command.

- `GET /attestations/<id>/receipt` now carries a `lineage` field
  (`is_current`, `supersedes`, `superseded_by`), composed at the endpoint from the
  supersession log — so a single receipt answers "is this untampered, sealed, *and*
  the current version?".
- The chat terminal gains `/receipt <id>`: the full per-item proof rendered in the
  card vocabulary — subject, status, confidence, entry integrity, ledger
  integrity, chain position, seal, and version (`current` / `superseded by #N`).
- The console's Receipt panel shows the same version line beside the integrity and
  seal it already displayed.

## Consequences

- One receipt now tells the whole per-item story: verified live in the terminal,
  `/receipt` on a superseded attestation reads "entry intact; ledger intact; chain
  1/2; sealed; **superseded by #2**", and on its replacement reads "chain 2/2;
  sealed; **current**". Integrity, seal, and lineage — the three questions a holder
  of an artifact asks — answered in one card.
- Composition, not new state: the lineage is read from the same supersession log
  the `/lineage` endpoint serves, added at the receipt endpoint, so the receipt
  cannot disagree with the lineage endpoint, and the engine's `receipt()` stays
  unaware of supersession (the annotation lives beside the chain, not in it).
- The conversational face reaches parity with the console for reading the record:
  posture, integrity, index, content lookup, the human report, and now the per-item
  receipt are all a slash-command away — the terminal can pull the same proof a
  consumer would otherwise script against the API.
- The unification is honest about what each fact means: entry integrity is about
  tampering, the seal is about the signature, and lineage is about *currency* — the
  receipt keeps them distinct rather than collapsing them into a single "valid",
  because a superseded attestation is still perfectly intact and sealed; it is just
  no longer the current version.

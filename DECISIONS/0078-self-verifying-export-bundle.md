# 0078 — Self-Verifying Export Bundle

## Context

Two portable trust artifacts existed side by side but never together. The export
bundle (`/attestations/export`, verified by `verify_ledger.py`) proves the *record*
was neither edited in place nor rewritten wholesale — chain integrity plus a signed
checkpoint plus, since round 80, the supersession graph. The signed status digest
(`DECISIONS/0075`) proves the *platform's own summary* of its posture — CVI, source
coverage, dissent rate, held queue — genuinely came from the platform.

But the bundle carried only the record, not the summary. A recipient holding an
exported bundle could confirm the chain was intact and sealed, yet had no signed
statement of what the platform *said about* that chain, and no way to catch a
bundle whose self-report disagreed with the ledger it shipped with. Two proofs, two
artifacts, no link between them.

## Decision

Embed the signed posture digest in the export bundle, and have the verifier
cross-check it against the chain.

- `/attestations/export` now adds `bundle["digest"]` — the same signed document
  `/status/digest` serves. Both come from a new shared `_status_digest_document()`
  helper in `app.py`, so the digest a caller fetches and the one embedded in a
  bundle are produced identically and cannot drift.
- `verify_ledger.verify_digest(bundle, key)` (pure, over the bundle) reports:
  `signature_valid` (the HMAC validates under the key), `chain_length_matches` (the
  digest's `chain_length` equals the bundle's attestation count), `checkpoint_matches`
  (the digest's `checkpoint_head` equals the bundle's latest checkpoint head), and
  `consistent` (both cross-checks agree — key-independent).
- `_is_trustworthy` now fails a bundle whose embedded digest is inconsistent
  (regardless of key) or whose signature is invalid (when a key is given), so the
  offline verifier's exit code reflects it. Bundles without a `digest` key behave
  exactly as before — backward compatible.

## Consequences

- The bundle is now one complete, self-verifying trust package: chain integrity,
  the checkpoint seal, the version graph, and a signed posture snapshot, all
  checkable offline with one key and no service. Verified live — an exported bundle
  reports `intact`, `trustworthy`, and `digest.consistent` all true and exits 0.
- A self-report that lies about its own record is caught. Because the digest's
  `chain_length` and `checkpoint_head` are cross-checked against the very chain the
  bundle contains, a digest edited to claim a longer chain (or a different sealed
  head) fails `consistent` and makes the whole bundle untrustworthy — verified
  live, tampering `chain_length` to 99 exits 1 even though the chain walk itself
  still passes. The two proofs now constrain each other.
- Honest about what is and is not cross-checkable. The digest's CVI, dissent rate,
  and held counts derive from state not present in the bundle (held-review
  releases, the consensus ledger), so the verifier does not pretend to recompute
  them; it checks what the bundle *can* prove — that the signed posture describes
  this exact chain and genuinely bears the platform's signature. The structural
  claims are verified; the derived scalars are attested, not re-derived, and the
  report says only what it can stand behind.
- One source, no drift: the endpoint and the export share
  `_status_digest_document()`, so `/status/digest` and the embedded digest are the
  same bytes for the same state, and a client verifying either uses the same
  `status_digest.verify`.
- Additive and compatible: a new bundle field and a new verifier check. Older
  bundles without the field verify exactly as before; the online twin
  (`/attestations/verify-bundle`) and the chain/seal logic are untouched.

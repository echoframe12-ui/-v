# 0079 — The Online Twin Mirrors the Offline Verifier

## Context

`/attestations/verify-bundle` is documented as "the online twin of
`verify_ledger.py`" — the same verification a caller can run offline, offered as a
service for callers without local tooling. The value of a twin is that it does not
lie by omission: whatever the offline verifier would catch, the online one catches
too.

Round 78 broke that. Adding the embedded-digest cross-check
(`DECISIONS/0078`) taught the *offline* CLI to reject a bundle whose signed posture
contradicts its own chain — but the online endpoint still ran only `verify_bundle`,
the chain-and-seal check. A caller who POSTed a bundle with a tampered embedded
digest to the service got back `intact` and `trustworthy`, while running the same
bundle through `verify_ledger.py` would have flagged it. The twin had fallen behind
its original. Worse, the divergence was silent: the endpoint's own docstring still
promised parity it no longer delivered.

## Decision

Give both verifiers one shared assembly function, and route the endpoint through it.

- New `verify_ledger.full_report(bundle, key)` assembles the complete report —
  chain integrity and seal (`verify_bundle`), the version-graph counts when the
  bundle carries supersessions, and the embedded-digest cross-check when it carries
  a digest.
- The offline CLI `main` now calls `full_report` instead of assembling the report
  inline.
- `/attestations/verify-bundle` calls the same `full_report`, so the online
  response is byte-for-byte what the CLI prints for the same bundle and key.

## Consequences

- The twin is a twin again, structurally: because both verifiers call one function,
  the online endpoint cannot fall behind the offline one — a future check added to
  `full_report` reaches both at once. Verified live, the online response equals the
  offline report for a good bundle and for a tampered one, and both flag a digest
  edited to lie about its checkpoint head as `consistent: false`.
- The gap round 78 opened is closed: a bundle whose embedded posture digest
  contradicts its chain is now rejected by the service exactly as by the CLI, so a
  caller relying on the online twin gets the same protection as one running the
  tool locally.
- No new behaviour, one honest promise: the endpoint's docstring now names the full
  set of checks it performs, and it performs them. The signing key is still never
  accepted over the wire — the digest and checkpoint signatures validate only when
  the server already holds the key the bundle was sealed with, unchanged.
- Backward compatible: `full_report` is a superset of `verify_bundle`, adding keys
  only when the bundle carries supersessions or a digest, so a plain bundle yields
  the same report it always did and the existing twin tests are untouched.

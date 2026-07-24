# 0075 — Sign Dissent in the Status Digest

## Context

Round 74 (`DECISIONS/0074`) closed the recording gap: build-time dissent now
lands in the ledger, so the panel's disagreement is a complete, first-class
signal. The human trust report (`report.py`) already reads it. But the one
artifact designed to be handed to a third party and *cryptographically verified* —
the signed status digest (`status_digest.py`) — did not carry it.

The digest's whole purpose is "attest, don't assert, even about your own health":
a compact canonical posture plus an operator-key HMAC, so a recipient can confirm
the platform genuinely reported this state rather than fabricating a "we were
healthy" claim. It signed CVI, source coverage, chain state, and the held queue —
but not dissent. A recipient could verify the confidence and the integrity of the
record while the panel's level of disagreement, now a primary signal, travelled
unsigned or not at all. The signature covered everything about trust except how
much the models trusted each other.

## Decision

Add `dissent_rate` to the signable posture.

- `status_digest.SIGNABLE_FIELDS` gains `dissent_rate` (placed with the other
  trust dimensions, after `sourced_ratio`), and `build_payload` takes and emits it.
  Because `canonical()` selects exactly `SIGNABLE_FIELDS`, the dissent rate is now
  inside the bytes the HMAC covers — tampering with it invalidates the signature,
  verified by test.
- `/status/digest` passes `consensus_log.stats()["dissent_rate"]`.
- The offline `digest` CLI (`oceanic_os.py`) reads the same figure straight from
  the ledger via `ConsensusLog(_db_path()).stats()["dissent_rate"]`, so a digest
  produced by the running service and one produced offline from the same database
  stay byte-identical — the property that lets the CLI verify a service-emitted
  digest and vice versa.

## Consequences

- The signed self-report is now complete: verified live, a service digest and an
  offline-CLI digest over the same seeded database both carry `dissent_rate 1.0`,
  each self-verifies under the key, and their canonical forms are byte-identical —
  so the dissent rate a recipient reads is the dissent rate the signature attests,
  from either producer. Tampering the field breaks verification exactly as
  tampering the posture does.
- One posture, one source of drift: dissent enters the digest through the same
  `consensus_log.stats()` the metrics endpoint and report already use, so the
  three surfaces cannot disagree about how split the panel has been.
- Recording without attesting was half the axiom. Round 74 made *dissent is data*;
  this makes that data part of what the platform will put its signature behind. A
  third party can now hold the platform to its disagreement, not just its
  confidence.
- Backward note: adding a signable field changes the canonical bytes, so a digest
  emitted before this change verifies only against a payload lacking `dissent_rate`.
  Digests are ephemeral point-in-time snapshots, not stored long-lived records
  (the checkpoint and per-attestation receipt are the durable proofs), so no
  archived artifact is invalidated in practice; a stale digest simply reflects the
  older schema, as its timestamp already shows.
- Additive to the schema, not the surface: no new endpoint, no new state — the
  ledger, its stats, and the digest all existed; this threads one figure that was
  already computed into the payload that was already signed.

# Ω∞v Attestation Protocol v0.1

**Principle:** Attest, don't assert.

## Purpose

This protocol adds a cryptographic envelope around one existing Oceanic
verification cycle. The repository already owns the domain-level attestation
model in `oceanic_attestation.py`; this module does not replace it.

It does not replace the existing Oceanic IR, Observer, lifecycle, or event
ledger.

## Trust boundaries

`Verification` answers whether the configured checks produced a result.

`Attestation` records that result, its provenance, dissent, hashes, status,
and lineage at a point in time.

`Signature` cryptographically authorizes the canonical bytes of that record.

These are intentionally separate.

## Signed record

The v0.1 signed document contains:

- schema and schema version
- attestation/request/session identifiers
- timestamp
- prompt hash and output hash
- model manifest and ensemble strategy
- verification status, contract/cycle references, confidence and decision
- CVI score/breakdown slot
- consensus and explicit dissent
- evidence anchors
- human-review state
- constitutional checks
- constitution version
- parent attestation lineage
- drift/recompile state
- next state
- schema digest
- signer algorithm and public-key-derived key ID

The outer envelope carries the Ed25519 signature and public key.

## Canonicalization

The unsigned document is serialized as UTF-8 JSON with:

- lexicographically sorted object keys;
- compact separators `,` and `:`;
- UTF-8 characters preserved.

The exact canonical bytes are what Ed25519 signs and what an independent
verifier reconstructs.

## Independent verification

A recipient needs the exported JSON document and its embedded Ed25519 public
key. `verify_attestation()`:

1. reconstructs the unsigned document;
2. verifies the Ed25519 signature;
3. verifies the public-key-derived signer identity;
4. checks the declared schema and version;
5. recomputes the final-output SHA-256 binding;
6. optionally compares the signed schema digest against an independently
   resolved schema digest;
7. returns `valid=false` if any of those integrity checks fail.

A modified signed field invalidates the signature. A valid signature alone is
not treated as sufficient: schema and output integrity must also hold.

## Key handling

Private keys are deliberately not stored in the repository or in an
attestation. `generate_keypair()` only provisions raw local key material.
Production key custody belongs outside the application data model.

The embedded public key is not a trust anchor by itself; a deployment must
establish which verification identities/keys it trusts.

## Revocation

The protocol reserves revocation as an append-only signed event referencing
the original attestation. **Revocation event creation is not implemented in
v0.1 yet.** No issued attestation is silently rewritten or deleted.

## First vertical slice

```text
Input
  ↓
Observation
  ↓
Existing Oceanic Cycle verification
  ↓
Domain attestation
  ↓
Cryptographic Ed25519 envelope
  ↓
Independent verification
  ↓
Next state
```

This is the minimum executable heartbeat. Persistent ledger integration,
VaaS exposure, richer CVI breakdowns, quorum semantics, revocation events,
and Ω∞v Edge attach to this boundary later.

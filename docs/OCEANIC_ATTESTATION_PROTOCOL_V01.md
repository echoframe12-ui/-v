# Ω∞v Attestation Protocol v0.1

**Principle:** Attest, don't assert.

## Purpose

This protocol binds one existing Oceanic verification cycle to a portable,
cryptographically signed evidence record. It does not replace the existing
Oceanic IR, Observer, lifecycle, or event ledger.

## Trust boundaries

`Verification` answers whether the configured checks produced a result.

`Attestation` records that result, its provenance, dissent, hashes, status,
and lineage at a point in time.

`Signature` cryptographically authorizes the canonical attestation bytes.

These are intentionally separate.

## Signed record

The v0.1 document contains:

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

The outer envelope carries the Ed25519 signature and public key.

## Canonicalization

The unsigned document is serialized as UTF-8 JSON with:

- lexicographically sorted object keys;
- compact separators `,` and `:`;
- UTF-8 characters preserved.

The exact canonical bytes are what Ed25519 signs and what an independent
verifier reconstructs.

## Independent verification

A recipient needs only the exported JSON document and its embedded Ed25519
public key. `verify_attestation()`:

1. reconstructs the unsigned document;
2. verifies the Ed25519 signature;
3. checks the declared schema;
4. recomputes the final-output SHA-256 binding;
5. returns the next state without trusting the producer's process.

A modified signed field invalidates the signature.

## Key handling

Private keys are deliberately not stored in the repository or in an
attestation. `generate_keypair()` only provisions raw local key material.
Production key custody belongs outside the application data model.

## Revocation

An issued attestation is immutable. Revocation must be represented by a new
signed event referencing the original attestation; the original record is not
rewritten.

## First vertical slice

```text
Input
  ↓
Observation
  ↓
Existing Oceanic Cycle verification
  ↓
Signed Attestation
  ↓
Independent Ed25519 verification
  ↓
Next state
```

This is the minimum executable heartbeat. Storage, VaaS exposure, richer CVI
breakdowns, quorum semantics, and Ω∞v Edge can attach to this boundary later.

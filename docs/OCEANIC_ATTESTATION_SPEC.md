# Ω∞ Oceanic Attestation Specification

**Status:** Draft v0.1

> Verification becomes auditable execution only when the evidence is preserved.

## Purpose

An attestation is a durable record of what the Oceanic verification system believed at a specific point in time, why it believed it, what dissent remained, and whether execution was authorized.

Attestation is evidence, not truth. Runtime observation may later invalidate the assumptions recorded here.

## Lifecycle

```text
CONTRACT
  ↓
COMPILE
  ↓
PROVE
  ↓
VERIFY
  ↓
ATTEST
  ↓
AUTHORIZE
  ↓
EXECUTE
  ↓
OBSERVE
  ↓
COMPARE
  ↓
LEARN
```

## Attestation Record

```yaml
attestation:
  schema: oceanic.attestation/v0.1
  attestation_id: ...
  contract_id: ...
  contract_digest: sha256:...
  created_at: ...
  adapters:
    - language: python
      adapter_version: ...
      implementation_digest: sha256:...
      proof_status: proved_with_dissent
      confidence: 0.95
      dissent:
        - ...
  aggregate:
    status: proved_with_dissent
    confidence: 0.90
    dissent:
      - ...
  authorization:
    status: pending
    authority: human
  runtime:
    status: not_started
  observation:
    status: pending
```

## Integrity

Every attestation should bind together:

- contract digest;
- implementation digest;
- adapter version;
- toolchain identity;
- proof artifact identity;
- verification outcome;
- authorization decision.

A change to any bound artifact creates a new attestation rather than silently mutating the old one.

## Authorization States

```text
PENDING
  ↓
AUTHORIZED ─────→ EXECUTED
  ↓                  ↓
REJECTED          OBSERVED
                     ↓
                  COMPARED
```

Authorization is intentionally separate from verification. A contract may be technically verified and still require human authorization because of risk, consequence, uncertainty, or unresolved dissent.

## Dissent Preservation

Dissent is never deleted from an attestation because the final status is successful.

The system preserves:

- which adapter raised dissent;
- what obligation was affected;
- whether dissent was hard or soft;
- whether a human reviewed it;
- whether runtime observation later confirmed or contradicted it.

## Runtime Observation

After execution, the Observer records whether reality matched the contract.

```yaml
observation:
  status: matched | deviated | inconclusive
  contract_id: ...
  runtime_digest: sha256:...
  evidence: ...
  deviations:
    - ...
```

A deviation is not automatically a failure of the whole system. It is a learning signal. The Evolution Engine may propose a contract revision, adapter proof improvement, or new dissent trigger.

## Confidence

Confidence is an evidence signal, not a probability of universal correctness.

The first implementation may aggregate adapter confidence as a simple mean, but future versions should account for:

- independence of evidence;
- proof strength;
- correlated failure modes;
- unresolved dissent;
- runtime history;
- domain risk.

The system must not use confidence to conceal hard safety constraints. A hard unmet obligation remains unproven regardless of aggregate confidence.

## Local-First Operation

Attestations must be serializable to a local, human-readable format and persistable without network access.

Recommended local storage:

```text
JSON/YAML file
      +
SQLite event log
      +
content-addressed artifacts
```

When connectivity returns, synchronization may occur, but the local attestation remains authoritative for the local execution event.

## Evolution Loop

```text
ATTESTATION
   ↓
RUNTIME OBSERVATION
   ↓
CONTRACT MATCH?
   ├── YES → strengthen evidence history
   └── NO  → record deviation
                ↓
          EVOLUTION PROPOSAL
                ↓
          HUMAN / POLICY REVIEW
                ↓
           NEW CONTRACT VERSION
```

The Evolution Engine proposes changes. It does not silently rewrite the contract that authorized a past execution.

## Constitutional Principle

> **A verified intention may be executed. A witnessed deviation may be learned from. Neither may erase the history of the other.**

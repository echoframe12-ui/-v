# Ω∞ Oceanic IR Contract Specification

**Status:** Draft v0.1 — experimental architecture

> **The language is the form. The contract is the conscience. The proof is the bridge.**

## 1. Definition

Oceanic IR is **not a programming language**. It is a machine-readable verification contract describing intent, required invariants, permitted effects, operational bounds, dependencies, dissent triggers, and proof obligations.

The contract is the stable reference shared by multiple implementations.

```text
Intent → Contract → Implementations → Proofs → Verification → Attestation
```

## 2. Minimal Contract Schema

```yaml
api_version: oceanic.ir/v0.1
contract_id: example.add.v1
intent: combine two numeric values
inputs:
  - name: a
    type: integer
  - name: b
    type: integer
outputs:
  type: integer
invariants:
  - result == mathematical_sum(a, b)
  - overflow_is_never_silent
effects: []
bounds:
  time: O(1)
  memory: O(1)
dependencies: []
proof_obligations:
  - arithmetic_correctness
  - overflow_handling
dissent_triggers:
  - overflow
  - unsupported_numeric_domain
risk:
  class: low
  human_authorization: false
```

## 3. Contract Semantics

### Intent
A human-readable statement of the desired behavior. Intent is explanatory; invariants and proof obligations are normative.

### Invariants
Properties that must remain true for every accepted execution within the declared domain.

### Effects
A declaration of state that may be mutated or external systems that may be contacted. An empty effect set means the contract requires purity.

### Bounds
Explicit operational constraints such as time complexity, memory, latency, precision, energy, or trust requirements.

### Dependencies
External resources required for compilation, verification, or runtime execution. Dependencies must be named and versioned where possible.

### Proof obligations
Claims that an adapter must provide evidence for before an implementation can be attested.

### Dissent triggers
Conditions that prevent silent acceptance. Dissent may be informational, escalation-worthy, or a hard rejection depending on policy.

## 4. Adapter Result States

Every adapter must return one of these semantic states:

```text
PROVED
  Contract requirements satisfied with declared evidence.

PROVED_WITH_DISSENT
  Required contract satisfied, but limitations or weaker evidence remain.

UNPROVEN
  Implementation exists, but required proof is incomplete.

REJECTED
  Adapter cannot satisfy a hard contract requirement.

FAILED
  Compilation or verification itself failed.
```

Adapters must never convert `UNPROVEN` into `PROVED` merely because the program executes successfully.

## 5. Proof Artifact Contract

```yaml
proof_api: oceanic.proof/v0.1
contract_id: example.add.v1
adapter:
  language: rust
  compiler: rustc
  compiler_version: 1.75.0
implementation_digest: sha256:...
toolchain_digest: sha256:...
claims:
  - obligation: arithmetic_correctness
    status: satisfied
    evidence_type: checked_tests
    evidence_digest: sha256:...
  - obligation: overflow_handling
    status: satisfied
    evidence_type: checked_arithmetic
    evidence_digest: sha256:...
limitations: []
dissent: []
reproducibility:
  lockfile: sha256:...
  environment: sha256:...
```

The verifier checks **coverage**: whether every mandatory proof obligation has sufficient evidence. Evidence strength is policy-driven and must remain visible.

## 6. Capability Negotiation

Before compilation, the compiler evaluates:

```text
contract requirements
        ×
adapter capabilities
        ↓
compatible / compatible-with-dissent / incompatible
```

A hard requirement that an adapter cannot prove produces `REJECTED`. A soft requirement produces `PROVED_WITH_DISSENT` only if all mandatory obligations are otherwise satisfied.

## 7. Multi-Adapter Verification

Multiple adapters are independent perspectives, not a popularity vote.

```text
             SAME CONTRACT
             /      |      \
        Python    Rust    TypeScript
           ↓        ↓         ↓
         proof    proof      proof
           \        |         /
            └── verifier ───┘
                    ↓
             coverage matrix
                    ↓
              dissent report
                    ↓
              attestation
```

A consensus result must preserve differences in proof strength. Agreement between implementations is evidence; it is not proof by itself.

## 8. Confidence and Escalation

Confidence is a derived signal and never replaces a hard proof obligation.

Recommended policy:

```text
hard safety constraint missing → REJECT / HUMAN REVIEW
mandatory proof incomplete     → UNPROVEN
multiple independent proofs    → confidence increases
adapter limitation             → dissent remains visible
high-risk domain               → human authorization required
```

The historical Ω∞ 74% threshold may be used as a configurable escalation policy, but must not be interpreted as permission to override constitutional or safety constraints.

## 9. Local-First Requirements

A conforming implementation should support:

- offline contract parsing;
- local validation;
- local adapter discovery;
- local proof verification;
- deterministic or reproducible builds where feasible;
- append-only local observation logs;
- explicit synchronization when network connectivity returns.

Network services are optional accelerators, not prerequisites for core contract integrity.

## 10. Observer Feedback

After runtime execution, the Observer records whether observed behavior matches the contract.

```text
CONTRACT
  ↓
PROOF
  ↓
ATTESTATION
  ↓
RUNTIME
  ↓
OBSERVATION
  ├── matches → reinforce evidence
  ├── mismatch → open dissent
  └── novel edge case → evolution proposal
```

The Evolution Engine may propose changes to contracts, proof schemas, or adapter capabilities. Changes require explicit review according to risk and governance policy.

## 11. Constitutional Guardrails

The compiler must preserve the following principles:

1. **Reality before assumption.**
2. **Evidence before certainty.**
3. **Dissent before forced consensus.**
4. **Provenance before convenience.**
5. **Human accountability for consequential decisions.**
6. **No silent capability inflation.**
7. **No automatic weakening of hard constraints.**
8. **Graceful degradation without loss of integrity.**

## 12. Reference Lifecycle

```text
SOURCE
  ↓
INTENT
  ↓
OCEANIC IR CONTRACT
  ↓
VALIDATE CONTRACT
  ↓
DISCOVER ADAPTERS
  ↓
CAPABILITY NEGOTIATION
  ↓
COMPILE INDEPENDENTLY
  ↓
GENERATE PROOFS
  ↓
VERIFY PROOFS AGAINST CONTRACT
  ↓
SURFACE DISSENT
  ↓
ATTEST OR ESCALATE
  ↓
AUTHORIZE WHEN REQUIRED
  ↓
RUN
  ↓
OBSERVE
  ↓
LEARN
  ↓
PROPOSE EVOLUTION
  ↺
```

## 13. Design Invariant

> **The contract remains stable while implementations may vary. Proofs may improve while claims remain bounded. Dissent is retained as information. Evolution changes the system through evidence, not silent self-modification.**

This specification is intentionally small. The next implementation milestone is a reference validator, adapter manifest schema, proof schema, and three minimal adapters: Python, Rust, and TypeScript.
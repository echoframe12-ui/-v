# Ω∞ Oceanic Adapter Protocol

**Status:** Draft v0.1

> **One contract. Many forms. Proof before permission.**

## Purpose

An Oceanic adapter translates an Oceanic IR contract into a concrete implementation language while producing evidence about which contract obligations it can and cannot prove.

The adapter is not trusted merely because it compiles code. Compilation is an implementation step. Verification is a separate step.

## Adapter Lifecycle

```text
DISCOVER
  ↓
READ MANIFEST
  ↓
MATCH CAPABILITIES
  ↓
COMPILE CONTRACT
  ↓
RUN ADAPTER TESTS
  ↓
GENERATE PROOF ARTIFACT
  ↓
VERIFY PROOF
  ↓
SURFACE DISSENT
  ↓
ATTEST / ESCALATE / REJECT
```

## Manifest

```yaml
adapter_manifest:
  protocol: oceanic.adapter/v0.1
  language: python
  language_version: "3.12"
  adapter_version: "0.1.0"
  capabilities:
    - pure_functions
    - runtime_checks
    - property_testing
  proof_types:
    - unit_tests
    - property_tests
    - static_analysis
  limitations:
    - "memory safety is not statically guaranteed"
  local_first: true
  dissent_mode: surface_first
```

Required manifest fields:

- protocol version;
- language and version;
- adapter version;
- declared capabilities;
- proof types;
- limitations;
- local-first support;
- dissent behavior.

## Capability Semantics

Capabilities are claims that must themselves be auditable.

```text
DECLARED CAPABILITY
       ↓
SUPPORTED BY ADAPTER
       ↓
SUPPORTED BY TOOLCHAIN
       ↓
SUPPORTED BY PROOF ARTIFACT
       ↓
ACCEPTED BY VERIFIER
```

An adapter may declare a capability but cannot claim contract satisfaction unless the generated proof artifact demonstrates coverage of the relevant obligation.

## Dissent Modes

### `surface_first`
Compile where possible, but expose all limitations.

### `reject_hard_constraints`
Refuse compilation when a mandatory requirement cannot be satisfied.

### `human_escalate`
Route unresolved capability gaps to human review.

Adapters must never silently downgrade a hard requirement into a soft one.

## Compilation Result

```yaml
compile_result:
  contract_id: example.add.v1
  adapter: python
  status: compiled
  implementation_digest: sha256:...
  artifacts:
    source: ...
    tests: ...
    proof: ...
  dissent:
    - "overflow behavior depends on declared numeric domain"
```

Compilation success does not imply verification success.

## Proof Result

```yaml
proof_result:
  contract_id: example.add.v1
  adapter: python
  status: proved_with_dissent
  obligations:
    - name: arithmetic_correctness
      status: satisfied
      evidence: property_tests
    - name: overflow_handling
      status: satisfied
      evidence: runtime_checks
  dissent:
    - "guarantee is runtime-enforced rather than statically enforced"
```

## Reference Adapter Set

The first reference implementations should target:

### Python

Strengths:
- rapid development;
- broad ecosystem;
- easy local execution.

Typical proof sources:
- unit tests;
- property tests;
- static analysis;
- dependency inspection.

Typical dissent:
- weaker compile-time guarantees;
- runtime-dependent behavior.

### Rust

Strengths:
- strong memory-safety guarantees;
- explicit error handling;
- useful systems-level evidence.

Typical proof sources:
- compiler checks;
- borrow checker;
- checked arithmetic;
- tests;
- dependency lockfiles.

Typical dissent:
- unsafe code where present;
- platform-specific behavior;
- toolchain-specific assumptions.

### TypeScript / JavaScript

Strengths:
- web-native execution;
- large ecosystem;
- asynchronous programming.

Typical proof sources:
- TypeScript compiler;
- tests;
- lint/static analysis;
- runtime assertions.

Typical dissent:
- JavaScript runtime differences;
- dynamic behavior at runtime;
- environment-dependent APIs.

## Adapter Independence

Adapters should be independently executable and testable. The core verifier must not depend on importing every target language runtime.

```text
                 OCEANIC IR
                     │
          ┌──────────┼──────────┐
          ↓          ↓          ↓
       Python       Rust    TypeScript
          │          │          │
       proof       proof      proof
          └──────────┼──────────┘
                     ↓
               Core Verifier
```

This keeps the core system small and allows new adapters to be added without changing the verification kernel.

## Local-First Adapter Contract

An adapter should provide:

```text
adapter inspect
adapter capabilities
adapter compile contract.ir
adapter test artifact
adapter prove artifact
adapter verify proof
```

These operations should work offline whenever the required compiler and dependencies are already installed.

Network access must be explicit and declared as a dependency when required.

## Security Boundary

An adapter is untrusted code until its outputs are verified.

The system must:

- isolate compilation where practical;
- pin toolchain versions for reproducibility;
- record dependency digests;
- hash implementation artifacts;
- preserve proof provenance;
- prevent adapter output from modifying contracts or governance automatically;
- require authorization before consequential execution.

## Evolution

When an adapter repeatedly exposes the same dissent, the Evolution Engine may propose:

1. a stronger IR invariant;
2. a new proof obligation;
3. a new capability declaration;
4. a better proof schema;
5. a new adapter implementation;
6. a policy change requiring human review.

The Evolution Engine must never silently erase historical dissent.

## Design Principle

> **Adapters translate. Proofs substantiate. The verifier judges coverage. The Observer checks reality. The Evolution Engine learns from the gap.**

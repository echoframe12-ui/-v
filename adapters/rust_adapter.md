# Ω∞ Rust Adapter Reference Design

**Status:** Reference adapter specification v0.1

The Rust adapter provides a second implementation perspective for the same Oceanic IR contract. Its purpose is not to make Rust the preferred language, but to demonstrate that different languages can produce different proof evidence for one shared contract.

## Contract Mapping

For a numeric addition contract requiring:

- arithmetic correctness;
- overflow handling;
- O(1) time;
- O(1) memory;

an idiomatic Rust implementation can use checked arithmetic:

```rust
pub fn combine(a: i64, b: i64) -> Result<i64, &'static str> {
    a.checked_add(b).ok_or("integer overflow")
}
```

## Proof Perspective

The adapter can provide evidence through:

- Rust compiler type checking;
- explicit `checked_add` overflow handling;
- unit tests for normal and boundary inputs;
- dependency lockfile provenance;
- optional property-based testing.

The Rust adapter should report its evidence explicitly rather than claiming that compilation alone proves the entire Oceanic contract.

## Expected Proof Artifact

```yaml
proof_api: oceanic.proof/v0.1
contract_id: example.add.v1
adapter:
  language: rust
  language_version: "1.75.0"
  adapter_version: "0.1.0"
claims:
  - obligation: arithmetic_correctness
    status: satisfied
    evidence_type: unit_tests
  - obligation: overflow_handling
    status: satisfied
    evidence_type: checked_arithmetic
limitations:
  - "platform assumptions must be recorded"
dissent: []
```

## Cross-Language Verification

The same IR contract can therefore produce:

```text
                 OCEANIC IR
                    /   \
                   /     \
             Python       Rust
                ↓           ↓
             proof       proof
                ↓           ↓
             runtime     runtime
                \           /
                 \         /
                  VERIFIER
                     ↓
              SHARED CONTRACT
                     ↓
              DISSENT REPORT
```

The verifier compares **contract coverage**, not source-code similarity.

## Deliberate Difference from Python

The Python reference adapter may rely more heavily on runtime semantics and tests. The Rust adapter can provide stronger evidence for certain classes of safety because the compiler and type system enforce additional constraints.

This difference is retained as useful dissent rather than normalized away.

## Next Implementation

The executable Rust adapter should emit a standard `ProofArtifact` compatible with `oceanic_ir.py`, allowing the same contract to be verified across Python and Rust.

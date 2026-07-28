# Oceanic Cycle Kernel — Specification

> 💧 Ω∞v — OBSERVE · VERIFY · EVOLVE

## Overview

The Oceanic Cycle Kernel is the executable heart of `Ω∞v / OCEANICOS`.
It implements one complete state transition cycle:

```
OBSERVE → CONTRACT → VERIFY → CONSENSUS/DISSENT → ATTEST →
ACCOUNT → ACT → CONSEQUENCE → LEARN → DETECT DRIFT →
RECOMPILE → OBSERVE
```

Each cycle transitions the system from **Sₙ** to **Sₙ₊₁**, leaving an
immutable audit record with full provenance.

## Invariants

1. **No state transition without an observable reason.**
2. **No evolution without verification.**
3. **No dissent without a record.**
4. **No record without provenance.**
5. **Evolution may change the system, but may not secretly change the rules
   by which the system is trusted.**

## Event Schema

Every `CycleEvent` contains exactly 14 fields:

| Field             | Type                 | Description                              |
|-------------------|----------------------|------------------------------------------|
| `cycle_id`        | `str`                | Unique hex ID for this cycle             |
| `state_id`        | `str`                | The state before this cycle (Sₙ)         |
| `contract_id`     | `str`                | Contract verified against                |
| `observer`        | `str`                | Who observed                             |
| `evidence`        | `tuple[str, ...]`    | Evidence references                      |
| `verification`    | `VerificationStatus` | Outcome of verification                  |
| `confidence`      | `float | None`       | Verification confidence [0.0, 1.0]       |
| `dissent`         | `tuple[str, ...]`    | Dissent records (never suppressed)       |
| `decision`        | `DecisionRoute`      | Routed decision                          |
| `action`          | `str`                | What was done                            |
| `consequence`     | `str`                | What happened as a result                |
| `next_state`      | `str`                | The state after this cycle (Sₙ₊₁)       |
| `provenance_hash` | `str`                | SHA-256 binding state+contract+evidence  |
| `timestamp`       | `str`                | ISO-8601 UTC timestamp                   |

## Verification Decision Routing

```
VERIFIED           → ACCEPT
PARTIALLY_VERIFIED → CONTINUE_CHECKING
DISSENT            → HUMAN_ROUTE
UNVERIFIED         → HOLD
BLOCKED            → HUMAN_AUTHORIZATION
```

## Provenance

The `provenance_hash` is a deterministic SHA-256 hash of:

```json
{
  "state_id": "S0",
  "contract_id": "C-001",
  "evidence": ["evidence-1"],
  "verification": "verified",
  "decision": "accept"
}
```

This can be re-derived from any `CycleEvent` to verify the record has not
been tampered with. `OceanicCycle.verify_provenance(event)` does this
automatically.

## Usage

```python
from oceanic_cycle import OceanicCycle, Observation, Contract, VerificationResult, VerificationStatus

cycle = OceanicCycle()

# 1. Observe
obs = Observation(observer="test", what="reality check", evidence=("e1",))

# 2. Contract
contract = Contract(contract_id="C-001", clauses=("no regressions",))

# 3. Verify
result = VerificationResult(
    status=VerificationStatus.VERIFIED, confidence=0.95,
    evidence_hash="abc", checks_passed=3, checks_total=3,
)

# 4. Execute cycle
event = cycle.execute(obs, contract, result)

# 5. Verify provenance
assert cycle.verify_provenance(event)

# 6. Audit trail
trail = cycle.audit_trail()  # JSON-serializable list of dicts
```

## Test Coverage

27 tests covering all 7 required scenarios from the master prompt:

1. ✅ Observe → Verify → Consensus
2. ✅ Observe → Verify → Dissent
3. ✅ Dissent → Human Hold
4. ✅ Verified → Evolve
5. ✅ Evolution → Reverify
6. ✅ Drift → Recompile
7. ✅ Full Cycle → Immutable Audit Record

Plus additional tests for provenance, routing, enums, invariants, schema,
immutability, and frozen data classes.

## Design Principle

> **Attest, don't assert.**

The cycle kernel does not hide uncertainty. When verification produces
dissent, the dissent is recorded and routed to human judgment. The gap
itself becomes data.

---

💧 Ω∞v — One Root · One Current · Infinite Becoming

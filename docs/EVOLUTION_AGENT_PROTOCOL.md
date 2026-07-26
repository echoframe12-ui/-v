# Ω∞ Evolution Agent Protocol

## Status

Proposed architecture for controlled self-improvement.

## Principle

> Evolution proposes. Verification disposes. Humans authorize. History remembers.

The evolution agent is an adaptive layer that observes runtime evidence, detects drift, proposes improvements, generates tests, and prepares patches. It does not silently rewrite constitutional or historical state.

## Lifecycle

```text
Observer
  ↓
Evidence
  ↓
Evolution Agent
  ↓
Proposal
  ├── reason
  ├── evidence
  ├── affected contract
  ├── expected improvement
  ├── risk
  └── generated tests
       ↓
Verification
       ↓
Human Authorization
       ↓
Patch
       ↓
CI
       ↓
Attestation
       ↓
Event Ledger
       ↺
```

## Proposal Contract

Every proposal should contain:

- `proposal_id` — stable identifier
- `source_observation` — evidence that triggered the proposal
- `target_contract` — contract or component affected
- `reason` — why change is proposed
- `hypothesis` — expected improvement
- `risk` — known and suspected risks
- `patch` — proposed implementation change
- `tests` — tests added or modified to validate the change
- `verification_plan` — how the proposal will be evaluated
- `authorization_state` — pending, approved, or rejected
- `provenance` — links to evidence, commits, attestations, and ledger events

## Agent Permissions

### The agent MAY

- Observe runtime evidence.
- Detect deviations and recurring friction.
- Identify missing invariants or proof obligations.
- Propose IR contract revisions.
- Generate candidate patches.
- Generate or improve tests.
- Run local verification where permitted.
- Surface dissent and uncertainty.
- Prepare pull requests for human review.

### The agent MUST NOT

- Silently rewrite the Charter.
- Delete or rewrite historical evidence.
- Bypass authorization gates.
- Suppress dissent to increase confidence.
- Treat a proposal as an accepted fact.
- Promote unverified code into trusted runtime state.
- Change its own governance rules without explicit authorization.

## Verification Gate

An evolution proposal is not an evolution event merely because an agent generated it.

```text
PROPOSED
   ↓
VERIFIED?
 ┌─┴─┐
NO  YES
 │    │
REJECT  HUMAN REVIEW
          ↓
       AUTHORIZED?
        ┌─┴─┐
       NO  YES
       │    │
     REJECT  MERGE
              ↓
             CI
              ↓
          ATTESTATION
              ↓
            LEDGER
```

## Self-Improvement Boundary

The agent may improve implementation and propose contract changes, but the system's constitutional constraints remain external to autonomous mutation.

This creates a bounded form of self-improvement:

```text
self-observation
      +
self-proposal
      +
self-testing
      +
self-verification
      -
self-authorization
```

The final term is intentionally excluded from autonomous control.

## A/B/C Continuity

Continuation repositories or accounts are treated as independent execution environments sharing a common protocol.

```text
A: Charter / Foundation
        ↓ verified handoff
B: Continuous Becoming / Evolution
        ↓ verified handoff
C: Observer / Runtime Feedback
        ↓ verified handoff
A → B → C → ∞
```

A handoff should carry enough provenance for the next environment to reconstruct the current state without trusting memory alone.

## Exit Condition

A successful evolution cycle is not the absence of change. It is a traceable transition:

```text
Observation
→ Proposal
→ Verification
→ Authorization
→ Implementation
→ CI
→ Attestation
→ Ledger
```

**Exit 0 = one verified transition completed.**

**Continue = the system remains open to the next verified transition.**

# Ω∞ Oceanic — Integration Contract v1

**Status:** Draft / executable contract target
**Parent:** `OMEGA_OCEANIC_MASTER_INTEGRATION_V1.md`

## Purpose

Define a minimal, provider-neutral contract for the Ω∞ Oceanic master loop without claiming capabilities that are not yet implemented.

## Canonical Pipeline

```text
Context → Perspectives → Dissent → Verify → Attest → Authorize → Observe
```

Every stage produces an explicit, serializable state. A later stage must not erase uncertainty, provenance, or dissent produced by an earlier stage.

## Core Objects

### Context

```text
id
source_refs[]
timestamp
content_hash
scope
truncation
```

### Perspective

```text
id
provider
model
response
source_refs[]
confidence
timestamp
```

### Dissent

```text
id
perspective_ids[]
claim
contradictions[]
severity
resolution_status
```

### Verification

```text
id
claim
checks[]
status
confidence
provenance[]
```

### Attestation

```text
id
verification_id
result_hash
timestamp
signer
confidence
```

### Authorization

```text
id
action
risk_level
policy_result
human_required
approved
```

### Observation

```text
id
action_id
outcome
expected
actual
drift
next_state
```

## Safety Invariants

1. **No provenance, no attestation.**
2. **Unresolved high-severity dissent blocks automatic authorization.**
3. **Low confidence never becomes certainty through serialization.**
4. **Human-required actions cannot be silently downgraded.**
5. **Offline fallback may reduce capability, never integrity.**
6. **Every consequential action has an observable outcome.**
7. **Every state transition is auditable.**

## Proactive Mode

The first proactive implementation is proposal-only:

```text
OBSERVE
→ PREDICT
→ SIMULATE
→ PROPOSE
→ VERIFY
→ AUTHORIZE
→ ACT
```

Until an implementation and tests demonstrate otherwise, **PROPOSE** is the terminal state for proactive mode. The system must not imply autonomous execution merely because it can generate a plan.

## Large-Context Mode

Large-context support must expose:

- the context sources included;
- the context sources omitted;
- truncation or summarization events;
- content hashes where practical;
- temporal ordering;
- authority or provenance metadata.

A larger context window is treated as increased observability, not automatic truth.

## Provider-Neutral Model Boundary

Model providers must be replaceable behind a common adapter boundary. An adapter must expose enough metadata to preserve:

- provider identity;
- model identity;
- version where available;
- timestamp;
- input/context references;
- output;
- confidence or uncertainty metadata where available;
- failure state.

## Acceptance Criteria

The integration is ready for implementation when tests can prove:

- a context can be assembled and traced;
- multiple perspectives can be compared;
- dissent can be represented without loss;
- verification can reject unsupported claims;
- attestations retain provenance;
- authorization respects policy and human gates;
- proactive mode stops at proposal when execution is not authorized;
- observations can feed drift detection;
- every transition remains auditable.

## Ω∞ Principle

> The Current may move through many forms, but every form must remain observable, verifiable, and accountable.

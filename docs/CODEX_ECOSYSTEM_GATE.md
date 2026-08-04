# Codex Ecosystem Gate

The Codex integration branch is intentionally based on the current `main` branch.

## Release sequence

```text
Ω∞v contract
  -> runtime evidence
  -> MOOD
  -> pytest
  -> E2E
  -> Docker
  -> CI artifact
  -> GREEN
```

## Evidence rule

No component may claim `VERIFIED` from a static assertion alone. The verification layer must expose failed evidence as MOOD dissent and route it to human review.

## Convergence rule

Feature branches should be rebased/converged against current `main` before release validation. This prevents a green result on stale repository state from being mistaken for a green release.

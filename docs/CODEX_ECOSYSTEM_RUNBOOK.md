# Codex Ecosystem Runbook

## End-to-end gate

Run the current-main stack in this order:

```text
make test
  -> make doctor
  -> make boot
  -> make docker-build
  -> make stack
```

The gates are intentionally separated:

- `test` proves application regressions.
- `doctor` proves offline readiness/ledger integrity.
- `boot` proves the ratified invocation path.
- `docker-build` proves packaging.
- `stack` proves the aggregate test/container build boundary.

A CI green state is only authoritative when these commands execute in GitHub Actions. Local/demo success must not be represented as external CI verification.

## Ω∞v release rule

`CLEAR` means the evidence currently available satisfies the declared gate. `DISSENT` means evidence is missing, contradictory, or failed and must route to human review.

Attest, don't assert.

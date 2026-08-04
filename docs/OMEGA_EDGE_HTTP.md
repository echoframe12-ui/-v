# Ω∞v Edge HTTP Boundary v0.1

The Edge HTTP boundary is transport-only.

`POST /omega/edge/verify` accepts a signed Ω∞v attestation and delegates all trust decisions to `omega_edge.verify_edge_attestation()`.

## Contract

- `200`: attestation is valid
- `422`: attestation was supplied but verification failed
- `400`: request body is not a JSON object

The endpoint does not sign, re-sign, mutate, or reinterpret attestations.

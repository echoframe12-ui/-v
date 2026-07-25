# 0085 — Shareable Proof Page

## Context

The platform proves a single verified output three ways, none of them a page a person
can be handed: the receipt (`/attestations/<id>/receipt`) is JSON for a verifier, the
per-attestation badge (`DECISIONS/0084`) is a one-glance colour, and the terminal
`/receipt` command lives inside the terminal. A customer who wants to *show* that a
specific output was verified — link it in a report, a PR, a client deliverable — had
nothing human-readable to point to. The proof existed; a face for it did not.

## Decision

Add `GET /proof/<id>` — a self-contained, shareable verification certificate for one
attestation.

- Server-rendered `templates/proof.html`: the record's verdict (`ATTESTED` green,
  `HELD` amber, `TAMPERED` red), its subject and a plain-language line, the embedded
  per-attestation badge, and a facts grid — confidence against the threshold, chain
  position, seal, chain/entry integrity, actor, version (current or superseded),
  sources, and timestamp.
- A **"Verify this yourself"** section prints the content `sha256` and the exact
  commands to confirm the proof independently — `curl …/attestations/<id>/receipt`
  online, and `oceanic-os receipt --verify … --content-file …` offline.
- Built from the same `attestation_engine.receipt(id)` (plus supersession lineage) the
  receipt endpoint and badge use, with the verdict computed the same way the badge
  computes its colour, so the page cannot claim more than the receipt does. A missing
  id renders a `NOT FOUND` certificate at 404.

## Consequences

- A verified output now has a public face: verified live by screenshot, `/proof/1`
  renders a clean certificate — `ATTESTED`, the green `verified output` badge,
  `confidence 0.95 / 0.74`, `chain position 1/2`, `sealed · len 2`, the sources and
  timestamp, and a copy-pasteable verify block ending in the content hash. It is the
  page a customer links as proof, where before there was only JSON and a badge.
- It teaches verification instead of asking for trust: the certificate does not say
  "trust us" — it hands the reader the hash and the two commands to check it
  themselves, online or offline, which is the whole thesis of the platform made
  legible on one page.
- Honest by construction and derivation: the page is computed from the same receipt
  the machine endpoint serves, so a held record reads `HELD` (never dressed as
  attested) and a tampered one reads `TAMPERED` with the proof called void — the
  certificate steps down exactly where the record does, and states no fact the receipt
  does not.
- Additive and presentation-only: one route and one template over the existing
  receipt, embedding the existing badge and pointing at the existing verify tools. No
  new state, no change to any endpoint.

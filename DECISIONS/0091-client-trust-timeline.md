# 0091 — Client-Side Trust Timeline

## Context

Rounds `0087`–`0090` built the three trust histories — the CVI trend, the compounding
footprint, and the posture verdict — and gave them a human home at `/timeline`. But
the Python client SDK, the interface a monitor or automation actually uses, could not
reach them. It wrapped `/cvi`, `/status.json`, `/evolution`, and the verification
surfaces, yet none of the *over-time* endpoints. A consumer wanting to chart trust or
alert on a regression had to hand-roll requests to the very endpoints the SDK exists
to hide.

## Decision

Add the three histories and a one-call timeline to `OceanicOSClient`.

- `cvi_history(actor="", limit=None)`, `evolution_history(limit=None)`, and
  `posture_history(limit=None)` wrap `/cvi/history`, `/evolution/history`, and
  `/posture/history`, threading the same `actor`/`limit` query params those endpoints
  accept.
- `timeline(limit=None)` assembles all three into one dict —
  `{"cvi": …, "evolution": …, "posture": …}` — the data behind the `/timeline` page,
  so a monitor can pull "how has trust moved" in a single method instead of three
  requests.

## Consequences

- The SDK now covers the observability layer it was missing: verified live against a
  running service, `timeline()` returns the CVI trend (3 points), the growth summary
  (`gain 8`), and the posture transitions (`INTACT → TRUSTWORTHY`, current
  `TRUSTWORTHY`) in one call. A consumer can chart or alert on trust over time without
  leaving the client.
- Parity restored: the SDK already exposed every point-in-time surface (CVI, status,
  verify, digest, receipt, lineage) and every offline verifier (`verify_digest`,
  `verify_receipt`); adding the histories completes its read coverage so the library
  is a faithful proxy for the platform's public API, not a partial one.
- Exercised against the real routes: the client tests drive these through the Flask
  test-client opener, so the wrappers cannot drift from the endpoints' actual shapes,
  and `timeline`'s posture matches the standalone `posture_history` call.
- Additive and thin: read wrappers and one aggregating convenience over existing
  public endpoints — no new endpoint, no new state, and nothing existing changed.

# 0077 — Client-Side Digest Verification

## Context

The signed status digest exists for one scenario: hand a compact, HMAC-signed
posture to a third party over an untrusted channel, and let that party confirm it
genuinely came from this platform rather than being fabricated — *attest, don't
assert, even about your own health* (`DECISIONS/0075` put the dissent rate inside
that signature). The verification is a pure function, `status_digest.verify`.

But the Python client SDK — the "thin client a consumer copies to talk to the
platform" — could only *fetch* the digest (`status_digest()`). It gave a recipient
no way to *verify* one. An SDK user who received a digest had to reach past the
client into a server-side module (`status_digest`) and reconstruct the check by
hand. The one artifact designed to be verified by an outside party was the one
thing the outside party's library could not verify. The loop was open exactly
where it was supposed to close.

## Decision

Add `OceanicOSClient.verify_digest(key, digest=None)`.

- Pure, offline HMAC check — no network call, no trust in whatever transport
  delivered the digest. It needs only the shared operator `key`.
- Pass a `digest` received out of band, or omit it to fetch the platform's current
  one first — so `kai.verify_digest(key)` is the whole recipient story in one call.
- Returns `False` for an unsigned digest (no signature to check) and for any wrong
  key or tampered field.
- Verifies through the platform's own `status_digest.verify`, so the client checks
  a signature exactly the way the service produces one and cannot drift from the
  scheme — the same anti-drift discipline the injectable-opener tests already give
  the rest of the client.

## Consequences

- The recipient story is complete and demonstrable: verified live, an SDK consumer
  fetches a signed digest, verifies it locally with the right key (`True`), and
  watches a wrong key, a tampered `posture`, a tampered `cvi`, and a tampered
  `dissent_rate` each fail (`False`) — including the round-0075 guarantee that the
  dissent rate is inside what the signature covers. The party handed a digest can
  now check it with the same library they used to read the platform, and nothing
  else.
- Trust is transport-independent: because verification is a local HMAC over the
  canonical payload, a digest that arrives by email, a CI artifact, or a pasted
  blob is as verifiable as one fetched live — the SDK does not have to trust the
  channel, only the key. This is the property the signature was for, now reachable
  from the client.
- No new server surface and no drift: the endpoint and the signing module already
  existed; this adds one client method that delegates to the platform's own
  verifier. The client cannot verify differently from how the service signs,
  because it calls the very same function.
- Honest about the unsigned case: a digest from a platform with no signing key is
  reported as not-verified rather than silently accepted, so the client never turns
  an absent signature into a false assurance.

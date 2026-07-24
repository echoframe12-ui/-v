# 0081 — The Terminal's `/digest` Command

## Context

The signed status digest is the platform's flagship portable proof: a compact,
HMAC-signed snapshot of the posture that a third party can verify came from here
without a running service (`DECISIONS/0075`–`0079`). It is reachable from the API
(`/status/digest`), the CLI (`oceanic-os digest`), and the client SDK
(`verify_digest`). The one surface it was *not* reachable from was the one an actual
person uses: the cosmic verification terminal at `/`.

The terminal already lets a visitor query the record — `/status`, `/verify`,
`/cvi`, `/lookup`, `/receipt`, `/report`. The digest, arguably the most
demonstrative artifact the platform produces, was absent from the very place the
platform invites people to explore it.

## Decision

Add a `/digest` slash-command to the terminal.

- It fetches `/status/digest` and renders the posture as a glass card in the
  terminal's max-mood aesthetic: a verdict pill (`digest · TRUSTWORTHY` /
  `INTACT` / `BROKEN`), a one-line statement of what the digest *is* ("a portable,
  signed snapshot of the posture — hand it to anyone and they can confirm it came
  from here, no service needed"), and the signable facts — CVI, source coverage,
  dissent rate, held count, and the signature (truncated).
- When the platform has no signing key, the card reads "unsigned" for the signature
  and calls the snapshot unsigned, so the terminal never implies a signature the
  platform did not make — the same honesty the endpoint keeps.
- The command joins the `COMMANDS` map (so `/help` lists it) and the header hint.

## Consequences

- The flagship proof is now demonstrable where people actually look: verified live
  by screenshot, typing `/digest` in the terminal renders a `DIGEST · TRUSTWORTHY`
  card with `cvi 0.50 · sourced 67% · dissent 100% · held 1` and the signature
  `1d3d2b95ac53845b40…`, in the same cosmic mood as the rest of the terminal. A
  visitor can see, and copy, the portable posture without leaving the page.
- The terminal now spans the whole read surface: posture, chain, index, content
  lookup, per-item receipt, the human report, and the signed digest — the query
  half of "I don't generate; I attest" is complete against every artifact the
  platform signs or serves.
- Presentation-only and additive: a new client-side command over an existing public
  endpoint, no new route and no server change. `/`, the other commands, and every
  endpoint are untouched; a bare markup test asserts the terminal now carries the
  `/digest` command and its endpoint.
- Honest by construction, like the rest of the terminal: the card shows the real
  signed values the endpoint returns and names an unsigned digest as unsigned — it
  never dresses an unsigned snapshot as a proof.

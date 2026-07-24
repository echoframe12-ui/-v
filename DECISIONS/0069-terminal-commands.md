# 0069 — Verification-Terminal Commands

## Context

Round 67 made the OS face a conversational terminal, but it could do only one
thing: attest what you typed. A verification terminal that can only *write* to the
record and never *read* it is half a terminal. To ask "is the chain intact?" or
"was this exact output attested?" a user had to leave the chat for the console or
the raw endpoints — breaking the single-surface promise of the conversational
face.

## Decision

Give the chat slash-commands that query the record.

- Typing a claim still *attests* it (via `/builder/run`); typing a `/command`
  *queries* the record instead. `/status` (the posture), `/verify` (chain
  integrity), `/cvi` (the index with its interval and a meter), `/lookup <text>`
  (was this exact content attested?), `/report` (the full human report), and
  `/help`.
- Each is a thin client over an existing endpoint (`/status.json`,
  `/attestations/verify`, `/cvi`, `/attestations/lookup`, `/report`), rendered in
  the same glass-card, verdict-pill vocabulary as the attestations, so read and
  write responses read as one conversation.
- The intro card and placeholder advertise the commands, and unknown commands and
  errors fail gracefully into a `broken` verdict with the platform's own message.

## Consequences

- The face is now a whole terminal: verified live in a browser, `/status` returns
  `TRUSTWORTHY` with the CVI, peak, source coverage and held count; `/verify`
  reports "the ledger is intact across N links — the record attests to itself";
  `/cvi` draws the index as a meter; and `/lookup` on a known artifact returns
  `FOUND · attested 1× · latest confidence 0.92` with the content hash. You can
  read and write the record from one prompt.
- Presentation only — no new endpoint and no new state. The commands are a client
  over routes that already exist, so the terminal cannot report anything the API
  does not already serve, and it stays in sync with them for free.
- The read/write split is deliberate and legible: a bare claim goes through the
  panel with its 2500 ms friction (a *write* to the record earns its cost), while
  a command reads instantly (a *query* has nothing to hesitate over). The interface
  teaches which is which by how it behaves.
- The console remains the operator's full instrument at `/console`; the chat is the
  everyday terminal. Between them, every read and the primary write are reachable
  from the conversational face — the verification terminal the Doctrine describes,
  now able to both attest and answer *about the record* without pretending to
  answer the question.

# 0086 — The Honest Vibe Protocol

## Context

The "Full-Stack Vibe Protocol" arrived as a satirical manifesto casting OceanicOS as
friction-as-a-service — "we charge per Joule of Hesitation," "we own the abyss." Read
carefully it is two things at once: a set of genuine, on-thesis kernels the platform
already embodies, and a set of user-hostile or dishonest dark patterns dressed in the
same voice. This ADR does what the platform does to every doctrine — maps it to real
code and marks what is aspirational — and, unusually, records what was *rejected* and
why, because refusing the dark patterns is itself the decision.

## Decision

Ship the honest kernels; decline the dark patterns; document both.

### Realized (built)

- **"Expose the fracture lines, never the smoothed-over plaster"
  (`preferred_interpretation: null`)** → `models.route_all` now returns
  `preferred_interpretation: None`. The panel surfaces the full verdict distribution
  and the majority as data, but the platform never designates a single smoothed-over
  answer. The refusal is now an explicit, tested output field, not just an omission.
- **"We charge per Joule of Hesitation"** → the honest inversion. `friction.reading`
  keeps the one honest term of the satirical price formula — `(1 - confidence)`, how
  far a claim fell short of certainty — and drops the rest: no latency term (slowing a
  page to bill for it is a dark pattern), and no price. The proof page shows it as a
  **Scrutiny** reading with a plain phrase ("high scrutiny — held 0.34 below the 0.74
  bar") and the stance in words: *the scrutiny this claim drew, measured — never
  charged.* Hesitation is exposed for free, not sold.
- **"Refuse to automate the handshake" (the Gap Engine)** → already real, unchanged:
  a held attestation below `0.74` cannot be auto-consumed; a human steward must
  release it. The platform already refuses the automatic hand-off — honestly, without
  a modem squeal.
- **"The Triad / dissent-first"** → already real: the three-strategy panel plus the
  rules-engine anchor, with disagreement recorded as data (`consensus_log`,
  `/consensus/stats`, the signed digest's `dissent_rate`).

### Rejected (documented, deliberately not built)

Each is antithetical to the platform's *attest, don't assert / honest by construction*
thesis, or hostile to the user, so it is named here and left unbuilt:

- **Forced `usleep(2.5s)` latency-as-UX.** Deliberately slowing the interface to make
  latency the product is a dark pattern; the terminal's "render delay" is a cosmetic
  label, never real imposed delay.
- **The `<blink>` moving target that charges for mis-clicks.** Charging a user for a
  UI the platform designed to be mis-clicked is user-hostile. Rejected outright.
- **Serving a stale "more-proven hallucination" on rollback.** Returning old content
  and calling it more trustworthy is the exact opposite of attesting the truth of the
  current record. It would make the ledger lie. Never.
- **The acoustic modem-squeal key-exit ("Humanosecond").** Requiring a human to hold a
  microphone to a speaker to decrypt their own output is theater, not verification, and
  charges for friction manufactured on purpose.
- **Literal billing "per Joule of Hesitation."** The platform measures hesitation and
  shows it for free (`friction.reading`); it does not bill for uncertainty. The real
  pricing tiers (`/pricing`) charge for verification capability, not for a user's
  hesitation.

## Consequences

- The manifesto is answered honestly: the parts that are true to verification are now
  code — `preferred_interpretation: null` and the friction reading, verified live (a
  held claim reads `scrutiny 0.6 · high scrutiny — held 0.34 below the 0.74 bar`, an
  attested claim `clear of the bar`; the consensus response carries
  `preferred_interpretation: null`) — and the parts that would betray it are recorded
  as refused, with reasons.
- Friction is *measured, never charged*, and the page says so in words. The one honest
  term of the price formula becomes a free, legible signal of how much scrutiny a claim
  drew; the latency term is dropped by design, not by omission.
- The rejections are part of the record. Choosing not to build a dark pattern is a
  design decision the platform's own append-only decision log should carry, so the line
  it will not cross is as legible as the features it ships.
- Additive and honest: a new pure module (`friction.py`), one new output field, and one
  proof-page row over existing surfaces — no new state, no imposed latency, no charge,
  and nothing existing changed in behaviour.

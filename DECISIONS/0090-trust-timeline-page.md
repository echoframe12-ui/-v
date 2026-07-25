# 0090 — The Trust Timeline Page

## Context

Three rounds gave each headline signal a memory: the CVI (`/cvi/history`,
`DECISIONS/…`), the compounding footprint (`/evolution/history`, `0087`), and the
posture verdict (`/posture/history`, `0089`). But they lived in three separate JSON
endpoints. To answer the one question those histories exist for — "how has trust
moved" — an operator had to fetch three places and assemble the picture by hand. The
trend, the growth, and the verdict changes belonged on one page.

## Decision

Add `GET /timeline` — the three histories on a single trust-over-time page.

- `templates/timeline.html` renders three panels in the platform's cosmic aesthetic:
  the **CVI trend** (a normalized line over `/cvi/history`, with the current value and
  its span), the **compounding footprint** (a growth line over `/evolution/history`,
  with the latest total and the gain), and the **posture verdict** (the transition
  pills from `/posture/history`, `from → to` with timestamps, coloured by verdict, and
  the current posture).
- A pure client over the three existing public endpoints; the route is a thin
  `render_template`. Each panel degrades to its own empty state if its series is
  unreachable or empty, and the charts are drawn only from the recorded points —
  never smoothed or extrapolated.

## Consequences

- "How has trust moved" is now one page: verified live by screenshot, the timeline
  shows the CVI line (`0.85`, from `0.90`, 5 points), the growth line (`109`, `+16`
  since it began), and the posture pills (`INTACT → TRUSTWORTHY`, current
  `TRUSTWORTHY`) — the index, the footprint, and the verdict, each over time, side by
  side. The three memories become one view.
- Consistent with the platform's honesty discipline: every panel plots only the
  recorded series and shows an explicit empty state otherwise, so the page never draws
  a curve the histories don't contain — the same refusal of a fabricated point the
  sparkline badge and the becoming page already keep.
- Additive and presentation-only, like `/becoming`: a new page and route, a pure
  client over public endpoints, no new state and no new server logic. Every existing
  endpoint and page is untouched.
- Completes the time-series arc as a destination: rounds `0087`–`0089` built the three
  histories; this gives them a home an operator can link to and read at a glance,
  turning three data feeds into the platform's trust timeline.

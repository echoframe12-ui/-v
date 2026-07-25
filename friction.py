"""The friction a claim drew — measured, and shown for free. Never a charge.

The satirical Vibe Protocol proposed billing "per Joule of Hesitation":
`Price = Latency*0.01 + (1-Confidence)*100 + Disagreements*5`. This module keeps
the one honest term — `(1 - confidence)`, how far a claim fell short of certainty —
and drops the rest: no latency (deliberately slowing a page to bill for it is a dark
pattern), and no price at all. The platform's whole thesis is *attest, don't assert*;
so it exposes how much scrutiny a claim warranted rather than charging for it. The
panel-disagreement term of that formula is surfaced honestly elsewhere — the dissent
ledger and the consensus output's `preferred_interpretation: null`.

Pure functions over a confidence value, no state — the same discipline as `badge.py`
and `status_digest.py`.
"""
from __future__ import annotations

from typing import Any

from attestation import CONFIDENCE_THRESHOLD


def reading(confidence: float, threshold: float = CONFIDENCE_THRESHOLD) -> dict[str, Any]:
    """How much scrutiny a single claim drew — the honest `(1 - confidence)` term.

    `friction` is `round(1 - confidence, 2)` (0 = certain, 1 = no confidence at all),
    the normalized confidence-gap term of the Vibe Protocol's price formula with the
    latency term dropped and nothing billed. `below_threshold` and `gap` say whether,
    and by how much, the claim fell under the platform's `0.74` bar (held). `phrase`
    is a human reading, and `note` states the stance: measured, never charged.
    """
    try:
        conf = float(confidence)
    except (TypeError, ValueError):
        conf = 0.0
    conf = max(0.0, min(1.0, conf))
    friction = round(1.0 - conf, 2)
    below = conf < threshold
    gap = round(max(0.0, threshold - conf), 2)
    if below:
        phrase = f"high scrutiny — held {gap:.2f} below the {threshold:.2f} bar"
    elif friction <= 0.15:
        phrase = "low friction — attested, clear of the bar"
    else:
        phrase = "some friction — attested, but not far above the bar"
    return {
        "friction": friction,
        "below_threshold": below,
        "gap": gap,
        "threshold": threshold,
        "phrase": phrase,
        "note": "the scrutiny this claim drew, measured — never charged",
    }

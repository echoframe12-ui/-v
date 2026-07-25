"""Self-contained SVG status badges — the trust index, rendered for a README.

No external service (shields.io), no network, no fonts to embed: a badge is a
flat two-cell SVG whose width is approximated from the character count, so it
renders identically wherever it is served or cached. The colour is derived from
the value against the platform's own `0.74` confidence threshold, so a badge
tells the truth the same way the terminal does — green only when the record
genuinely earns it.

`CONTENT_TYPE` is the SVG mimetype; `cvi_color` maps a 0–1 index to a hue band;
`render` builds the two-cell badge. Pure functions, no state.
"""

CONTENT_TYPE = "image/svg+xml"

# Threshold-aligned colour bands. 0.74 is the platform's held/attested line
# (attestation.py, DECISIONS/0001): below it the record is not trustworthy, and
# the badge must not read green. The bands step down from there.
_GREEN = "#3fb950"
_YELLOW = "#d29922"
_ORANGE = "#db6d28"
_RED = "#f85149"
_GREY = "#8b949e"


def posture_color(posture):
    """Map a trust posture verdict to a colour.

    `TRUSTWORTHY` (chain intact, sealed head signed) is green; `INTACT` (intact
    but not yet sealed) is amber; `BROKEN` is red; anything else grey. The verdict
    is the whole-record answer the status board and digest already compute.
    """
    return {"TRUSTWORTHY": _GREEN, "INTACT": _YELLOW, "BROKEN": _RED}.get(posture, _GREY)


def cvi_color(value):
    """Map a CVI (0–1) to a colour band anchored on the 0.74 threshold.

    At or above threshold is green (trustworthy); a near-miss is yellow; the
    lower bands are orange then red. Values outside [0, 1] clamp to the ends,
    so a malformed index still yields a defined colour rather than an error.
    """
    try:
        v = float(value)
    except (TypeError, ValueError):
        return _GREY
    if v != v:  # NaN
        return _GREY
    v = max(0.0, min(1.0, v))
    if v >= 0.74:
        return _GREEN
    if v >= 0.6:
        return _YELLOW
    if v >= 0.4:
        return _ORANGE
    return _RED


def attestation_message(receipt):
    """Message and colour for a per-attestation badge, from its receipt.

    Shows one record's own verdict as an embeddable proof: a tampered entry (or a
    broken chain) reads red as `tampered` regardless of confidence — the proof is
    void, so the badge must not dress it up. Otherwise an attested record is green
    with its confidence, and a held record takes the threshold-aligned `cvi_color`
    of its confidence, so a below-`0.74` item never reads green. Pure over the
    receipt `verify_ledger`/the engine already produce.
    """
    att = receipt["attestation"]
    conf = att["confidence"]
    if not receipt.get("entry_intact", True) or not receipt.get("chain_intact", True):
        return "tampered", _RED
    if att["status"] == "attested":
        return f"attested {conf:.2f}", _GREEN
    return f"held {conf:.2f}", cvi_color(conf)


def _escape(text):
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _cell_width(text):
    # ~7px per glyph plus symmetric padding; good enough for a flat badge, and
    # deterministic so the SVG is byte-stable for caching.
    return len(str(text)) * 7 + 10


def render(label, message, color):
    """Return a flat two-cell SVG badge: grey `label` | coloured `message`.

    Width is derived from the text length so the cells always fit their
    content, and both strings are XML-escaped. `color` is used verbatim as the
    right cell's fill (see `cvi_color` for the CVI mapping).
    """
    label = _escape(label)
    message = _escape(message)
    lw = _cell_width(label)
    mw = _cell_width(message)
    total = lw + mw
    label_x = lw / 2
    message_x = lw + mw / 2
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{total}" height="20" '
        f'role="img" aria-label="{label}: {message}">'
        f'<title>{label}: {message}</title>'
        f'<linearGradient id="s" x2="0" y2="100%">'
        f'<stop offset="0" stop-color="#bbb" stop-opacity=".1"/>'
        f'<stop offset="1" stop-opacity=".1"/></linearGradient>'
        f'<clipPath id="r"><rect width="{total}" height="20" rx="3" fill="#fff"/></clipPath>'
        f'<g clip-path="url(#r)">'
        f'<rect width="{lw}" height="20" fill="#555"/>'
        f'<rect x="{lw}" width="{mw}" height="20" fill="{color}"/>'
        f'<rect width="{total}" height="20" fill="url(#s)"/></g>'
        f'<g fill="#fff" text-anchor="middle" '
        f'font-family="Verdana,Geneva,DejaVu Sans,sans-serif" font-size="11">'
        f'<text x="{label_x}" y="15" fill="#010101" fill-opacity=".3">{label}</text>'
        f'<text x="{label_x}" y="14">{label}</text>'
        f'<text x="{message_x}" y="15" fill="#010101" fill-opacity=".3">{message}</text>'
        f'<text x="{message_x}" y="14">{message}</text>'
        f'</g></svg>'
    )


def sparkline(values, label="records", color=_GREEN):
    """A compact trend badge: a grey `label N` cell | a sparkline of `values`.

    `values` is the series oldest→newest (e.g. `records_total` over time); the left
    cell shows the label and the latest value, the right cell draws the trend as a
    normalized polyline with a dot at the current point. Deterministic geometry so
    the SVG is byte-stable for caching. An empty series renders a flat baseline and a
    `0` — honest about having no trajectory yet, never a fabricated shape.
    """
    values = [v for v in (values or []) if isinstance(v, (int, float))]
    latest = int(values[-1]) if values else 0
    left = _escape(f"{label} {latest}")
    lw = _cell_width(left)
    chart_w, height, pad = 84, 20, 4
    total = lw + chart_w
    x0, x1 = lw + pad, total - pad
    y0, y1 = height - pad, pad
    if len(values) >= 2:
        lo, hi = min(values), max(values)
        span = (hi - lo) or 1
        n = len(values)
        pts = [
            (
                x0 + (x1 - x0) * i / (n - 1),
                y0 - (v - lo) / span * (y0 - y1),
            )
            for i, v in enumerate(values)
        ]
    else:
        mid = (y0 + y1) / 2
        pts = [(x0, mid), (x1, mid)]
    polyline = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    end_x, end_y = pts[-1]
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{total}" height="{height}" '
        f'role="img" aria-label="{left} trend">'
        f'<title>{left} (trend)</title>'
        f'<linearGradient id="s" x2="0" y2="100%">'
        f'<stop offset="0" stop-color="#bbb" stop-opacity=".1"/>'
        f'<stop offset="1" stop-opacity=".1"/></linearGradient>'
        f'<clipPath id="r"><rect width="{total}" height="{height}" rx="3" fill="#fff"/></clipPath>'
        f'<g clip-path="url(#r)">'
        f'<rect width="{lw}" height="{height}" fill="#555"/>'
        f'<rect x="{lw}" width="{chart_w}" height="{height}" fill="#0d1117"/>'
        f'<rect width="{total}" height="{height}" fill="url(#s)"/></g>'
        f'<polyline fill="none" stroke="{color}" stroke-width="1.5" '
        f'stroke-linejoin="round" stroke-linecap="round" points="{polyline}"/>'
        f'<circle cx="{end_x:.1f}" cy="{end_y:.1f}" r="1.8" fill="{color}"/>'
        f'<g fill="#fff" text-anchor="middle" '
        f'font-family="Verdana,Geneva,DejaVu Sans,sans-serif" font-size="11">'
        f'<text x="{lw/2:.0f}" y="15" fill="#010101" fill-opacity=".3">{left}</text>'
        f'<text x="{lw/2:.0f}" y="14">{left}</text>'
        f'</g></svg>'
    )

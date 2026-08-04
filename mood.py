"""MOOD: operational observation and dissent layer for OceanicOS."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class MoodSignal:
    name: str
    value: Any
    source: str
    confidence: float = 1.0


@dataclass(frozen=True)
class MoodAssessment:
    status: str
    gaps: tuple[str, ...] = field(default_factory=tuple)
    evidence: tuple[MoodSignal, ...] = field(default_factory=tuple)
    route: str = "continue"

    @property
    def requires_human(self) -> bool:
        return self.route == "human"


def assess(signals: list[MoodSignal]) -> MoodAssessment:
    """Surface disagreement or low confidence instead of hiding it."""
    gaps: list[str] = []
    for signal in signals:
        if not 0.0 <= signal.confidence <= 1.0:
            gaps.append(f"invalid-confidence:{signal.name}")
        elif signal.confidence < 0.5:
            gaps.append(f"low-confidence:{signal.name}")
        elif signal.value is False:
            gaps.append(f"failed:{signal.name}")

    by_name: dict[str, list[Any]] = {}
    for signal in signals:
        by_name.setdefault(signal.name, []).append(signal.value)

    for name, values in by_name.items():
        if len(set(map(repr, values))) > 1:
            gaps.append(f"dissent:{name}")

    route = "human" if gaps else "continue"
    return MoodAssessment(
        status="dissent" if gaps else "clear",
        gaps=tuple(gaps),
        evidence=tuple(signals),
        route=route,
    )


def _assessment_payload(assessment: MoodAssessment) -> dict[str, Any]:
    """Build a ledger-safe payload from a MoodAssessment."""
    return {
        "status": assessment.status,
        "route": assessment.route,
        "gaps": list(assessment.gaps),
        "signal_count": len(assessment.evidence),
        "signals": [
            {"name": s.name, "value": s.value, "source": s.source, "confidence": s.confidence}
            for s in assessment.evidence
        ],
    }


def record_to_ledger(
    assessment: MoodAssessment,
    ledger: Any,
    *,
    entity_id: str = "mood-assessment",
) -> Any:
    """Emit a mood.clear or mood.dissent event into the EventLedger.

    Returns the LedgerEvent created. The ``ledger`` must expose an
    ``append(event_type, entity_id, payload)`` method compatible with
    :class:`oceanic_event_ledger.EventLedger`.
    """
    event_type = f"mood.{assessment.status}"
    payload = _assessment_payload(assessment)
    return ledger.append(event_type, entity_id, payload)


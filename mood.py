"""MOOD: operational observation and dissent layer for OceanicOS."""

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
        if signal.confidence < 0.5:
            gaps.append(f"low-confidence:{signal.name}")

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

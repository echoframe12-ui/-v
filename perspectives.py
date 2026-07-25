from __future__ import annotations

"""Provider-neutral perspective contracts for Ω∞ Oceanic."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Protocol

from context_assembly import ContextAssembly


@dataclass(frozen=True)
class Perspective:
    """A model/provider response with traceable context provenance."""

    id: str
    provider: str
    model: str
    response: Any
    context_hash: str
    source_refs: tuple[str, ...]
    timestamp: str
    confidence: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class PerspectiveAdapter(Protocol):
    """Minimal adapter boundary for local, hosted, or open-weight models."""

    provider: str
    model: str

    def generate(self, context: ContextAssembly) -> Perspective:
        ...


def make_perspective(
    *,
    perspective_id: str,
    provider: str,
    model: str,
    response: Any,
    context: ContextAssembly,
    confidence: float | None = None,
    metadata: dict[str, Any] | None = None,
) -> Perspective:
    """Construct a perspective while preserving the context lineage."""
    if confidence is not None and not 0.0 <= confidence <= 1.0:
        raise ValueError("confidence must be between 0.0 and 1.0")

    return Perspective(
        id=perspective_id,
        provider=provider,
        model=model,
        response=response,
        context_hash=context.content_hash,
        source_refs=context.included_refs,
        timestamp=datetime.now(timezone.utc).isoformat(),
        confidence=confidence,
        metadata=metadata or {},
    )


def compare_perspectives(perspectives: list[Perspective]) -> dict[str, Any]:
    """Return an auditable comparison without selecting a winner."""
    if not perspectives:
        return {
            "perspectives": [],
            "dissent": False,
            "context_hashes": [],
            "preferred_interpretation": None,
        }

    responses = [perspective.response for perspective in perspectives]
    return {
        "perspectives": [perspective.id for perspective in perspectives],
        "providers": [perspective.provider for perspective in perspectives],
        "models": [perspective.model for perspective in perspectives],
        "responses": responses,
        "context_hashes": sorted({perspective.context_hash for perspective in perspectives}),
        "source_refs": sorted({ref for p in perspectives for ref in p.source_refs}),
        "dissent": len({repr(response) for response in responses}) > 1,
        "preferred_interpretation": None,
    }

from __future__ import annotations

"""Provider-neutral perspective contracts for Ω∞ Oceanic."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Protocol, Sequence

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
    repr_responses = [repr(r) for r in responses]
    majority_repr = max(set(repr_responses), key=repr_responses.count) if repr_responses else None
    majority_index = repr_responses.index(majority_repr) if majority_repr is not None else None
    majority = responses[majority_index] if majority_index is not None else None

    return {
        "perspectives": [perspective.id for perspective in perspectives],
        "providers": [perspective.provider for perspective in perspectives],
        "models": [perspective.model for perspective in perspectives],
        "responses": responses,
        # Legacy aliases used by consensus_log.record and other callers
        "verdicts": responses,
        "majority": majority,
        "adapters": [perspective.provider for perspective in perspectives],
        "context_hashes": sorted({perspective.context_hash for perspective in perspectives}),
        "source_refs": sorted({ref for p in perspectives for ref in p.source_refs}),
        "dissent": len(set(repr_responses)) > 1,
        "preferred_interpretation": None,
    }


class MockPerspectiveAdapter:
    """Mock perspective adapter for testing or local rules-based evaluations."""

    def __init__(self, provider: str, model: str, response: Any = "approve", confidence: float | None = 0.95):
        self.provider = provider
        self.model = model
        self.response = response
        self.confidence = confidence

    def generate(self, context: ContextAssembly) -> Perspective:
        return make_perspective(
            perspective_id=f"{self.provider}-{self.model}-{context.content_hash[:8]}",
            provider=self.provider,
            model=self.model,
            response=self.response,
            context=context,
            confidence=self.confidence,
        )


class PerspectiveRegistry:
    """Registry managing multiple model adapters for multi-perspective evaluations."""

    def __init__(self, adapters: Sequence[PerspectiveAdapter] = ()) -> None:
        self._adapters: list[PerspectiveAdapter] = list(adapters)

    def register(self, adapter: PerspectiveAdapter) -> None:
        self._adapters.append(adapter)

    def evaluate_all(self, context: ContextAssembly) -> list[Perspective]:
        return [adapter.generate(context) for adapter in self._adapters]

    def compare_all(self, context: ContextAssembly) -> dict[str, Any]:
        perspectives = self.evaluate_all(context)
        return compare_perspectives(perspectives)

    def list_adapters(self) -> list[dict]:
        return [{"provider": a.provider, "model": a.model} for a in self._adapters]


def create_live_registry() -> PerspectiveRegistry:
    """Build a PerspectiveRegistry populated with real API adapters if credentials exist."""
    import os
    registry = PerspectiveRegistry()

    if os.getenv("ANTHROPIC_API_KEY"):
        try:
            from claude_perspective import ClaudePerspectiveAdapter
            registry.register(ClaudePerspectiveAdapter())
        except ImportError:
            pass

    if os.getenv("OPENAI_API_KEY"):
        try:
            from openai_perspective import OpenAIPerspectiveAdapter
            registry.register(OpenAIPerspectiveAdapter())
        except ImportError:
            pass

    if not registry._adapters:
        # Fallback to local mock if no API keys are present
        registry.register(MockPerspectiveAdapter("local", "mock-fallback"))

    return registry

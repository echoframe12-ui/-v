from __future__ import annotations

"""Minimal executable Context → Perspectives → Dissent pipeline."""

from dataclasses import dataclass
from typing import Any, Iterable

from context_assembly import ContextAssembler, ContextSource
from perspectives import Perspective, PerspectiveAdapter, compare_perspectives


@dataclass(frozen=True)
class IntegrationResult:
    context: Any
    perspectives: tuple[Perspective, ...]
    comparison: dict[str, Any]


class IntegrationPipeline:
    """Connect context assembly to provider-neutral perspective adapters."""

    def __init__(self, adapters: Iterable[PerspectiveAdapter], max_chars: int | None = None):
        self.adapters = tuple(adapters)
        self.assembler = ContextAssembler(max_chars=max_chars)

    def run(self, sources: Iterable[ContextSource]) -> IntegrationResult:
        context = self.assembler.assemble(sources)
        perspectives = tuple(adapter.generate(context) for adapter in self.adapters)
        comparison = compare_perspectives(list(perspectives))
        return IntegrationResult(
            context=context,
            perspectives=perspectives,
            comparison=comparison,
        )

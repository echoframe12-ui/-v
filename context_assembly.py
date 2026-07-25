from __future__ import annotations

"""Auditable, provider-neutral context assembly for Ω∞ Oceanic.

Context is treated as evidence with explicit provenance, not as truth.
"""

from dataclasses import asdict, dataclass, field
import hashlib
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class ContextSource:
    """A source included in an assembled context field."""

    ref: str
    content: str
    authority: str = "unknown"
    timestamp: str | None = None
    metadata: dict[str, str] = field(default_factory=dict)

    @property
    def content_hash(self) -> str:
        return hashlib.sha256(self.content.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ContextAssembly:
    """Serializable result of context assembly."""

    sources: tuple[dict, ...]
    included_refs: tuple[str, ...]
    omitted_refs: tuple[str, ...]
    content: str
    content_hash: str
    truncated: bool
    max_chars: int | None


class ContextAssembler:
    """Build a deterministic, provenance-preserving context field.

    The assembler never silently drops sources. If a character budget is
    exceeded, omitted references and truncation are explicitly recorded.
    """

    def __init__(self, max_chars: int | None = None) -> None:
        if max_chars is not None and max_chars <= 0:
            raise ValueError("max_chars must be positive or None")
        self.max_chars = max_chars

    def assemble(self, sources: Iterable[ContextSource]) -> ContextAssembly:
        ordered = list(sources)
        included: list[ContextSource] = []
        omitted: list[str] = []
        chunks: list[str] = []
        used = 0
        truncated = False

        for source in ordered:
            block = f"[{source.ref}]\n{source.content}"
            separator = "\n\n" if chunks else ""
            required = len(separator) + len(block)

            if self.max_chars is not None and used + required > self.max_chars:
                omitted.append(source.ref)
                truncated = True
                continue

            chunks.append(block)
            included.append(source)
            used += required

        content = "\n\n".join(chunks)
        return ContextAssembly(
            sources=tuple(asdict(source) | {"content_hash": source.content_hash} for source in included),
            included_refs=tuple(source.ref for source in included),
            omitted_refs=tuple(omitted),
            content=content,
            content_hash=hashlib.sha256(content.encode("utf-8")).hexdigest(),
            truncated=truncated,
            max_chars=self.max_chars,
        )

    def from_files(self, paths: Iterable[str | Path]) -> ContextAssembly:
        sources = [
            ContextSource(ref=str(path), content=Path(path).read_text(encoding="utf-8"))
            for path in paths
        ]
        return self.assemble(sources)

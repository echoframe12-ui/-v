from __future__ import annotations

"""Contract-oriented multi-adapter verification orchestrator."""

from dataclasses import dataclass, field
from typing import Any, Protocol, Sequence

from oceanic_ir import OceanicIRContract


@dataclass(frozen=True)
class AdapterResult:
    language: str
    supported: bool
    proof: dict[str, Any] = field(default_factory=dict)
    dissent: tuple[str, ...] = ()
    confidence: float = 0.0


@dataclass(frozen=True)
class CompilationReport:
    contract_id: str
    results: tuple[AdapterResult, ...]

    @property
    def supported_results(self) -> tuple[AdapterResult, ...]:
        return tuple(result for result in self.results if result.supported)

    @property
    def dissent(self) -> tuple[str, ...]:
        return tuple(
            message
            for result in self.results
            for message in result.dissent
        )

    @property
    def confidence(self) -> float:
        if not self.results:
            return 0.0
        return sum(result.confidence for result in self.results) / len(self.results)


class OceanicAdapter(Protocol):
    language: str

    def verify(self, contract: OceanicIRContract) -> AdapterResult:
        ...


class ContractAdapter:
    """A deterministic baseline adapter used until language-specific adapters exist."""

    def __init__(self, language: str, capabilities: Sequence[str] = ()):
        self.language = language
        self.capabilities = frozenset(capabilities)

    def verify(self, contract: OceanicIRContract) -> AdapterResult:
        missing = tuple(
            obligation
            for obligation in contract.proof_obligations
            if obligation not in self.capabilities
        )
        dissent = tuple(
            f"{self.language}: cannot prove {obligation}"
            for obligation in missing
        )
        supported = not missing
        proof = {
            "type": "capability_attestation",
            "language": self.language,
            "capabilities": sorted(self.capabilities),
            "covered_obligations": [
                obligation
                for obligation in contract.proof_obligations
                if obligation in self.capabilities
            ],
        }
        confidence = 1.0 if supported else (
            len(contract.proof_obligations) - len(missing)
        ) / max(1, len(contract.proof_obligations))
        return AdapterResult(
            language=self.language,
            supported=supported,
            proof=proof,
            dissent=dissent,
            confidence=confidence,
        )


class OceanicOrchestrator:
    def __init__(self, adapters: Sequence[OceanicAdapter]):
        self.adapters = tuple(adapters)

    def run(self, contract: OceanicIRContract) -> CompilationReport:
        results = tuple(adapter.verify(contract) for adapter in self.adapters)
        return CompilationReport(contract_id=contract.contract_id, results=results)


def default_adapters() -> tuple[OceanicAdapter, ...]:
    """Return conservative baseline perspectives for initial local verification.

    These are contract-verification perspectives, not language runtimes. Real
    Python/Rust/TypeScript adapters can replace or extend them later.
    """
    return (
        ContractAdapter(
            "python",
            capabilities=("arithmetic_correctness",),
        ),
        ContractAdapter(
            "rust",
            capabilities=("arithmetic_correctness", "overflow_handling"),
        ),
        ContractAdapter(
            "typescript",
            capabilities=("arithmetic_correctness",),
        ),
    )

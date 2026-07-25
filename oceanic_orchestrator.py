from __future__ import annotations

"""Multi-adapter orchestration for the Ω∞ Oceanic verification compiler."""

from dataclasses import dataclass
from typing import Any, Callable

from oceanic_ir import (
    AdapterManifest,
    ContractState,
    OceanicIRContract,
    OceanicIRValidator,
    ProofArtifact,
    VerificationOutcome,
)


@dataclass(frozen=True)
class AdapterRun:
    language: str
    manifest: AdapterManifest
    implementation_digest: str
    outcome: VerificationOutcome


@dataclass(frozen=True)
class VerificationReport:
    contract_id: str
    runs: tuple[AdapterRun, ...]
    overall_status: ContractState
    dissent: tuple[str, ...]
    confidence: float


@dataclass(frozen=True)
class AdapterDefinition:
    manifest: AdapterManifest
    compile_contract: Callable[[OceanicIRContract], Any]
    prove_contract: Callable[[OceanicIRContract, Any], ProofArtifact]


class OceanicOrchestrator:
    """Compile and verify one contract through multiple independent adapters."""

    def __init__(self, adapters: tuple[AdapterDefinition, ...]):
        self.adapters = adapters
        self.validator = OceanicIRValidator()

    def run(self, contract: OceanicIRContract) -> VerificationReport:
        self.validator.validate_contract(contract)
        runs: list[AdapterRun] = []
        dissent: list[str] = []

        for adapter in self.adapters:
            artifact = adapter.compile_contract(contract)
            proof = adapter.prove_contract(contract, artifact)
            outcome = self.validator.verify(contract, proof)
            runs.append(
                AdapterRun(
                    language=adapter.manifest.language,
                    manifest=adapter.manifest,
                    implementation_digest=artifact.implementation_digest,
                    outcome=outcome,
                )
            )
            dissent.extend(
                f"{adapter.manifest.language}: {item}" for item in outcome.dissent
            )

        if not runs:
            return VerificationReport(
                contract_id=contract.contract_id,
                runs=(),
                overall_status=ContractState.UNPROVEN,
                dissent=("no adapters available",),
                confidence=0.0,
            )

        statuses = {run.outcome.status for run in runs}
        if ContractState.REJECTED in statuses or ContractState.FAILED in statuses:
            overall = ContractState.REJECTED
        elif ContractState.UNPROVEN in statuses:
            overall = ContractState.UNPROVEN
        elif ContractState.PROVED_WITH_DISSENT in statuses:
            overall = ContractState.PROVED_WITH_DISSENT
        else:
            overall = ContractState.PROVED

        confidence = round(
            sum(run.outcome.confidence or 0.0 for run in runs) / len(runs),
            3,
        )

        return VerificationReport(
            contract_id=contract.contract_id,
            runs=tuple(runs),
            overall_status=overall,
            dissent=tuple(sorted(set(dissent))),
            confidence=confidence,
        )


def default_adapters() -> tuple[AdapterDefinition, ...]:
    """Load the three reference perspectives without coupling the verifier to them."""
    from adapters.python_adapter import MANIFEST as PYTHON_MANIFEST
    from adapters.python_adapter import compile_contract as python_compile
    from adapters.python_adapter import prove_contract as python_prove
    from adapters.rust_adapter import MANIFEST as RUST_MANIFEST
    from adapters.rust_adapter import compile_contract as rust_compile
    from adapters.rust_adapter import prove_contract as rust_prove
    from adapters.typescript_adapter import MANIFEST as TS_MANIFEST
    from adapters.typescript_adapter import compile_contract as ts_compile
    from adapters.typescript_adapter import prove_contract as ts_prove

    return (
        AdapterDefinition(PYTHON_MANIFEST, python_compile, python_prove),
        AdapterDefinition(RUST_MANIFEST, rust_compile, rust_prove),
        AdapterDefinition(TS_MANIFEST, ts_compile, ts_prove),
    )

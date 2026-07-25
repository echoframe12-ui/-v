from __future__ import annotations

"""Oceanic IR contract kernel for Ω∞ Oceanic.

Oceanic IR is a verification contract, not a programming language.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ContractState(str, Enum):
    PROVED = "proved"
    PROVED_WITH_DISSENT = "proved_with_dissent"
    UNPROVEN = "unproven"
    REJECTED = "rejected"
    FAILED = "failed"


@dataclass(frozen=True)
class OceanicIRContract:
    api_version: str
    contract_id: str
    intent: str
    inputs: tuple[dict[str, Any], ...]
    outputs: dict[str, Any]
    invariants: tuple[str, ...]
    effects: tuple[str, ...]
    bounds: dict[str, str]
    dependencies: tuple[str, ...]
    proof_obligations: tuple[str, ...]
    dissent_triggers: tuple[str, ...]
    risk: dict[str, Any]


@dataclass(frozen=True)
class AdapterManifest:
    protocol: str
    language: str
    language_version: str
    adapter_version: str
    capabilities: tuple[str, ...]
    proof_types: tuple[str, ...]
    limitations: tuple[str, ...]
    local_first: bool = True
    dissent_mode: str = "surface_first"


@dataclass(frozen=True)
class ProofClaim:
    obligation: str
    status: str
    evidence_type: str
    evidence_digest: str


@dataclass(frozen=True)
class ProofArtifact:
    contract_id: str
    adapter: AdapterManifest
    implementation_digest: str
    toolchain_digest: str
    claims: tuple[ProofClaim, ...]
    limitations: tuple[str, ...] = field(default_factory=tuple)
    dissent: tuple[str, ...] = field(default_factory=tuple)
    reproducibility: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class VerificationOutcome:
    status: ContractState
    confidence: float | None
    satisfied_obligations: tuple[str, ...]
    missing_obligations: tuple[str, ...]
    dissent: tuple[str, ...]


class OceanicIRValidator:
    """Validate contracts, manifests, and proof artifacts.

    The validator checks coverage and declared capability matches. It does not
    attempt full program verification.
    """

    def validate_contract(self, contract: OceanicIRContract) -> None:
        if not contract.api_version:
            raise ValueError("contract requires api_version")
        if not contract.contract_id:
            raise ValueError("contract requires contract_id")
        if not contract.intent:
            raise ValueError("contract requires intent")
        if not contract.proof_obligations:
            raise ValueError("contract requires at least one proof obligation")
        if not contract.risk:
            raise ValueError("contract requires risk metadata")

    def validate_manifest(self, manifest: AdapterManifest) -> None:
        if not manifest.protocol:
            raise ValueError("manifest requires protocol")
        if not manifest.language:
            raise ValueError("manifest requires language")
        if not manifest.language_version:
            raise ValueError("manifest requires language_version")
        if not manifest.adapter_version:
            raise ValueError("manifest requires adapter_version")
        if not manifest.capabilities:
            raise ValueError("manifest requires capabilities")
        if not manifest.proof_types:
            raise ValueError("manifest requires proof_types")

    def verify(self, contract: OceanicIRContract, proof: ProofArtifact) -> VerificationOutcome:
        self.validate_contract(contract)
        self.validate_manifest(proof.adapter)

        if proof.contract_id != contract.contract_id:
            return VerificationOutcome(
                status=ContractState.REJECTED,
                confidence=0.0,
                satisfied_obligations=(),
                missing_obligations=contract.proof_obligations,
                dissent=("contract_id mismatch",),
            )

        obligations = set(contract.proof_obligations)
        satisfied = {claim.obligation for claim in proof.claims if claim.status == "satisfied"}
        missing = tuple(sorted(obligations - satisfied))
        dissent = tuple(sorted(set(proof.dissent) | {claim.obligation for claim in proof.claims if claim.status != "satisfied"}))

        if missing:
            return VerificationOutcome(
                status=ContractState.UNPROVEN,
                confidence=self._confidence(contract, proof, satisfied, obligations),
                satisfied_obligations=tuple(sorted(satisfied)),
                missing_obligations=missing,
                dissent=dissent,
            )

        state = ContractState.PROVED_WITH_DISSENT if dissent else ContractState.PROVED
        return VerificationOutcome(
            status=state,
            confidence=self._confidence(contract, proof, satisfied, obligations),
            satisfied_obligations=tuple(sorted(satisfied)),
            missing_obligations=(),
            dissent=dissent,
        )

    def match_capabilities(self, contract: OceanicIRContract, manifest: AdapterManifest) -> tuple[bool, tuple[str, ...]]:
        required = set(contract.proof_obligations)
        capabilities = set(manifest.capabilities)
        missing = tuple(sorted(required - capabilities))
        return (len(missing) == 0, missing)

    @staticmethod
    def _confidence(
        contract: OceanicIRContract,
        proof: ProofArtifact,
        satisfied: set[str],
        obligations: set[str],
    ) -> float:
        if not obligations:
            return 0.0
        base = len(satisfied) / len(obligations)
        bonus = 0.1 if not proof.dissent else 0.0
        penalty = 0.05 * len(proof.limitations)
        confidence = max(0.0, min(1.0, base + bonus - penalty))
        return round(confidence, 3)

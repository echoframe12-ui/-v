from __future__ import annotations

"""Minimal, serializable Oceanic verification contract.

The IR is intentionally a contract, not a programming language. It describes
intent, invariants, effects, bounds, dependencies, proof obligations, dissent
triggers, and risk so adapters can implement and prove the contract.
"""

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence


@dataclass(frozen=True)
class OceanicIRContract:
    api_version: str
    contract_id: str
    intent: str
    inputs: Sequence[Mapping[str, Any]] = field(default_factory=tuple)
    outputs: Mapping[str, Any] = field(default_factory=dict)
    invariants: Sequence[str] = field(default_factory=tuple)
    effects: Sequence[str] = field(default_factory=tuple)
    bounds: Mapping[str, Any] = field(default_factory=dict)
    dependencies: Sequence[str] = field(default_factory=tuple)
    proof_obligations: Sequence[str] = field(default_factory=tuple)
    dissent_triggers: Sequence[str] = field(default_factory=tuple)
    risk: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.api_version:
            raise ValueError("api_version is required")
        if not self.contract_id:
            raise ValueError("contract_id is required")
        if not self.intent:
            raise ValueError("intent is required")

    def to_dict(self) -> dict[str, Any]:
        return {
            "api_version": self.api_version,
            "contract_id": self.contract_id,
            "intent": self.intent,
            "inputs": [dict(item) for item in self.inputs],
            "outputs": dict(self.outputs),
            "invariants": list(self.invariants),
            "effects": list(self.effects),
            "bounds": dict(self.bounds),
            "dependencies": list(self.dependencies),
            "proof_obligations": list(self.proof_obligations),
            "dissent_triggers": list(self.dissent_triggers),
            "risk": dict(self.risk),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "OceanicIRContract":
        return cls(
            api_version=str(data["api_version"]),
            contract_id=str(data["contract_id"]),
            intent=str(data["intent"]),
            inputs=tuple(data.get("inputs", ())),
            outputs=dict(data.get("outputs", {})),
            invariants=tuple(data.get("invariants", ())),
            effects=tuple(data.get("effects", ())),
            bounds=dict(data.get("bounds", {})),
            dependencies=tuple(data.get("dependencies", ())),
            proof_obligations=tuple(data.get("proof_obligations", ())),
            dissent_triggers=tuple(data.get("dissent_triggers", ())),
            risk=dict(data.get("risk", {})),
        )

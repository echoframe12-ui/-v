from __future__ import annotations

"""End-to-end Ω∞ Oceanic cycle: source → stack → observer → becoming."""

from dataclasses import dataclass
from typing import Any, Iterable

from continuous_becoming import BecomingTransition, ContinuousBecomingEngine
from context_assembly import ContextSource
from observer import Observation, Observer
from stack_runner import OceanicStack, StackRun


@dataclass(frozen=True)
class EcosystemCycle:
    stack_run: StackRun
    observation: Observation
    transition: BecomingTransition


class EcosystemCycleEngine:
    """Run the full observable cycle without bypassing evidence or policy."""

    def __init__(self, stack: OceanicStack):
        self.stack = stack
        self.observer = Observer()
        self.becoming = ContinuousBecomingEngine()

    def run(self, sources: Iterable[ContextSource]) -> EcosystemCycle:
        stack_run = self.stack.run(sources)
        observation = self.observer.observe(stack_run)
        transition = self.becoming.advance(observation)
        return EcosystemCycle(stack_run=stack_run, observation=observation, transition=transition)

    @staticmethod
    def to_dict(cycle: EcosystemCycle) -> dict[str, Any]:
        return {
            "stack_run": {
                "integration": {
                    "context_hash": cycle.stack_run.integration.context.content_hash,
                    "included_refs": list(cycle.stack_run.integration.context.included_refs),
                    "omitted_refs": list(cycle.stack_run.integration.context.omitted_refs),
                    "dissent": cycle.stack_run.integration.comparison.get("dissent", False),
                },
                "verification": {
                    "status": cycle.stack_run.verification.status,
                    "confidence": cycle.stack_run.verification.confidence,
                    "dissent": cycle.stack_run.verification.dissent,
                    "provenance": list(cycle.stack_run.verification.provenance),
                    "result_hash": cycle.stack_run.verification.result_hash,
                },
                "attestation": None
                if cycle.stack_run.attestation is None
                else {
                    "status": cycle.stack_run.attestation.status,
                    "confidence": cycle.stack_run.attestation.confidence,
                    "provenance": list(cycle.stack_run.attestation.provenance),
                    "verification_hash": cycle.stack_run.attestation.verification_hash,
                },
                "authorization": {
                    "level": cycle.stack_run.authorization.level.value,
                    "requires_human": cycle.stack_run.authorization.requires_human,
                    "reason": cycle.stack_run.authorization.reason,
                },
            },
            "observation": Observer.to_dict(cycle.observation),
            "transition": ContinuousBecomingEngine.to_dict(cycle.transition),
        }

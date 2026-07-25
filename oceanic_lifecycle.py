from __future__ import annotations

"""Single coordinator for the Ω∞ Oceanic evidence lifecycle.

This layer composes existing components. It does not mutate contracts or
historical attestations; it records lifecycle transitions in an append-only
ledger and returns explicit evolution proposals for human review.
"""

from dataclasses import dataclass
from typing import Any, Callable

from oceanic_attestation import Attestation, create_attestation
from oceanic_authorization import Authorization, authorize
from oceanic_evolution import EvolutionProposal, propose_evolution
from oceanic_event_ledger import EventLedger
from oceanic_observer import Observation, execute_and_observe
from oceanic_orchestrator import CompilationReport, OceanicOrchestrator
from oceanic_ir import OceanicIRContract


@dataclass(frozen=True)
class LifecycleResult:
    report: CompilationReport
    attestation: Attestation
    authorization: Authorization
    observation: Observation
    evolution: EvolutionProposal | None


class OceanicLifecycle:
    def __init__(self, orchestrator: OceanicOrchestrator, ledger: EventLedger):
        self.orchestrator = orchestrator
        self.ledger = ledger

    def run(
        self,
        contract: OceanicIRContract,
        *,
        reviewer: str,
        authorization_reason: str,
        execute: Callable[[], Any],
        expected: Any,
    ) -> LifecycleResult:
        self.ledger.append("contract.created", contract.contract_id, {"intent": contract.intent})

        report = self.orchestrator.run(contract)
        self.ledger.append(
            "verification.completed",
            contract.contract_id,
            {"adapter_count": len(report.results)},
        )

        attestation = create_attestation(report)
        self.ledger.append(
            "attestation.created",
            attestation.attestation_id,
            {"contract_id": attestation.contract_id},
        )

        authorization = authorize(
            attestation,
            reviewer=reviewer,
            reason=authorization_reason,
        )
        self.ledger.append(
            "authorization.granted",
            attestation.attestation_id,
            {"reviewer": reviewer},
        )

        updated_attestation, observation = execute_and_observe(
            authorization,
            execute=execute,
            expected=expected,
        )
        self.ledger.append(
            "runtime.observed",
            attestation.attestation_id,
            {
                "status": observation.status,
                "runtime_digest": observation.runtime_digest,
            },
        )

        self.ledger.append(
            f"observation.{observation.status}",
            attestation.attestation_id,
            {"deviations": list(observation.deviations)},
        )

        evolution = propose_evolution(updated_attestation, observation)
        if evolution is not None:
            self.ledger.append(
                "evolution.proposed",
                evolution.proposal_id,
                {
                    "contract_id": evolution.contract_id,
                    "category": evolution.category,
                    "requires_human_review": evolution.requires_human_review,
                },
            )
            self.ledger.append(
                "human.review.required",
                evolution.proposal_id,
                {"reason": evolution.reason},
            )

        return LifecycleResult(
            report=report,
            attestation=updated_attestation,
            authorization=authorization,
            observation=observation,
            evolution=evolution,
        )

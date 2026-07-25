from __future__ import annotations

"""Single orchestration boundary for the Ω∞ Oceanic full-stack flow."""

from dataclasses import dataclass
from typing import Iterable

from authorization import AuthorizationDecision, AuthorizationGate
from context_assembly import ContextSource
from integration_pipeline import IntegrationPipeline, IntegrationResult
from proactive import Proposal, ProposalDecision, ProactiveEngine
from verification_pipeline import Attestation, VerificationPipeline, VerificationResult


@dataclass(frozen=True)
class StackRun:
    integration: IntegrationResult
    verification: VerificationResult
    attestation: Attestation | None
    authorization: AuthorizationDecision


class OceanicStack:
    """Run the evidence-bound path from source to authorization."""

    def __init__(self, integration: IntegrationPipeline, verification=None, authorization=None):
        self.integration = integration
        self.verification = verification or VerificationPipeline()
        self.authorization = authorization or AuthorizationGate()

    def run(self, sources: Iterable[ContextSource]) -> StackRun:
        integration = self.integration.run(sources)
        verification = self.verification.verify(integration)
        attestation = None
        if verification.status == "verified":
            attestation = self.verification.attest(verification)
        authorization = self.authorization.decide(verification)
        return StackRun(integration, verification, attestation, authorization)

    @staticmethod
    def route_proposal(run: StackRun, proposal: Proposal) -> ProposalDecision:
        return ProactiveEngine.route(proposal, run.authorization)

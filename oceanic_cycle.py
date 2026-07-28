"""The Oceanic Cycle Kernel — Continuous Becoming made executable.

    OBSERVE → CONTRACT → VERIFY → CONSENSUS/DISSENT → ATTEST →
    ACCOUNT → ACT → CONSEQUENCE → LEARN → DETECT DRIFT →
    RECOMPILE → OBSERVE

One complete cycle transitions the system from Sₙ to Sₙ₊₁. Every transition
is recorded with full provenance. No state transition without an observable
reason. No evolution without verification. No dissent without a record.
No record without provenance.

The cycle is the heartbeat of Ω∞v: each beat leaves an immutable audit trail
so the system's history is verifiable by construction.
"""
from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


# ─── Invariants ──────────────────────────────────────────────────────────────

INVARIANTS = (
    "No state transition without an observable reason.",
    "No evolution without verification.",
    "No dissent without a record.",
    "No record without provenance.",
    "Evolution may change the system, but may not secretly change the rules "
    "by which the system is trusted.",
)


# ─── Verification status ─────────────────────────────────────────────────────

class VerificationStatus(str, Enum):
    VERIFIED = "verified"
    PARTIALLY_VERIFIED = "partially_verified"
    DISSENT = "dissent"
    UNVERIFIED = "unverified"
    BLOCKED = "blocked"


class DecisionRoute(str, Enum):
    ACCEPT = "accept"
    CONTINUE_CHECKING = "continue_checking"
    RETRY = "retry"
    REVERIFY = "reverify"
    HUMAN_ROUTE = "human_route"
    HOLD = "hold"
    HUMAN_AUTHORIZATION = "human_authorization"


# ─── Data containers ─────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Observation:
    """What the Observer recorded."""
    observer: str
    what: str
    evidence: tuple[str, ...]
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    observation_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])


@dataclass(frozen=True)
class Contract:
    """The invariants this cycle checks against."""
    contract_id: str
    clauses: tuple[str, ...]
    version: str = "1.0"


@dataclass(frozen=True)
class VerificationResult:
    """The outcome of verifying observation against contract."""
    status: VerificationStatus
    confidence: float | None
    evidence_hash: str
    dissent: tuple[str, ...] = ()
    checks_passed: int = 0
    checks_total: int = 0


@dataclass(frozen=True)
class CycleEvent:
    """One complete cycle event — the immutable audit record."""
    cycle_id: str
    state_id: str
    contract_id: str
    observer: str
    evidence: tuple[str, ...]
    verification: VerificationStatus
    confidence: float | None
    dissent: tuple[str, ...]
    decision: DecisionRoute
    action: str
    consequence: str
    next_state: str
    provenance_hash: str
    timestamp: str


# ─── Decision logic ──────────────────────────────────────────────────────────

def route_decision(result: VerificationResult) -> DecisionRoute:
    """Map a verification result to a decision route.

    VERIFIED → ACCEPT
    PARTIALLY_VERIFIED → CONTINUE_CHECKING
    DISSENT → HUMAN_ROUTE (dissent is always recorded, never suppressed)
    UNVERIFIED → HOLD
    BLOCKED → HUMAN_AUTHORIZATION
    """
    return {
        VerificationStatus.VERIFIED: DecisionRoute.ACCEPT,
        VerificationStatus.PARTIALLY_VERIFIED: DecisionRoute.CONTINUE_CHECKING,
        VerificationStatus.DISSENT: DecisionRoute.HUMAN_ROUTE,
        VerificationStatus.UNVERIFIED: DecisionRoute.HOLD,
        VerificationStatus.BLOCKED: DecisionRoute.HUMAN_AUTHORIZATION,
    }[result.status]


# ─── Provenance ──────────────────────────────────────────────────────────────

def provenance_hash(
    state_id: str,
    contract_id: str,
    evidence: tuple[str, ...],
    verification: VerificationStatus,
    decision: DecisionRoute,
) -> str:
    """Deterministic hash binding state, contract, evidence, and outcome."""
    payload = json.dumps({
        "state_id": state_id,
        "contract_id": contract_id,
        "evidence": list(evidence),
        "verification": verification.value,
        "decision": decision.value,
    }, sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()


# ─── The Cycle Engine ────────────────────────────────────────────────────────

class OceanicCycle:
    """Execute one complete Observe → Verify → Attest → Evolve → Recompile cycle.

    Each cycle:
      1. Receives an Observation (the Observer has already read reality)
      2. Verifies the observation against a Contract
      3. Routes the decision (accept, hold, human_route, etc.)
      4. Records the full CycleEvent with provenance
      5. Returns the next state id — Sₙ₊₁

    The cycle is pure: given the same inputs, it produces the same outputs
    and the same provenance hash. The ledger (list of events) is append-only.
    """

    def __init__(self) -> None:
        self._events: list[CycleEvent] = []
        self._state_counter: int = 0

    @property
    def state_id(self) -> str:
        return f"S{self._state_counter}"

    @property
    def events(self) -> tuple[CycleEvent, ...]:
        return tuple(self._events)

    def execute(
        self,
        observation: Observation,
        contract: Contract,
        verification: VerificationResult,
        action: str = "",
        consequence: str = "",
    ) -> CycleEvent:
        """Run one cycle. Returns the CycleEvent (the immutable audit record).

        The action and consequence describe what was done and what happened.
        If the decision is HOLD or HUMAN_ROUTE, the action should reflect
        that no autonomous action was taken.
        """
        current_state = self.state_id
        decision = route_decision(verification)

        # Determine the action description based on decision
        if not action:
            action = _default_action(decision)
        if not consequence:
            consequence = _default_consequence(decision)

        # Compute next state
        self._state_counter += 1
        next_state = self.state_id

        # Build provenance
        prov_hash = provenance_hash(
            current_state, contract.contract_id,
            observation.evidence, verification.status, decision,
        )

        event = CycleEvent(
            cycle_id=uuid.uuid4().hex[:16],
            state_id=current_state,
            contract_id=contract.contract_id,
            observer=observation.observer,
            evidence=observation.evidence,
            verification=verification.status,
            confidence=verification.confidence,
            dissent=verification.dissent,
            decision=decision,
            action=action,
            consequence=consequence,
            next_state=next_state,
            provenance_hash=prov_hash,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        self._events.append(event)
        return event

    def audit_trail(self) -> list[dict[str, Any]]:
        """The full immutable audit trail as serializable dicts."""
        result = []
        for event in self._events:
            d = asdict(event)
            # Convert enums to their string values for serialization
            d["verification"] = event.verification.value
            d["decision"] = event.decision.value
            d["dissent"] = list(event.dissent)
            d["evidence"] = list(event.evidence)
            result.append(d)
        return result

    def verify_provenance(self, event: CycleEvent) -> bool:
        """Re-derive the provenance hash and check it matches the record."""
        expected = provenance_hash(
            event.state_id, event.contract_id,
            event.evidence, event.verification, event.decision,
        )
        return expected == event.provenance_hash


# ─── Default descriptions ────────────────────────────────────────────────────

def _default_action(decision: DecisionRoute) -> str:
    return {
        DecisionRoute.ACCEPT: "proceed — verification passed",
        DecisionRoute.CONTINUE_CHECKING: "continue — partial verification",
        DecisionRoute.RETRY: "retry — verification inconclusive",
        DecisionRoute.REVERIFY: "reverify — dissent requires re-examination",
        DecisionRoute.HUMAN_ROUTE: "hold for human — dissent recorded",
        DecisionRoute.HOLD: "hold — unverified, no action authorized",
        DecisionRoute.HUMAN_AUTHORIZATION: "blocked — requires human authorization",
    }[decision]


def _default_consequence(decision: DecisionRoute) -> str:
    return {
        DecisionRoute.ACCEPT: "state advanced — Sₙ → Sₙ₊₁",
        DecisionRoute.CONTINUE_CHECKING: "state pending — additional checks needed",
        DecisionRoute.RETRY: "state unchanged — awaiting retry",
        DecisionRoute.REVERIFY: "state held — re-examination in progress",
        DecisionRoute.HUMAN_ROUTE: "state held — awaiting human judgment",
        DecisionRoute.HOLD: "state frozen — no transition authorized",
        DecisionRoute.HUMAN_AUTHORIZATION: "state blocked — escalated to human",
    }[decision]

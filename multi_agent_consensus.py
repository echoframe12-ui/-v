from __future__ import annotations

"""Multi-agent autonomous consensus loop engine for the Ω∞ Oceanic stack.

Executes iterative consensus evaluations across provider perspectives, tracking opinion
convergence, dissent scores, and routing results through MOOD integrity into continuous
becoming transitions.
"""

from dataclasses import dataclass
from typing import Any

from consensus_log import ConsensusLog, dissent_score
from context_assembly import ContextAssembly, make_context
from continuous_becoming import BecomingTransition, ContinuousBecomingEngine
from mood import MoodAssessment, MoodSignal, assess, record_to_ledger
from mood_integrity import assess_perspectives
from perspectives import PerspectiveRegistry, compare_perspectives, create_live_registry


@dataclass(frozen=True)
class ConsensusRoundResult:
    round_index: int
    perspectives: list[Any]
    verdicts: list[str]
    dissent_score: float
    has_dissent: bool
    majority: str | None


@dataclass(frozen=True)
class MultiAgentConsensusResult:
    prompt: str
    iterations: int
    converged: bool
    final_dissent_score: float
    rounds: list[ConsensusRoundResult]
    assessment: MoodAssessment
    transition: BecomingTransition


class MultiAgentConsensusEngine:
    """Iterative multi-agent consensus loop driven by MOOD dissent routing."""

    def __init__(
        self,
        registry: PerspectiveRegistry | None = None,
        db_path: str | None = None,
        ledger: Any | None = None,
    ) -> None:
        self._registry = registry if registry is not None else create_live_registry()
        self._db_path = db_path
        self._ledger = ledger
        self._becoming_engine = ContinuousBecomingEngine()

    def run_loop(
        self,
        prompt: str,
        *,
        max_iterations: int = 3,
        dissent_threshold: float = 0.0,
        context: Any = None,
    ) -> MultiAgentConsensusResult:
        """Run an iterative consensus loop across registered perspectives.

        Evaluates responses each round. If dissent score <= dissent_threshold, consensus
        converges early. Otherwise continues up to max_iterations. Emits ledger events and
        returns a complete MultiAgentConsensusResult.
        """
        consensus_log = ConsensusLog(self._db_path) if self._db_path else None
        rounds: list[ConsensusRoundResult] = []
        converged = False
        latest_assessment: MoodAssessment | None = None
        latest_perspectives: list[Any] = []

        ctx = context if isinstance(context, ContextAssembly) else make_context(prompt)

        for i in range(1, max_iterations + 1):
            latest_perspectives = self._registry.evaluate_all(ctx)
            comparison = compare_perspectives(latest_perspectives)
            verdicts = comparison.get("verdicts", [getattr(p, "response", "unknown") for p in latest_perspectives])
            score = dissent_score(verdicts)

            if consensus_log is not None:
                consensus_log.record(
                    prompt,
                    {
                        "adapters": [getattr(p, "provider", "unknown") for p in latest_perspectives],
                        "verdicts": verdicts,
                        "majority": comparison.get("majority"),
                        "dissent": comparison.get("dissent", False),
                    },
                )

            round_res = ConsensusRoundResult(
                round_index=i,
                perspectives=latest_perspectives,
                verdicts=verdicts,
                dissent_score=score,
                has_dissent=comparison.get("dissent", False),
                majority=comparison.get("majority"),
            )
            rounds.append(round_res)

            latest_assessment = assess_perspectives(
                latest_perspectives,
                ledger=self._ledger,
                entity_id=f"consensus-loop-round-{i}",
            )

            if score <= dissent_threshold and not comparison.get("dissent", False):
                converged = True
                break


        if latest_assessment is None:
            latest_assessment = assess([])

        if self._ledger is not None:
            event_type = "mood.consensus" if converged else "mood.dissent"
            record_to_ledger(latest_assessment, self._ledger, entity_id="multi-agent-consensus")
            self._ledger.append(
                event_type=event_type,
                entity_id=prompt[:32],
                payload={
                    "prompt": prompt,
                    "iterations": len(rounds),
                    "converged": converged,
                    "final_dissent_score": rounds[-1].dissent_score if rounds else 0.0,
                },
            )


        transition = self._becoming_engine.advance_mood(
            latest_assessment,
            current_state="consensus_loop",
            provenance=("multi_agent_consensus", f"rounds:{len(rounds)}"),
        )

        return MultiAgentConsensusResult(
            prompt=prompt,
            iterations=len(rounds),
            converged=converged,
            final_dissent_score=rounds[-1].dissent_score if rounds else 0.0,
            rounds=rounds,
            assessment=latest_assessment,
            transition=transition,
        )

from __future__ import annotations

"""Drift -> recompile -> reverify boundary for Ω∞v attestation v0.1.

Recompilation is deliberately supplied by the existing cycle/compiler layer.
This module owns only the trust boundary: drift never mutates an issued
attestation, and a recompilation must produce a freshly verified CycleEvent
before a new signed attestation is issued.
"""

from typing import Any

from attestation_protocol import SignedAttestation, evolve_attestation
from oceanic_cycle import CycleEvent, VerificationStatus


def recompile_and_reattest(
    parent: SignedAttestation,
    recompiled_event: CycleEvent,
    *,
    prompt: str,
    final_output: str,
    schema_digest: str,
    private_key: bytes,
    drift_state: str,
    recompile_state: str,
    expected_parent_schema_digest: str | None = None,
    **kwargs: Any,
) -> SignedAttestation:
    """Issue a new attestation only after the recompiled event verifies.

    The parent is checked by ``evolve_attestation``. The new event must itself
    be VERIFIED; partial, dissenting, blocked, or unverified recompilations
    cannot cross the attested boundary.
    """
    if recompiled_event.verification != VerificationStatus.VERIFIED:
        raise ValueError("recompiled state must be independently verified before attestation")

    return evolve_attestation(
        parent,
        recompiled_event,
        prompt=prompt,
        final_output=final_output,
        schema_digest=schema_digest,
        private_key=private_key,
        expected_parent_schema_digest=expected_parent_schema_digest,
        drift_state=drift_state,
        recompile_state=recompile_state,
        **kwargs,
    )

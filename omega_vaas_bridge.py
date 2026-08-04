from __future__ import annotations

"""Thin Ω∞v bridge for the existing Oceanic lifecycle.

The bridge does not create a second lifecycle. It converts the existing
lifecycle's verified cycle evidence into the cryptographic Ω∞v envelope.
"""

from dataclasses import dataclass
from typing import Any

from attestation_protocol import SignedAttestation, attest_cycle
from oceanic_cycle import CycleEvent, VerificationStatus
from omega_signer import OmegaSigner


@dataclass(frozen=True)
class OmegaVaasAttestation:
    signed: SignedAttestation
    verified: bool


def attest_verified_cycle(
    event: CycleEvent,
    *,
    signer: OmegaSigner,
    prompt: str,
    final_output: str,
    schema_digest: str,
    request_id: str | None = None,
    session_id: str | None = None,
    **kwargs: Any,
) -> OmegaVaasAttestation:
    """Issue Ω∞v attestation only for a fully verified CycleEvent."""
    if event.verification is not VerificationStatus.VERIFIED:
        raise ValueError("Ω∞v VaaS attestation requires VERIFIED cycle status")
    signed = attest_cycle(
        event,
        prompt=prompt,
        final_output=final_output,
        schema_digest=schema_digest,
        private_key=signer.private_key,
        request_id=request_id,
        session_id=session_id,
        **kwargs,
    )
    return OmegaVaasAttestation(signed=signed, verified=True)

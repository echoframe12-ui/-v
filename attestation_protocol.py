from __future__ import annotations

"""Ω∞v Attestation Protocol v0.1.

Verification, attestation, and cryptographic authorization remain distinct.
The protocol signs canonical JSON and never persists private signing material.
"""

import base64
import hashlib
import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives.serialization import Encoding, NoEncryption, PrivateFormat, PublicFormat

from oceanic_cycle import CycleEvent, VerificationStatus

SCHEMA = "oceanic.attestation/v0.1"
SCHEMA_VERSION = "0.1"


def _canonical_json(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_hex(value: str | bytes) -> str:
    raw = value.encode("utf-8") if isinstance(value, str) else value
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def hash_json(value: Any) -> str:
    return sha256_hex(_canonical_json(value))


def generate_keypair() -> tuple[bytes, bytes]:
    """Return raw Ed25519 private/public key bytes for local provisioning."""
    private = Ed25519PrivateKey.generate()
    return (
        private.private_bytes(Encoding.Raw, PrivateFormat.Raw, NoEncryption()),
        private.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw),
    )


def _b64(value: bytes) -> str:
    return base64.b64encode(value).decode("ascii")


def _unb64(value: str) -> bytes:
    return base64.b64decode(value.encode("ascii"), validate=True)


@dataclass(frozen=True)
class Attestation:
    document: dict[str, Any]
    signature: str
    public_key: str

    def signing_bytes(self) -> bytes:
        return _canonical_json(self.document)

    def to_dict(self) -> dict[str, Any]:
        result = dict(self.document)
        result["signature"] = self.signature
        result["verifier"] = {"algorithm": "Ed25519", "public_key": self.public_key}
        return result

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def attest_cycle(
    event: CycleEvent,
    *,
    prompt: str,
    final_output: str,
    schema_digest: str,
    private_key: bytes,
    request_id: str | None = None,
    session_id: str | None = None,
    model_manifest: list[dict[str, Any]] | None = None,
    ensemble_strategy: str = "existing-cycle-verification",
    cvi: float | None = None,
    evidence: list[str] | None = None,
    human_review_state: str = "not_required",
    constitution_version: str = "unknown",
    parent_attestation_id: str | None = None,
    drift_state: str = "none",
    recompile_state: str = "not_required",
) -> Attestation:
    """Create and sign one v0.1 attestation from an existing CycleEvent."""
    if len(private_key) != 32:
        raise ValueError("Ed25519 private key must contain exactly 32 raw bytes")

    key = Ed25519PrivateKey.from_private_bytes(private_key)
    public_key = key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    now = datetime.now(timezone.utc).isoformat()
    status_map = {
        VerificationStatus.VERIFIED: "VERIFIED",
        VerificationStatus.PARTIALLY_VERIFIED: "PARTIALLY_VERIFIED",
        VerificationStatus.DISSENT: "DISSENT_FLAGGED",
        VerificationStatus.UNVERIFIED: "UNVERIFIED",
        VerificationStatus.BLOCKED: "HUMAN_HOLD",
    }

    document: dict[str, Any] = {
        "schema": SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "attestation_id": "att_" + uuid.uuid4().hex,
        "timestamp": now,
        "request_id": request_id or "req_" + uuid.uuid4().hex,
        "session_id": session_id or "ses_" + uuid.uuid4().hex,
        "prompt_hash": sha256_hex(prompt),
        "model_manifest": model_manifest or [],
        "ensemble_strategy": ensemble_strategy,
        "verification": {
            "status": status_map[event.verification],
            "cycle_id": event.cycle_id,
            "contract_id": event.contract_id,
            "confidence": event.confidence,
            "decision": event.decision.value,
            "checks": {"provenance": event.provenance_hash, "evidence_count": len(event.evidence)},
        },
        "cvi": {"score": cvi, "breakdown": None},
        "consensus": event.verification == VerificationStatus.VERIFIED and not event.dissent,
        "dissent": list(event.dissent),
        "evidence_anchors": list(evidence or event.evidence),
        "attestation_status": "ATTESTED" if event.verification == VerificationStatus.VERIFIED else status_map[event.verification],
        "human_review_state": human_review_state,
        "constitutional_checks": {
            "provenance_present": bool(event.provenance_hash),
            "dissent_preserved": True,
            "verification_attestation_separate": True,
        },
        "final_output": final_output,
        "output_hash": sha256_hex(final_output),
        "parent_attestation_id": parent_attestation_id,
        "constitution_version": constitution_version,
        "drift_state": drift_state,
        "recompile_state": recompile_state,
        "next_state": event.next_state,
        "schema_digest": schema_digest,
    }
    signature = key.sign(_canonical_json(document))
    return Attestation(document=document, signature=_b64(signature), public_key=_b64(public_key))


def verify_attestation(attestation: dict[str, Any]) -> dict[str, Any]:
    """Independently verify an attestation using only its document and public key."""
    try:
        signature = _unb64(attestation["signature"])
        public_key = _unb64(attestation["verifier"]["public_key"])
        document = {k: v for k, v in attestation.items() if k not in {"signature", "verifier"}}
        Ed25519PublicKey.from_public_bytes(public_key).verify(signature, _canonical_json(document))
    except (KeyError, ValueError, TypeError, InvalidSignature):
        return {"valid": False, "reason": "signature_invalid"}

    final_output = document.get("final_output")
    return {
        "valid": True,
        "signature_valid": True,
        "output_intact": isinstance(final_output, str) and document.get("output_hash") == sha256_hex(final_output),
        "schema_valid": document.get("schema") == SCHEMA,
        "attestation_id": document.get("attestation_id"),
        "next_state": document.get("next_state"),
    }

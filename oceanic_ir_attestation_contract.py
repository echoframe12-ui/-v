from __future__ import annotations

"""Bridge Ω∞v attestations into the canonical Oceanic IR proof contract."""

from hashlib import sha256
from typing import Any, Mapping

from oceanic_ir import AdapterManifest, OceanicIRContract, OceanicIRValidator, ProofArtifact, ProofClaim

CONTRACT_ID = "omega-edge-attestation-v1"
API_VERSION = "1"


def contract() -> OceanicIRContract:
    return OceanicIRContract(
        api_version=API_VERSION,
        contract_id=CONTRACT_ID,
        intent="verify an Ω∞v Edge attestation against its declared proof obligations",
        proof_obligations=("attestation_signature", "attestation_lineage"),
        invariants=("contract_id is stable", "missing proof obligations remain unproven"),
        effects=("verification only",),
        dissent_triggers=("missing proof", "invalid signature", "lineage mismatch"),
        risk={"trust_boundary": "edge"},
    )


def proof_from_attestation(attestation: Mapping[str, Any]) -> ProofArtifact:
    signature = attestation.get("signature")
    lineage = attestation.get("lineage")
    claims = (
        ProofClaim("attestation_signature", "satisfied" if signature else "missing", "signature", _digest(signature)),
        ProofClaim("attestation_lineage", "satisfied" if lineage else "missing", "lineage", _digest(lineage)),
    )
    adapter = AdapterManifest(
        protocol="omega-edge", language="python", language_version="runtime", adapter_version="1",
        capabilities=("attestation_signature", "attestation_lineage"), proof_types=("signature", "lineage"), limitations=(),
    )
    return ProofArtifact(
        contract_id=CONTRACT_ID, adapter=adapter, implementation_digest=_digest(attestation),
        toolchain_digest=_digest("omega-edge"), claims=claims,
    )


def verify_attestation_contract(attestation: Mapping[str, Any]):
    return OceanicIRValidator().verify(contract(), proof_from_attestation(attestation))


def _digest(value: Any) -> str:
    return sha256(repr(value).encode("utf-8")).hexdigest()

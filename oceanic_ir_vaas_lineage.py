from __future__ import annotations

"""Make Ω∞v VaaS attestation lineage an explicit Oceanic IR obligation."""

from typing import Any, Mapping

from oceanic_ir import AdapterManifest, OceanicIRContract, OceanicIRValidator, ProofArtifact, ProofClaim
from attestation_protocol import verify_attestation

CONTRACT_ID = "omega-vaas-lineage-v1"


def contract() -> OceanicIRContract:
    return OceanicIRContract(
        api_version="1",
        contract_id=CONTRACT_ID,
        intent="verify that an Ω∞v VaaS attestation has an intact signed lineage",
        proof_obligations=("signature_integrity", "attestation_lineage"),
        invariants=(
            "the signed record is independently verifiable",
            "an evolved attestation names its parent",
        ),
        dissent_triggers=("invalid signature", "missing lineage", "lineage mismatch"),
        risk={"trust_boundary": "vaas"},
    )


def proof_from_attestation(attestation: Mapping[str, Any]) -> ProofArtifact:
    record = dict(attestation)
    report = verify_attestation(record)
    attestation_id = record.get("attestation_id")
    parent_id = record.get("parent_attestation_id")
    lineage_ok = isinstance(attestation_id, str) and bool(attestation_id) and (
        parent_id is None or (isinstance(parent_id, str) and bool(parent_id))
    )
    claims = (
        ProofClaim(
            obligation="signature_integrity",
            status="satisfied" if report.get("valid") else "missing",
            evidence_type="signed-attestation",
            evidence_digest=attestation_id or "",
        ),
        ProofClaim(
            obligation="attestation_lineage",
            status="satisfied" if lineage_ok else "missing",
            evidence_type="parent_attestation_id",
            evidence_digest=str(parent_id or attestation_id or ""),
        ),
    )
    adapter = AdapterManifest(
        protocol="omega-vaas",
        language="python",
        language_version="runtime",
        adapter_version="1",
        capabilities=("signature_integrity", "attestation_lineage"),
        proof_types=("ed25519", "parent_attestation_id"),
        limitations=(),
    )
    return ProofArtifact(
        contract_id=CONTRACT_ID,
        adapter=adapter,
        implementation_digest=attestation_id or "",
        toolchain_digest="omega-vaas",
        claims=claims,
    )


def verify_vaas_lineage(attestation: Mapping[str, Any]):
    return OceanicIRValidator().verify(contract(), proof_from_attestation(attestation))

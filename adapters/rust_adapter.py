from __future__ import annotations

"""Reference Rust adapter for the Ω∞ Oceanic verification compiler.

Rust gives a stronger proof perspective than the Python reference adapter,
because the compiler and borrow checker contribute evidence to the proof chain.
"""

import hashlib
from dataclasses import dataclass

from oceanic_ir import AdapterManifest, OceanicIRContract, ProofArtifact, ProofClaim


MANIFEST = AdapterManifest(
    protocol="oceanic.adapter/v0.1",
    language="rust",
    language_version="1.75.0",
    adapter_version="0.1.0",
    capabilities=("arithmetic_correctness", "overflow_handling", "memory_safety"),
    proof_types=("borrow_checker", "checked_arithmetic", "unit_tests"),
    limitations=("compile time may be longer",),
    local_first=True,
    dissent_mode="surface_first",
)


@dataclass(frozen=True)
class CompileArtifact:
    source: str
    implementation_digest: str


def compile_contract(contract: OceanicIRContract) -> CompileArtifact:
    """Produce a deterministic illustrative Rust implementation."""
    if contract.intent != "combine two numeric values":
        raise NotImplementedError("reference adapter only supports numeric addition")

    source = """pub fn combine(a: i64, b: i64) -> Result<i64, &'static str> {\n    a.checked_add(b).ok_or(\"overflow\")\n}\n"""
    digest = "sha256:" + hashlib.sha256(source.encode("utf-8")).hexdigest()
    return CompileArtifact(source=source, implementation_digest=digest)


def prove_contract(
    contract: OceanicIRContract,
    artifact: CompileArtifact,
) -> ProofArtifact:
    """Generate a proof artifact from the Rust adapter evidence model."""
    claims = (
        ProofClaim(
            obligation="arithmetic_correctness",
            status="satisfied",
            evidence_type="unit_tests",
            evidence_digest=artifact.implementation_digest,
        ),
        ProofClaim(
            obligation="overflow_handling",
            status="satisfied",
            evidence_type="checked_arithmetic",
            evidence_digest=artifact.implementation_digest,
        ),
    )
    return ProofArtifact(
        contract_id=contract.contract_id,
        adapter=MANIFEST,
        implementation_digest=artifact.implementation_digest,
        toolchain_digest="sha256:rust-reference-toolchain",
        claims=claims,
        limitations=MANIFEST.limitations,
        dissent=(),
        reproducibility={"adapter_version": MANIFEST.adapter_version},
    )

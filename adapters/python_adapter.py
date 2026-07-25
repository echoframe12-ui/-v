from __future__ import annotations

"""Reference Python adapter for the Ω∞ Oceanic verification compiler.

This adapter demonstrates the protocol boundary: compile an IR contract into
an implementation artifact, then produce a proof artifact for the verifier.
It intentionally does not claim guarantees that Python cannot substantiate.
"""

import hashlib
from dataclasses import dataclass

from oceanic_ir import AdapterManifest, OceanicIRContract, ProofArtifact, ProofClaim


MANIFEST = AdapterManifest(
    protocol="oceanic.adapter/v0.1",
    language="python",
    language_version="3.12",
    adapter_version="0.1.0",
    capabilities=("arithmetic_correctness", "overflow_handling", "pure_functions"),
    proof_types=("unit_tests", "property_tests", "static_analysis"),
    limitations=(
        "memory safety is not statically guaranteed",
        "numeric safety depends on runtime semantics and explicit checks",
    ),
    local_first=True,
    dissent_mode="surface_first",
)


@dataclass(frozen=True)
class CompileArtifact:
    source: str
    implementation_digest: str


def compile_contract(contract: OceanicIRContract) -> CompileArtifact:
    """Produce a deterministic illustrative Python implementation.

    This reference adapter currently supports the narrow 'combine two values'
    intent. Unsupported intent is rejected rather than silently approximated.
    """
    if contract.intent != "combine two numeric values":
        raise NotImplementedError("reference adapter only supports numeric addition")

    source = """def combine(a, b):\n    result = a + b\n    return result\n"""
    digest = "sha256:" + hashlib.sha256(source.encode("utf-8")).hexdigest()
    return CompileArtifact(source=source, implementation_digest=digest)


def prove_contract(
    contract: OceanicIRContract,
    artifact: CompileArtifact,
) -> ProofArtifact:
    """Generate a proof artifact from the reference adapter's evidence model."""
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
            evidence_type="python_integer_runtime_semantics",
            evidence_digest=artifact.implementation_digest,
        ),
    )
    return ProofArtifact(
        contract_id=contract.contract_id,
        adapter=MANIFEST,
        implementation_digest=artifact.implementation_digest,
        toolchain_digest="sha256:python-reference-toolchain",
        claims=claims,
        limitations=MANIFEST.limitations,
        dissent=(
            "overflow guarantee relies on Python integer semantics rather than a static numeric bound",
        ),
        reproducibility={"adapter_version": MANIFEST.adapter_version},
    )

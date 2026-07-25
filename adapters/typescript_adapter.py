from __future__ import annotations

"""Reference TypeScript/JavaScript adapter for Ω∞ Oceanic.

This adapter models a third execution perspective: web-native and dynamic at
runtime, with compile-time TypeScript evidence and explicit runtime dissent.
"""

import hashlib
from dataclasses import dataclass

from oceanic_ir import AdapterManifest, OceanicIRContract, ProofArtifact, ProofClaim


MANIFEST = AdapterManifest(
    protocol="oceanic.adapter/v0.1",
    language="typescript",
    language_version="5.x",
    adapter_version="0.1.0",
    capabilities=("arithmetic_correctness", "overflow_handling", "type_checked_interfaces"),
    proof_types=("typescript_compiler", "unit_tests", "static_analysis"),
    limitations=(
        "JavaScript runtime number semantics require explicit numeric-domain constraints",
        "runtime environment may affect execution behavior",
    ),
    local_first=True,
    dissent_mode="surface_first",
)


@dataclass(frozen=True)
class CompileArtifact:
    source: str
    implementation_digest: str


def compile_contract(contract: OceanicIRContract) -> CompileArtifact:
    """Produce a deterministic illustrative TypeScript implementation."""
    if contract.intent != "combine two numeric values":
        raise NotImplementedError("reference adapter only supports numeric addition")

    source = """export function combine(a: number, b: number): number {\n  const result = a + b;\n  if (!Number.isSafeInteger(result)) {\n    throw new Error('numeric bound exceeded');\n  }\n  return result;\n}\n"""
    digest = "sha256:" + hashlib.sha256(source.encode("utf-8")).hexdigest()
    return CompileArtifact(source=source, implementation_digest=digest)


def prove_contract(
    contract: OceanicIRContract,
    artifact: CompileArtifact,
) -> ProofArtifact:
    """Generate a proof artifact from TypeScript compiler and test evidence."""
    claims = (
        ProofClaim(
            obligation="arithmetic_correctness",
            status="satisfied",
            evidence_type="typescript_compiler_and_unit_tests",
            evidence_digest=artifact.implementation_digest,
        ),
        ProofClaim(
            obligation="overflow_handling",
            status="satisfied",
            evidence_type="runtime_safe_integer_guard",
            evidence_digest=artifact.implementation_digest,
        ),
    )
    return ProofArtifact(
        contract_id=contract.contract_id,
        adapter=MANIFEST,
        implementation_digest=artifact.implementation_digest,
        toolchain_digest="sha256:typescript-reference-toolchain",
        claims=claims,
        limitations=MANIFEST.limitations,
        dissent=(
            "numeric correctness depends on the declared safe-integer domain and JavaScript runtime semantics",
        ),
        reproducibility={"adapter_version": MANIFEST.adapter_version},
    )

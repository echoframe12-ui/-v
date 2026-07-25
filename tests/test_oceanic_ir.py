import unittest

from oceanic_ir import (
    AdapterManifest,
    ContractState,
    OceanicIRContract,
    OceanicIRValidator,
    ProofArtifact,
    ProofClaim,
)


class OceanicIRTests(unittest.TestCase):
    def setUp(self):
        self.contract = OceanicIRContract(
            api_version="oceanic.ir/v0.1",
            contract_id="example.add.v1",
            intent="combine two numeric values",
            inputs=(
                {"name": "a", "type": "integer"},
                {"name": "b", "type": "integer"},
            ),
            outputs={"type": "integer"},
            invariants=(
                "result == mathematical_sum(a, b)",
                "overflow_is_never_silent",
            ),
            effects=(),
            bounds={"time": "O(1)", "memory": "O(1)"},
            dependencies=(),
            proof_obligations=("arithmetic_correctness", "overflow_handling"),
            dissent_triggers=("overflow", "unsupported_numeric_domain"),
            risk={"class": "low", "human_authorization": False},
        )
        self.manifest = AdapterManifest(
            protocol="oceanic.adapter/v0.1",
            language="rust",
            language_version="1.75.0",
            adapter_version="0.1.0",
            capabilities=("arithmetic_correctness", "overflow_handling", "memory_safety"),
            proof_types=("borrow_checker", "unit_tests"),
            limitations=("no garbage collection",),
        )
        self.proof = ProofArtifact(
            contract_id="example.add.v1",
            adapter=self.manifest,
            implementation_digest="sha256:impl",
            toolchain_digest="sha256:toolchain",
            claims=(
                ProofClaim("arithmetic_correctness", "satisfied", "unit_tests", "sha256:a"),
                ProofClaim("overflow_handling", "satisfied", "checked_arithmetic", "sha256:b"),
            ),
            limitations=(),
            dissent=(),
            reproducibility={"lockfile": "sha256:lock"},
        )

    def test_contract_validation_passes(self):
        validator = OceanicIRValidator()
        validator.validate_contract(self.contract)
        validator.validate_manifest(self.manifest)

    def test_capability_matching(self):
        validator = OceanicIRValidator()
        ok, missing = validator.match_capabilities(self.contract, self.manifest)
        self.assertTrue(ok)
        self.assertEqual(missing, ())

    def test_proof_verification_proves_contract(self):
        outcome = OceanicIRValidator().verify(self.contract, self.proof)
        self.assertEqual(outcome.status, ContractState.PROVED)
        self.assertEqual(outcome.missing_obligations, ())
        self.assertEqual(outcome.satisfied_obligations, ("arithmetic_correctness", "overflow_handling"))
        self.assertGreaterEqual(outcome.confidence, 0.9)

    def test_dissent_is_preserved_when_present(self):
        proof = ProofArtifact(
            contract_id="example.add.v1",
            adapter=self.manifest,
            implementation_digest="sha256:impl",
            toolchain_digest="sha256:toolchain",
            claims=(
                ProofClaim("arithmetic_correctness", "satisfied", "unit_tests", "sha256:a"),
                ProofClaim("overflow_handling", "satisfied", "checked_arithmetic", "sha256:b"),
            ),
            limitations=("runtime-only guarantee",),
            dissent=("runtime_only_safety",),
            reproducibility={"lockfile": "sha256:lock"},
        )
        outcome = OceanicIRValidator().verify(self.contract, proof)
        self.assertEqual(outcome.status, ContractState.PROVED_WITH_DISSENT)
        self.assertIn("runtime_only_safety", outcome.dissent)

    def test_missing_obligation_is_unproven(self):
        proof = ProofArtifact(
            contract_id="example.add.v1",
            adapter=self.manifest,
            implementation_digest="sha256:impl",
            toolchain_digest="sha256:toolchain",
            claims=(
                ProofClaim("arithmetic_correctness", "satisfied", "unit_tests", "sha256:a"),
            ),
            limitations=(),
            dissent=(),
            reproducibility={"lockfile": "sha256:lock"},
        )
        outcome = OceanicIRValidator().verify(self.contract, proof)
        self.assertEqual(outcome.status, ContractState.UNPROVEN)
        self.assertEqual(outcome.missing_obligations, ("overflow_handling",))

    def test_contract_id_mismatch_is_rejected(self):
        proof = ProofArtifact(
            contract_id="different.v1",
            adapter=self.manifest,
            implementation_digest="sha256:impl",
            toolchain_digest="sha256:toolchain",
            claims=(),
            limitations=(),
            dissent=(),
            reproducibility={},
        )
        outcome = OceanicIRValidator().verify(self.contract, proof)
        self.assertEqual(outcome.status, ContractState.REJECTED)

    def test_invalid_contract_is_rejected(self):
        validator = OceanicIRValidator()
        invalid = OceanicIRContract(
            api_version="",
            contract_id="",
            intent="",
            inputs=(),
            outputs={},
            invariants=(),
            effects=(),
            bounds={},
            dependencies=(),
            proof_obligations=(),
            dissent_triggers=(),
            risk={},
        )
        with self.assertRaises(ValueError):
            validator.validate_contract(invalid)


if __name__ == "__main__":
    unittest.main()

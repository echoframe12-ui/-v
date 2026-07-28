"""Tests for the Oceanic Orchestrator — the core compilation/verification engine.

Covers:
  - ContractAdapter: full coverage, partial coverage, zero coverage, confidence
  - CompilationReport: supported_results, dissent, confidence
  - OceanicOrchestrator: single adapter, multiple adapters, empty adapters
  - default_adapters: 3 adapters, python/rust/typescript capabilities
  - VerificationReport backward-compat alias
  - Zero obligations: all adapters pass, full confidence, no dissent
  - Adapter with no capabilities: not supported, dissent for every obligation
"""
import unittest

from oceanic_ir import OceanicIRContract
from oceanic_orchestrator import (
    AdapterResult,
    CompilationReport,
    ContractAdapter,
    OceanicOrchestrator,
    VerificationReport,
    default_adapters,
)


def _make_contract(proof_obligations=("arithmetic_correctness", "overflow_handling")):
    return OceanicIRContract(
        api_version="oceanic.ir/v0.1",
        contract_id="orch.test.v1",
        intent="test the orchestrator",
        inputs=({"name": "x", "type": "integer"},),
        outputs={"type": "integer"},
        invariants=("result == x",),
        effects=(),
        bounds={"time": "O(1)", "memory": "O(1)"},
        dependencies=(),
        proof_obligations=proof_obligations,
        dissent_triggers=(),
        risk={"class": "low", "human_authorization": False},
    )


class ContractAdapterTests(unittest.TestCase):

    def test_adapter_with_all_capabilities_is_supported(self):
        adapter = ContractAdapter(
            "rust", capabilities=("arithmetic_correctness", "overflow_handling")
        )
        result = adapter.verify(_make_contract())
        self.assertTrue(result.supported)
        self.assertEqual(result.dissent, ())
        self.assertEqual(result.confidence, 1.0)
        self.assertEqual(result.language, "rust")

    def test_adapter_missing_one_capability_has_dissent(self):
        adapter = ContractAdapter("python", capabilities=("arithmetic_correctness",))
        result = adapter.verify(_make_contract())
        self.assertFalse(result.supported)
        self.assertEqual(len(result.dissent), 1)
        self.assertIn("overflow_handling", result.dissent[0])
        self.assertIn("python:", result.dissent[0])

    def test_adapter_with_no_capabilities_has_zero_confidence(self):
        adapter = ContractAdapter("empty", capabilities=())
        result = adapter.verify(_make_contract())
        self.assertFalse(result.supported)
        self.assertEqual(result.confidence, 0.0)
        self.assertEqual(len(result.dissent), 2)

    def test_adapter_partial_coverage_confidence_is_fractional(self):
        adapter = ContractAdapter("python", capabilities=("arithmetic_correctness",))
        # 1 of 2 obligations covered → confidence = 0.5
        result = adapter.verify(_make_contract())
        self.assertAlmostEqual(result.confidence, 0.5, places=6)

    def test_adapter_with_zero_obligations_is_supported_and_full_confidence(self):
        adapter = ContractAdapter("rust", capabilities=("arithmetic_correctness",))
        result = adapter.verify(_make_contract(proof_obligations=()))
        self.assertTrue(result.supported)
        self.assertEqual(result.confidence, 1.0)
        self.assertEqual(result.dissent, ())

    def test_proof_dict_contains_capabilities_and_covered_obligations(self):
        adapter = ContractAdapter(
            "rust", capabilities=("arithmetic_correctness", "overflow_handling")
        )
        result = adapter.verify(_make_contract())
        self.assertEqual(result.proof["type"], "capability_attestation")
        self.assertIn("arithmetic_correctness", result.proof["covered_obligations"])
        self.assertIn("overflow_handling", result.proof["covered_obligations"])
        self.assertIn("arithmetic_correctness", result.proof["capabilities"])


class CompilationReportTests(unittest.TestCase):

    def _two_adapter_report(self):
        adapters = (
            ContractAdapter("rust", capabilities=("arithmetic_correctness", "overflow_handling")),
            ContractAdapter("python", capabilities=("arithmetic_correctness",)),
        )
        return OceanicOrchestrator(adapters).run(_make_contract())

    def test_supported_results_filters_to_passing_adapters(self):
        report = self._two_adapter_report()
        self.assertEqual(len(report.supported_results), 1)
        self.assertEqual(report.supported_results[0].language, "rust")

    def test_dissent_aggregates_all_adapter_dissent(self):
        report = self._two_adapter_report()
        # Only python has dissent (overflow_handling)
        self.assertEqual(len(report.dissent), 1)
        self.assertIn("python:", report.dissent[0])
        self.assertIn("overflow_handling", report.dissent[0])

    def test_confidence_is_average_of_adapter_confidences(self):
        report = self._two_adapter_report()
        # rust=1.0, python=0.5 → average=0.75
        self.assertAlmostEqual(report.confidence, 0.75, places=6)

    def test_empty_report_has_zero_confidence(self):
        report = CompilationReport(contract_id="x", results=())
        self.assertEqual(report.confidence, 0.0)

    def test_contract_id_propagated_to_report(self):
        adapters = (ContractAdapter("rust", capabilities=("arithmetic_correctness",)),)
        report = OceanicOrchestrator(adapters).run(_make_contract())
        self.assertEqual(report.contract_id, "orch.test.v1")


class OceanicOrchestratorTests(unittest.TestCase):

    def test_single_adapter_run_returns_one_result(self):
        adapter = ContractAdapter("rust", capabilities=("arithmetic_correctness", "overflow_handling"))
        report = OceanicOrchestrator((adapter,)).run(_make_contract())
        self.assertEqual(len(report.results), 1)

    def test_multiple_adapters_run_returns_all_results(self):
        report = OceanicOrchestrator(default_adapters()).run(_make_contract())
        self.assertEqual(len(report.results), 3)

    def test_empty_adapters_produces_empty_report(self):
        report = OceanicOrchestrator(()).run(_make_contract())
        self.assertEqual(report.results, ())
        self.assertEqual(report.confidence, 0.0)
        self.assertEqual(report.dissent, ())

    def test_run_preserves_adapter_order(self):
        adapters = (
            ContractAdapter("first", capabilities=()),
            ContractAdapter("second", capabilities=("arithmetic_correctness",)),
            ContractAdapter("third", capabilities=("overflow_handling",)),
        )
        report = OceanicOrchestrator(adapters).run(_make_contract())
        self.assertEqual([r.language for r in report.results], ["first", "second", "third"])


class DefaultAdaptersTests(unittest.TestCase):

    def test_default_adapters_returns_three(self):
        adapters = default_adapters()
        self.assertEqual(len(adapters), 3)

    def test_default_adapters_languages(self):
        languages = {a.language for a in default_adapters()}
        self.assertEqual(languages, {"python", "rust", "typescript"})

    def test_rust_adapter_covers_both_obligations(self):
        rust = next(a for a in default_adapters() if a.language == "rust")
        result = rust.verify(_make_contract())
        self.assertTrue(result.supported)
        self.assertEqual(result.confidence, 1.0)

    def test_python_and_typescript_miss_overflow_handling(self):
        for adapter in default_adapters():
            if adapter.language in ("python", "typescript"):
                result = adapter.verify(_make_contract())
                self.assertFalse(result.supported)
                self.assertTrue(any("overflow_handling" in d for d in result.dissent))

    def test_all_adapters_cover_arithmetic_correctness(self):
        for adapter in default_adapters():
            result = adapter.verify(_make_contract(proof_obligations=("arithmetic_correctness",)))
            self.assertTrue(result.supported, f"{adapter.language} should support arithmetic_correctness")


class BackwardCompatTests(unittest.TestCase):

    def test_verification_report_is_compilation_report(self):
        self.assertIs(VerificationReport, CompilationReport)

    def test_verification_report_instance_is_compilation_report(self):
        adapters = (ContractAdapter("rust", capabilities=("arithmetic_correctness",)),)
        report = OceanicOrchestrator(adapters).run(_make_contract())
        self.assertIsInstance(report, CompilationReport)
        self.assertIsInstance(report, VerificationReport)


if __name__ == "__main__":
    unittest.main()

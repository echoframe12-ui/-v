"""Tests for verification_pipeline.py — verification pipeline and attestation generation.

Covers:
  - verify() preserves dissent, provenance, confidence, and result_hash
  - attest() requires verified result and produces attested Attestation
  - failed check produces 'held' status and cannot be attested (raises ValueError)
  - empty context produces 'held' status with confidence=None
  - VerificationCheck dataclass fields
  - checks array passed to verify() are all evaluated
  - multiple passing custom checks produce status 'verified'
  - attest() on unverified status raises ValueError
"""
import unittest

from context_assembly import ContextSource
from integration_pipeline import IntegrationPipeline
from perspectives import make_perspective
from verification_pipeline import VerificationCheck, VerificationPipeline, VerificationResult


class StubAdapter:
    def __init__(self, provider, model, response, confidence=None):
        self.provider = provider
        self.model = model
        self.response = response
        self.confidence = confidence

    def generate(self, context):
        return make_perspective(
            perspective_id=f"{self.provider}:{self.model}",
            provider=self.provider,
            model=self.model,
            response=self.response,
            context=context,
            confidence=self.confidence,
        )


class VerificationPipelineTests(unittest.TestCase):

    def _result(self):
        return IntegrationPipeline(
            [
                StubAdapter("local", "a", "approve", 0.8),
                StubAdapter("open", "b", "revise", 0.6),
                StubAdapter("hosted", "c", "approve", 0.7),
            ]
        ).run([ContextSource(ref="source", content="Evidence", authority="test")])

    def test_verify_preserves_dissent_and_provenance(self):
        result = self._result()
        verification = VerificationPipeline().verify(result)

        self.assertEqual(verification.status, "verified")
        self.assertTrue(verification.dissent)
        self.assertEqual(verification.provenance, ("source",))
        self.assertAlmostEqual(verification.confidence, 0.7)
        self.assertTrue(verification.result_hash)

    def test_attestation_requires_verified_result_and_provenance(self):
        result = self._result()
        verification = VerificationPipeline().verify(result)
        attestation = VerificationPipeline().attest(verification)

        self.assertEqual(attestation.status, "attested")
        self.assertEqual(attestation.verification_hash, verification.result_hash)
        self.assertEqual(attestation.provenance, ("source",))

    def test_failed_check_is_held_and_cannot_be_attested(self):
        result = self._result()
        verification = VerificationPipeline(
            checks=[
                lambda _: VerificationCheck("blocking_check", False, "manual hold")
            ],
        ).verify(result)

        self.assertEqual(verification.status, "held")
        with self.assertRaises(ValueError):
            VerificationPipeline().attest(verification)

    def test_empty_context_is_held(self):
        result = IntegrationPipeline([]).run([])
        verification = VerificationPipeline().verify(result)

        self.assertEqual(verification.status, "held")
        self.assertIsNone(verification.confidence)

    def test_verification_check_dataclass(self):
        chk = VerificationCheck("custom_chk", True, "all clear")
        self.assertEqual(chk.name, "custom_chk")
        self.assertTrue(chk.passed)
        self.assertEqual(chk.detail, "all clear")

    def test_multiple_custom_checks_all_pass(self):
        result = self._result()
        pipeline = VerificationPipeline(
            checks=[
                lambda _: VerificationCheck("chk_1", True),
                lambda _: VerificationCheck("chk_2", True),
            ]
        )
        verification = pipeline.verify(result)
        self.assertEqual(verification.status, "verified")
        # 4 default checks + 2 custom checks = 6 total checks
        self.assertEqual(len(verification.checks), 6)

    def test_attest_unverified_raises_valueerror(self):
        unverified = VerificationResult(
            status="unverified",
            confidence=0.5,
            checks=(),
            dissent=False,
            provenance=("source",),
            result_hash="fakehash",
        )
        with self.assertRaises(ValueError):
            VerificationPipeline().attest(unverified)



if __name__ == "__main__":
    unittest.main()


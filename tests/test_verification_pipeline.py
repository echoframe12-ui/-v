import unittest

from context_assembly import ContextSource
from integration_pipeline import IntegrationPipeline
from perspectives import make_perspective
from verification_pipeline import VerificationCheck, VerificationPipeline


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


if __name__ == "__main__":
    unittest.main()

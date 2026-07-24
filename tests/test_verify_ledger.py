import copy
import json
import os
import subprocess
import sys
import tempfile
import unittest

import status_digest
from attestation import GENESIS_HASH, AttestationEngine, link_hash
from verify_ledger import current_ids, verify_bundle, verify_digest, verify_receipt, _is_trustworthy

KEY = "operator-secret"
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _make_bundle(db_path, key=KEY, checkpoint=True):
    engine = AttestationEngine(db_path, signing_key=key)
    engine.attest("a", "one", ["plan"], 0.9)
    engine.attest("b", "two", [], 0.9)
    if checkpoint:
        engine.checkpoint()
    return engine.export()


class VerifyBundleTests(unittest.TestCase):
    def setUp(self):
        handle = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        handle.close()
        self.db_path = handle.name
        self.bundle = _make_bundle(self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_good_bundle_is_intact_and_trustworthy(self):
        report = verify_bundle(self.bundle, key=KEY)
        self.assertTrue(report["intact"])
        self.assertTrue(report["checkpointed"])
        self.assertTrue(report["checkpoint"]["signature_valid"])
        self.assertTrue(report["trustworthy"])

    def test_good_bundle_without_key_is_intact_but_unsigned(self):
        report = verify_bundle(self.bundle, key=None)
        self.assertTrue(report["intact"])
        # the chain still checks out; the signature just isn't validated
        self.assertFalse(report["checkpoint"]["signature_valid"])
        self.assertFalse(report["trustworthy"])

    def test_current_ids_reads_the_version_graph_offline(self):
        # no supersessions -> every attestation is current
        self.assertEqual(current_ids(self.bundle), [1, 2])
        # #1 superseded by #2 -> only #2 is current
        bundle = copy.deepcopy(self.bundle)
        bundle["supersessions"] = [{"old_id": 1, "new_id": 2, "actor": "a", "reason": "r"}]
        self.assertEqual(current_ids(bundle), [2])

    def test_missing_supersessions_key_treats_all_as_current(self):
        bundle = copy.deepcopy(self.bundle)
        bundle.pop("supersessions", None)
        self.assertEqual(current_ids(bundle), [1, 2])

    def test_editing_an_attestation_breaks_the_chain(self):
        tampered = copy.deepcopy(self.bundle)
        tampered["attestations"][0]["confidence"] = 0.1
        report = verify_bundle(tampered, key=KEY)
        self.assertFalse(report["intact"])
        self.assertEqual(report["broken_at"], tampered["attestations"][0]["id"])

    def test_recomputed_forward_rewrite_is_caught_by_the_seal(self):
        # rebuild the chain forward around an edit so the walk passes, exactly
        # as an attacker with the bundle would — the stale sealed head catches it
        tampered = copy.deepcopy(self.bundle)
        tampered["attestations"][0]["subject"] = "tampered"
        prev = GENESIS_HASH
        for entry in tampered["attestations"]:
            entry["prev_hash"] = prev
            entry["entry_hash"] = link_hash(prev, entry)
            prev = entry["entry_hash"]
        report = verify_bundle(tampered, key=KEY)
        self.assertTrue(report["intact"])  # chain walk fooled
        self.assertFalse(report["checkpoint"]["head_reproduced"])
        self.assertFalse(report["trustworthy"])

    def test_wrong_key_fails_the_signature(self):
        report = verify_bundle(self.bundle, key="not-the-key")
        self.assertFalse(report["checkpoint"]["signature_valid"])
        self.assertFalse(report["trustworthy"])

    def test_bundle_without_a_checkpoint_reports_uncheckpointed(self):
        engine_path = self.db_path + ".2"
        try:
            bundle = _make_bundle(engine_path, checkpoint=False)
            report = verify_bundle(bundle, key=KEY)
            self.assertTrue(report["intact"])
            self.assertFalse(report["checkpointed"])
        finally:
            if os.path.exists(engine_path):
                os.remove(engine_path)


def _attach_digest(bundle, key=KEY, **override):
    """Embed a signed posture digest that matches the bundle, minus any overrides."""
    cp_head = bundle["checkpoints"][-1]["head_hash"] if bundle["checkpoints"] else None
    payload = status_digest.build_payload(
        verify={"intact": True, "trustworthy": True, "length": len(bundle["attestations"])},
        cvi_value=0.9, sourced_ratio=1.0, dissent_rate=0.0,
        held_pending=0, held_breached=0,
        checkpoint_head=cp_head,
        generated_at="2026-07-24T00:00:00+00:00",
    )
    payload.update(override)  # tamper a signable field before signing, if asked
    signed = bundle.get("_sign_key", key)
    sig = status_digest.sign(signed, payload) if signed else None
    out = copy.deepcopy(bundle)
    out["digest"] = {**payload, "signed": sig is not None, "signature": sig}
    return out


class VerifyDigestTests(unittest.TestCase):
    def setUp(self):
        handle = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        handle.close()
        self.db_path = handle.name
        self.bundle = _make_bundle(self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_matching_digest_is_valid_and_consistent(self):
        bundle = _attach_digest(self.bundle)
        result = verify_digest(bundle, key=KEY)
        self.assertTrue(result["signature_valid"])
        self.assertTrue(result["chain_length_matches"])
        self.assertTrue(result["checkpoint_matches"])
        self.assertTrue(result["consistent"])

    def test_digest_claiming_a_different_length_is_inconsistent(self):
        # the signed posture says the chain is longer than the bundle actually is
        bundle = _attach_digest(self.bundle, chain_length=99)
        result = verify_digest(bundle, key=KEY)
        self.assertTrue(result["signature_valid"])  # genuinely signed…
        self.assertFalse(result["chain_length_matches"])  # …but describes another chain
        self.assertFalse(result["consistent"])

    def test_wrong_key_invalidates_the_digest_signature(self):
        bundle = _attach_digest(self.bundle)
        result = verify_digest(bundle, key="not-the-key")
        self.assertFalse(result["signature_valid"])
        self.assertTrue(result["consistent"])  # consistency is key-independent

    def test_inconsistent_digest_makes_the_bundle_untrustworthy(self):
        bundle = _attach_digest(self.bundle, chain_length=99)
        report = verify_bundle(bundle, key=KEY)
        report["digest"] = verify_digest(bundle, key=KEY)
        # the chain itself is fine, but its own signed summary contradicts it
        self.assertTrue(report["intact"])
        self.assertFalse(_is_trustworthy(report, KEY))

    def test_consistent_digest_keeps_a_good_bundle_trustworthy(self):
        bundle = _attach_digest(self.bundle)
        report = verify_bundle(bundle, key=KEY)
        report["digest"] = verify_digest(bundle, key=KEY)
        self.assertTrue(_is_trustworthy(report, KEY))


class VerifyReceiptTests(unittest.TestCase):
    def setUp(self):
        handle = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        handle.close()
        self.db_path = handle.name
        self.engine = AttestationEngine(self.db_path, signing_key=KEY)
        self.engine.attest("subj-a", "the output", ["plan"], 0.9)
        self.engine.attest("subj-b", "another", [], 0.4)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_a_genuine_receipt_verifies_independently(self):
        receipt = self.engine.receipt(1)
        result = verify_receipt(receipt)
        self.assertTrue(result["entry_hash_valid"])
        self.assertEqual(result["attestation_id"], 1)
        # asserted claims are echoed, not silently promoted to verified
        self.assertIn("entry_intact", result["asserted"])

    def test_content_binding_confirms_the_output(self):
        receipt = self.engine.receipt(1)
        self.assertTrue(verify_receipt(receipt, content="the output")["content_matches"])
        self.assertFalse(verify_receipt(receipt, content="not the output")["content_matches"])
        # without content, the binding is simply not asserted
        self.assertIsNone(verify_receipt(receipt)["content_matches"])

    def test_an_edited_receipt_fails_even_when_it_claims_intact(self):
        receipt = self.engine.receipt(1)
        # forge the content but keep the old (now-wrong) entry_hash and the
        # asserted intact flags — recomputation catches what the claim hides
        receipt["attestation"]["subject"] = "tampered"
        receipt["entry_intact"] = True
        receipt["chain_intact"] = True
        result = verify_receipt(receipt)
        self.assertFalse(result["entry_hash_valid"])
        self.assertTrue(result["asserted"]["entry_intact"])  # the lie is preserved…
        # …but the independent recomputation does not honour it

    def test_a_forged_content_hash_breaks_binding(self):
        receipt = self.engine.receipt(1)
        receipt["attestation"]["sha256"] = "0" * 64
        self.assertFalse(verify_receipt(receipt, content="the output")["content_matches"])


class VerifyLedgerCliTests(unittest.TestCase):
    """The script must run as a standalone integrity gate: exit 0 good, 1 tampered."""

    def setUp(self):
        handle = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        handle.close()
        self.db_path = handle.name
        self.bundle = _make_bundle(self.db_path)
        bundle_handle = tempfile.NamedTemporaryFile(
            delete=False, suffix=".json", mode="w"
        )
        json.dump(self.bundle, bundle_handle)
        bundle_handle.close()
        self.bundle_path = bundle_handle.name

    def tearDown(self):
        for path in (self.db_path, self.bundle_path):
            if os.path.exists(path):
                os.remove(path)

    def _run(self, *args):
        return subprocess.run(
            [sys.executable, "verify_ledger.py", *args],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )

    def test_exit_zero_for_a_good_bundle(self):
        result = self._run("--key", KEY, self.bundle_path)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('"trustworthy": true', result.stdout)

    def test_exit_nonzero_for_a_tampered_bundle(self):
        tampered = copy.deepcopy(self.bundle)
        tampered["attestations"][0]["confidence"] = 0.1
        with open(self.bundle_path, "w") as handle:
            json.dump(tampered, handle)
        result = self._run("--key", KEY, self.bundle_path)
        self.assertEqual(result.returncode, 1)
        self.assertIn('"intact": false', result.stdout)


if __name__ == "__main__":
    unittest.main()

import sqlite3
import unittest
from unittest.mock import patch

import app as app_module
from app import app
from oceanicos_client import OceanicOSClient, OceanicOSError


def _flask_opener(method, path, headers, json):
    """Transport that speaks to the real routes via the Flask test client.

    Mirrors the default requests opener: parsed JSON when the body is JSON, else
    the raw text (so text/markdown endpoints like /report round-trip).
    """
    resp = app.test_client().open(path, method=method, headers=headers, json=json)
    body = resp.get_json(silent=True)
    if body is None:
        body = resp.get_data(as_text=True)
    return resp.status_code, body


class OceanicOSClientTests(unittest.TestCase):
    _TRANSIENT_TABLES = [
        "users",
        "attestations",
        "attestation_checkpoints",
        "usage",
        "held_reviews",
        "drift_audits",
        "cvi_snapshots",
        "evolution_snapshots",
        "consensus_evaluations",
        "supersessions",
    ]

    def setUp(self):
        self.kai = OceanicOSClient(opener=_flask_opener)
        # Wipe all transient tables before each test for full isolation.
        # Also reset ROWID sequences so id-based assertions are stable.
        db_path = str(app_module.auth_registry._db_path)
        with sqlite3.connect(db_path) as conn:
            for table in self._TRANSIENT_TABLES:
                conn.execute(f"DELETE FROM {table}")  # noqa: S608
                conn.execute(
                    "DELETE FROM sqlite_sequence WHERE name = ?", (table,)
                )

    def test_public_reads(self):
        self.assertEqual(self.kai.health()["status"], "ok")
        self.assertIn("cvi", self.kai.cvi())
        self.assertIn("posture", self.kai.status())
        self.assertIn("records_total", self.kai.evolution())
        self.assertEqual(self.kai.doctrine()["invariant"], "Continuous Becoming")
        self.assertIn("intact", self.kai.verify())
        self.assertIn("sourced_ratio", self.kai.stats())
        # the report is Markdown text, not JSON — the opener round-trips it
        self.assertIn("# OceanicOS Trust Report", self.kai.report())

    def test_trust_timeline_via_client(self):
        # a build moves the CVI and the footprint; an audit records the posture
        app_module.auth_registry.admin_users.add("client-timeline")
        try:
            self.kai.register("client-timeline")
            self.kai._call("POST", "/builder/run", {"task": "compound the record"})
            self.kai._call("POST", "/attestations/audit", None)
            # the three histories are reachable individually
            self.assertIsInstance(self.kai.cvi_history(), list)
            evo = self.kai.evolution_history()
            self.assertIn("growth", evo)
            self.assertIn("history", evo)
            pos = self.kai.posture_history()
            self.assertIn("current", pos)
            self.assertIn("transitions", pos)
            # …and together in one call
            tl = self.kai.timeline()
            self.assertEqual(set(tl), {"cvi", "evolution", "posture"})
            self.assertGreaterEqual(len(tl["cvi"]), 1)
            self.assertEqual(tl["posture"]["current"], pos["current"])
            # limit is honoured
            self.assertLessEqual(len(self.kai.cvi_history(limit=1)), 1)
        finally:
            app_module.auth_registry.admin_users.discard("client-timeline")

    def test_supersession_and_lineage_via_client(self):
        eng = app_module.attestation_engine
        v1 = eng.attest("client-charter", "one", ["plan"], 0.9)
        v2 = eng.attest("client-charter", "two", ["plan"], 0.95)
        self.kai.register("client-super")
        self.kai.supersede(v2["id"], v1["id"], "re-verified")
        self.assertFalse(self.kai.lineage(v1["id"])["is_current"])
        self.assertTrue(self.kai.lineage(v2["id"])["is_current"])

    def test_register_sets_token_and_enables_authed_calls(self):
        token = self.kai.register("client-analyst")
        self.assertTrue(token)
        self.assertEqual(self.kai._token, token)
        # consensus requires a token; it now works
        result = self.kai.consensus("ship it now")
        self.assertIn("dissent_score", result)
        self.assertIn("majority", result)

    def test_attest_then_read_back_via_client(self):
        att = app_module.attestation_engine.attest("client-subj", "the output", ["plan"], 0.9)
        # content-addressable lookup finds it
        found = self.kai.lookup("the output")
        self.assertTrue(found["found"])
        # receipt for the id
        receipt = self.kai.receipt(att["id"])
        self.assertEqual(receipt["attestation"]["sha256"], att["sha256"])
        # subject history
        history = self.kai.subject_history("client-subj")
        self.assertGreaterEqual(history["count"], 1)

    def test_admin_call_requires_admin_token(self):
        # without an admin token, attention is forbidden -> raises
        self.kai.register("client-member")
        with self.assertRaises(OceanicOSError) as ctx:
            self.kai.attention()
        self.assertEqual(ctx.exception.status, 403)

    def test_admin_attention_with_admin_token(self):
        app_module.auth_registry.admin_users.add("client-steward")
        try:
            self.kai.register("client-steward")
            self.assertIsInstance(self.kai.attention(), list)
        finally:
            app_module.auth_registry.admin_users.discard("client-steward")

    def test_verify_digest_locally(self):
        app_module.attestation_engine.attest("client-digest", "body", ["plan"], 0.9)
        with patch.dict("os.environ", {"OCEANICOS_SIGNING_KEY": "client-key"}, clear=False):
            # fetch-and-verify in one call with the right key
            self.assertTrue(self.kai.verify_digest("client-key"))
            # a wrong key does not verify
            self.assertFalse(self.kai.verify_digest("wrong-key"))
            # a supplied, tampered digest does not verify
            digest = self.kai.status_digest()
        self.assertTrue(self.kai.verify_digest("client-key", {**digest}))
        self.assertFalse(self.kai.verify_digest("client-key", {**digest, "posture": "BROKEN"}))
        # the dissent rate is inside what the signature covers (round 0075)
        self.assertFalse(self.kai.verify_digest("client-key", {**digest, "dissent_rate": 0.999}))

    def test_verify_receipt_locally(self):
        att = app_module.attestation_engine.attest("client-receipt", "the payload", ["plan"], 0.9)
        # fetch-and-verify: the entry hash recomputes, and the content binds
        result = self.kai.verify_receipt(att["id"], content="the payload")
        self.assertTrue(result["entry_hash_valid"])
        self.assertTrue(result["content_matches"])
        self.assertEqual(result["attestation_id"], att["id"])
        # a wrong content does not bind to the receipt
        self.assertFalse(self.kai.verify_receipt(att["id"], content="wrong")["content_matches"])
        # without content, entry integrity still verifies
        self.assertTrue(self.kai.verify_receipt(att["id"])["entry_hash_valid"])

    def test_verify_digest_false_when_unsigned(self):
        # no signing key -> unsigned digest -> nothing to verify
        with patch.dict("os.environ", {}, clear=False):
            import os
            os.environ.pop("OCEANICOS_SIGNING_KEY", None)
            self.assertFalse(self.kai.verify_digest("any-key"))

    def test_error_raises_with_status(self):
        with self.assertRaises(OceanicOSError) as ctx:
            self.kai.receipt(999999)
        self.assertEqual(ctx.exception.status, 404)


if __name__ == "__main__":
    unittest.main()

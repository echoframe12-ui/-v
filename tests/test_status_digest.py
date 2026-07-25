import unittest

import status_digest


BASE = {
    "posture": "TRUSTWORTHY",
    "cvi": 0.9,
    "sourced_ratio": 0.75,
    "dissent_rate": 0.25,
    "chain_intact": True,
    "trustworthy": True,
    "chain_length": 4,
    "held_pending": 1,
    "held_breached": 0,
    "checkpoint_head": "abc123",
    "generated_at": "2026-07-23T00:00:00+00:00",
}


class CanonicalTests(unittest.TestCase):
    def test_canonical_is_deterministic_and_order_independent(self):
        reordered = dict(reversed(list(BASE.items())))
        self.assertEqual(status_digest.canonical(BASE), status_digest.canonical(reordered))

    def test_canonical_ignores_extra_fields(self):
        with_extra = {**BASE, "signed": True, "signature": "x"}
        self.assertEqual(status_digest.canonical(BASE), status_digest.canonical(with_extra))


class PostureTests(unittest.TestCase):
    def test_posture_verdicts(self):
        self.assertEqual(status_digest.posture_of({"intact": False}), "BROKEN")
        self.assertEqual(
            status_digest.posture_of({"intact": True, "trustworthy": True}), "TRUSTWORTHY"
        )
        self.assertEqual(status_digest.posture_of({"intact": True}), "INTACT")

    def test_build_payload_has_exactly_the_signable_fields(self):
        payload = status_digest.build_payload(
            verify={"intact": True, "trustworthy": True, "length": 3},
            cvi_value=0.9,
            sourced_ratio=0.5,
            dissent_rate=0.5,
            held_pending=1,
            held_breached=0,
            checkpoint_head="h",
            generated_at="2026-07-23T00:00:00+00:00",
        )
        self.assertEqual(set(payload), set(status_digest.SIGNABLE_FIELDS))
        self.assertEqual(payload["posture"], "TRUSTWORTHY")
        self.assertEqual(payload["chain_length"], 3)
        self.assertEqual(payload["dissent_rate"], 0.5)


class TransitionsTests(unittest.TestCase):
    def _audit(self, id, intact, trustworthy, at):
        return {"id": id, "intact": intact, "trustworthy": trustworthy, "length": id, "checked_at": at}

    def test_collapses_runs_into_change_points(self):
        audits = [
            self._audit(1, True, False, "t1"),   # INTACT
            self._audit(2, True, False, "t2"),   # INTACT (no change)
            self._audit(3, True, True, "t3"),    # -> TRUSTWORTHY
            self._audit(4, False, False, "t4"),  # -> BROKEN
            self._audit(5, True, True, "t5"),    # -> TRUSTWORTHY
        ]
        changes = status_digest.transitions(audits)
        self.assertEqual(
            [(c["from"], c["to"]) for c in changes],
            [(None, "INTACT"), ("INTACT", "TRUSTWORTHY"),
             ("TRUSTWORTHY", "BROKEN"), ("BROKEN", "TRUSTWORTHY")],
        )
        # each change carries when and where it happened
        self.assertEqual(changes[2]["at"], "t4")
        self.assertEqual(changes[2]["audit_id"], 4)

    def test_no_audits_is_no_transitions(self):
        self.assertEqual(status_digest.transitions([]), [])

    def test_a_steady_posture_is_a_single_transition_from_null(self):
        audits = [self._audit(i, True, True, f"t{i}") for i in range(1, 4)]
        changes = status_digest.transitions(audits)
        self.assertEqual(len(changes), 1)
        self.assertEqual((changes[0]["from"], changes[0]["to"]), (None, "TRUSTWORTHY"))


class SignVerifyTests(unittest.TestCase):
    def test_sign_then_verify_roundtrip(self):
        sig = status_digest.sign("secret", BASE)
        self.assertTrue(status_digest.verify(BASE, sig, "secret"))

    def test_wrong_key_fails(self):
        sig = status_digest.sign("secret", BASE)
        self.assertFalse(status_digest.verify(BASE, sig, "other"))

    def test_tampered_payload_fails(self):
        sig = status_digest.sign("secret", BASE)
        tampered = {**BASE, "posture": "BROKEN"}
        self.assertFalse(status_digest.verify(tampered, sig, "secret"))

    def test_no_key_never_verifies(self):
        sig = status_digest.sign("secret", BASE)
        self.assertFalse(status_digest.verify(BASE, sig, None))
        self.assertFalse(status_digest.verify(BASE, "", "secret"))


if __name__ == "__main__":
    unittest.main()

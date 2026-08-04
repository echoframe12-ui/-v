import base64

import pytest

from omega_signer import ENV_PRIVATE_KEY, OmegaSigner


def test_key_id_is_stable_for_same_private_key():
    signer = OmegaSigner.generate_for_provisioning()
    restored = OmegaSigner.from_private_bytes(signer.private_key)
    assert restored.key_id == signer.key_id
    assert restored.public_key == signer.public_key


def test_environment_provisioning_round_trips(monkeypatch):
    signer = OmegaSigner.generate_for_provisioning()
    monkeypatch.setenv(ENV_PRIVATE_KEY, signer.private_key_b64())
    restored = OmegaSigner.from_environment()
    assert restored.private_key == signer.private_key
    assert restored.public_key == signer.public_key
    assert restored.key_id == signer.key_id


def test_environment_requires_explicit_key(monkeypatch):
    monkeypatch.delenv(ENV_PRIVATE_KEY, raising=False)
    with pytest.raises(RuntimeError, match="not configured"):
        OmegaSigner.from_environment()


def test_environment_rejects_bad_base64(monkeypatch):
    monkeypatch.setenv(ENV_PRIVATE_KEY, "not-base64")
    with pytest.raises(ValueError, match="valid base64"):
        OmegaSigner.from_environment()


def test_environment_rejects_wrong_key_length(monkeypatch):
    monkeypatch.setenv(ENV_PRIVATE_KEY, base64.b64encode(b"short").decode())
    with pytest.raises(ValueError, match="exactly 32"):
        OmegaSigner.from_environment()


def test_private_key_is_not_exposed_as_verifier_material():
    signer = OmegaSigner.generate_for_provisioning()
    assert signer.public_key_b64() != signer.private_key_b64()
    assert signer.key_id.startswith("sha256:")

from __future__ import annotations

"""Stable Ed25519 signer provisioning for Ω∞v service integrations.

The signer keeps key lifecycle separate from attestation construction. Private
key material is supplied explicitly or through an environment variable; it is
never serialized into an attestation envelope.
"""

import base64
import os
from dataclasses import dataclass

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, NoEncryption, PrivateFormat, PublicFormat

from attestation_protocol import sha256_hex

ENV_PRIVATE_KEY = "OMEGA_ATTESTATION_PRIVATE_KEY_B64"


@dataclass(frozen=True)
class OmegaSigner:
    """Provisioned Ω∞v Ed25519 identity with stable key ID."""

    private_key: bytes
    public_key: bytes
    key_id: str

    @classmethod
    def from_private_bytes(cls, private_key: bytes) -> "OmegaSigner":
        if len(private_key) != 32:
            raise ValueError("Ed25519 private key must contain exactly 32 raw bytes")
        key = Ed25519PrivateKey.from_private_bytes(private_key)
        public = key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
        return cls(private_key=private_key, public_key=public, key_id=sha256_hex(public))

    @classmethod
    def from_environment(cls, name: str = ENV_PRIVATE_KEY) -> "OmegaSigner":
        value = os.environ.get(name)
        if not value:
            raise RuntimeError(f"Ω∞v signing key is not configured: {name}")
        try:
            private = base64.b64decode(value.encode("ascii"), validate=True)
        except (ValueError, UnicodeEncodeError) as exc:
            raise ValueError(f"{name} must be valid base64") from exc
        return cls.from_private_bytes(private)

    @classmethod
    def generate_for_provisioning(cls) -> "OmegaSigner":
        key = Ed25519PrivateKey.generate()
        private = key.private_bytes(Encoding.Raw, PrivateFormat.Raw, NoEncryption())
        return cls.from_private_bytes(private)

    def public_key_b64(self) -> str:
        return base64.b64encode(self.public_key).decode("ascii")

    def private_key_b64(self) -> str:
        return base64.b64encode(self.private_key).decode("ascii")

"""A thin Python client for the OceanicOS VaaS API — the "Python API Proxy" interface.

Wraps the platform's HTTP endpoints in a small, typed surface so a consumer can
attest, read the trust posture, and verify the record without hand-rolling
requests. The transport is injectable: by default it speaks HTTP to a running
service, but a test (or an in-process caller) can pass an `opener` backed by the
Flask test client, so the client is exercised against the real routes and cannot
drift from them.

    from oceanicos_client import OceanicOSClient
    kai = OceanicOSClient("http://localhost:8000")
    print(kai.cvi()["cvi"])
    token = kai.register("analyst")          # sets the client's token
    print(kai.consensus("ship it")["dissent_score"])
"""
from __future__ import annotations

from typing import Any, Callable, Optional
from urllib.parse import quote

# opener(method, path, headers, json) -> (status_code, parsed_body)
Opener = Callable[[str, str, dict, Optional[dict]], "tuple[int, Any]"]


class OceanicOSError(RuntimeError):
    """A non-2xx response from the platform."""

    def __init__(self, status: int, body: Any) -> None:
        message = body.get("error") if isinstance(body, dict) else body
        super().__init__(f"HTTP {status}: {message}")
        self.status = status
        self.body = body


def _requests_opener(base_url: str) -> Opener:
    """The default transport — real HTTP via `requests` (imported lazily)."""
    import requests

    def opener(method: str, path: str, headers: dict, json: Optional[dict]):
        resp = requests.request(method, base_url + path, headers=headers, json=json, timeout=30)
        try:
            body = resp.json()
        except ValueError:
            body = resp.text
        return resp.status_code, body

    return opener


class OceanicOSClient:
    """A small client over the OceanicOS API. Token is optional; set it via `register`."""

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        token: Optional[str] = None,
        opener: Optional[Opener] = None,
    ) -> None:
        self._base = base_url.rstrip("/")
        self._token = token
        self._opener = opener or _requests_opener(self._base)

    # ---- transport ----
    def _headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        return headers

    def _call(self, method: str, path: str, json: Optional[dict] = None) -> Any:
        status, body = self._opener(method, path, self._headers(), json)
        if status >= 400:
            raise OceanicOSError(status, body)
        return body

    # ---- auth ----
    def register(self, username: str) -> str:
        """Register (or re-fetch) a token for `username` and remember it on the client."""
        body = self._call("POST", "/auth/register", {"username": username})
        self._token = body["token"]
        return self._token

    # ---- reads (public) ----
    def health(self) -> Any:
        return self._call("GET", "/health")

    def cvi(self) -> Any:
        return self._call("GET", "/cvi")

    def status(self) -> Any:
        """The machine-readable trust posture (`/status.json`)."""
        return self._call("GET", "/status.json")

    def status_digest(self) -> Any:
        return self._call("GET", "/status/digest")

    def verify_digest(self, key: str, digest: Optional[dict] = None) -> bool:
        """Locally confirm a signed digest genuinely came from the platform.

        The digest is meant to be handed to a third party over an untrusted
        channel; this closes the loop for an SDK consumer — verification is a pure,
        offline HMAC check needing only the shared operator `key`, no network call
        and no trust in the transport that delivered the digest. Pass a `digest`
        (e.g. one received out of band) or omit it to fetch the platform's current
        one first. Returns False for an unsigned digest (no signature to check).

        Uses the platform's own `status_digest` module to verify exactly the way
        the service signs, so the client cannot drift from the signing scheme.
        """
        import status_digest

        payload = digest if digest is not None else self.status_digest()
        return status_digest.verify(payload, payload.get("signature"), key)

    def evolution(self) -> Any:
        return self._call("GET", "/evolution")

    # ---- trust over time (the three histories) ----
    def cvi_history(self, actor: str = "", limit: Optional[int] = None) -> Any:
        """The CVI trend — the index over time (`/cvi/history`)."""
        query = []
        if actor:
            query.append("actor=" + quote(actor, safe=""))
        if limit is not None:
            query.append("limit=" + str(int(limit)))
        suffix = ("?" + "&".join(query)) if query else ""
        return self._call("GET", "/cvi/history" + suffix)

    def evolution_history(self, limit: Optional[int] = None) -> Any:
        """The compounding footprint over time — the growth curve (`/evolution/history`)."""
        suffix = f"?limit={int(limit)}" if limit is not None else ""
        return self._call("GET", "/evolution/history" + suffix)

    def posture_history(self, limit: Optional[int] = None) -> Any:
        """When trust changed state — the posture verdict's transitions (`/posture/history`)."""
        suffix = f"?limit={int(limit)}" if limit is not None else ""
        return self._call("GET", "/posture/history" + suffix)

    def timeline(self, limit: Optional[int] = None) -> dict:
        """The whole trust timeline in one call — index, footprint, and verdict over time.

        The data behind the `/timeline` page, assembled client-side: the CVI trend,
        the growth curve, and the posture transitions together, so a monitor can pull
        "how has trust moved" in a single method instead of three requests.
        """
        return {
            "cvi": self.cvi_history(limit=limit),
            "evolution": self.evolution_history(limit=limit),
            "posture": self.posture_history(limit=limit),
        }

    def doctrine(self) -> Any:
        return self._call("GET", "/doctrine")

    def verify(self) -> Any:
        """The whole-chain integrity report (`/attestations/verify`)."""
        return self._call("GET", "/attestations/verify")

    def stats(self) -> Any:
        return self._call("GET", "/attestations/stats")

    def receipt(self, att_id: int) -> Any:
        return self._call("GET", f"/attestations/{int(att_id)}/receipt")

    def lineage(self, att_id: int) -> Any:
        """Supersession lineage — is this the current verified version?"""
        return self._call("GET", f"/attestations/{int(att_id)}/lineage")

    def verify_receipt(self, att_id: int, content: Optional[str] = None) -> dict:
        """Fetch a receipt and independently confirm it, offline — recompute, don't trust.

        Completes the recipient story for the third artifact the platform hands out:
        as `verify_digest` checks a signed posture and `verify_bundle` checks a
        record, this recomputes a single attestation's own `link_hash` rather than
        believing the receipt's asserted `entry_intact` flag, so a receipt whose
        content was edited fails even though it claims to be intact. Pass the
        original `content` to also bind the receipt to it by SHA-256.

        Uses the platform's own `verify_ledger.verify_receipt`, so the client checks
        an entry exactly the way the ledger hashes one and cannot drift.
        """
        import verify_ledger

        receipt = self.receipt(att_id)
        return verify_ledger.verify_receipt(receipt, content=content)

    def subject_history(self, subject: str) -> Any:
        return self._call("GET", "/attestations/history?subject=" + quote(subject, safe=""))

    def lookup(self, content: str) -> Any:
        """Content-addressable lookup — was this exact output attested?"""
        return self._call("POST", "/attestations/lookup", {"content": content})

    def report(self) -> str:
        """The composed, human-readable Markdown trust report (`/report`)."""
        return self._call("GET", "/report")

    # ---- writes (authed) ----
    def consensus(self, prompt: str) -> Any:
        """Convene the dissent panel on a prompt (requires a token)."""
        return self._call("POST", "/models/consensus", {"prompt": prompt})

    def attention(self) -> Any:
        """The steward attention worklist (requires an admin token)."""
        return self._call("GET", "/attestations/attention")

    def supersede(self, new_id: int, old_id: int, reason: str) -> Any:
        """Record that attestation `new_id` supersedes `old_id` (requires a token)."""
        return self._call(
            "POST", f"/attestations/{int(new_id)}/supersedes",
            {"old_id": int(old_id), "reason": reason},
        )

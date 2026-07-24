#!/usr/bin/env python3
"""Verify an exported OceanicOS attestation ledger — offline, without the system.

The running service can attest to its own record via /attestations/verify. This
script does the same from a bundle exported by /attestations/export, importing
only the pure hashing and signing functions the engine uses — no Flask, no
database, no engine instance. It is the ground truth surviving the system:
anyone holding the bundle (and, for the seal, the key) can confirm the record
was neither edited in place nor rewritten wholesale.

Usage:
    python verify_ledger.py bundle.json               # chain integrity only
    python verify_ledger.py --key SECRET bundle.json  # + signed-checkpoint check
    curl .../attestations/export | python verify_ledger.py --key SECRET -

Exit code 0 when the record is intact (and, when --key is given, trustworthy);
non-zero otherwise — so it doubles as a CI or cron integrity gate.
"""
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import sys
from typing import Any

import status_digest
from attestation import GENESIS_HASH, checkpoint_signature, link_hash


def verify_bundle(bundle: dict[str, Any], key: str | None = None) -> dict[str, Any]:
    """Recompute the integrity report purely from an exported bundle.

    Mirrors ``AttestationEngine.verify`` but reads the chain and checkpoints out
    of the bundle rather than a live database, so the same guarantees hold with
    nothing running. Walks the hash chain (edit-in-place detection) and, when a
    key is supplied, validates the latest signed checkpoint (whole-rewrite
    detection): trustworthy only when the chain is intact, the sealed head is
    still reproduced at its length, and the signature validates under the key.
    """
    attestations = bundle.get("attestations", [])
    checkpoints = bundle.get("checkpoints", [])

    prev_hash = GENESIS_HASH
    for entry in attestations:
        expected = link_hash(prev_hash, entry)
        if entry["prev_hash"] != prev_hash or entry["entry_hash"] != expected:
            return {
                "intact": False,
                "length": len(attestations),
                "broken_at": entry["id"],
            }
        prev_hash = entry["entry_hash"]
    chain = {
        "intact": True,
        "length": len(attestations),
        "broken_at": None,
        "head": prev_hash,
    }

    if not checkpoints:
        return {**chain, "checkpointed": False}

    cp = checkpoints[-1]
    head_reproduced = (
        len(attestations) >= cp["length"] > 0
        and attestations[cp["length"] - 1]["entry_hash"] == cp["head_hash"]
    ) or (cp["length"] == 0 and cp["head_hash"] == GENESIS_HASH)
    signature_valid = bool(key) and hmac.compare_digest(
        cp["signature"], checkpoint_signature(key, cp["head_hash"], cp["length"])
    )
    return {
        **chain,
        "checkpointed": True,
        "checkpoint": {
            "head_hash": cp["head_hash"],
            "length": cp["length"],
            "created_at": cp.get("created_at"),
            "signature_valid": signature_valid,
            "head_reproduced": head_reproduced,
        },
        "trustworthy": bool(chain["intact"] and head_reproduced and signature_valid),
    }


def verify_receipt(receipt: dict[str, Any], content: str | None = None) -> dict[str, Any]:
    """Independently verify a single attestation receipt — recompute, don't trust.

    The per-item receipt (`/attestations/{id}/receipt`) is the proof a client
    presents for one record. This confirms it offline from the receipt alone, by
    recomputing the entry's own `link_hash` from its content fields and recorded
    predecessor rather than believing the receipt's asserted `entry_intact` flag —
    a fabricated receipt whose content was edited fails here even though it claims
    to be intact. Given the original `content`, it also binds the receipt to that
    content by recomputing its SHA-256.

    Pure over the receipt. Reports:
    - `entry_hash_valid`: the recomputed `link_hash(prev_hash, entry)` equals the
      receipt's stored `entry_hash` — the entry's content and prev-linkage are
      self-consistent, independent of any service.
    - `content_matches`: `sha256(content)` equals the entry's `sha256` (only when
      `content` is supplied; otherwise `None`).
    - `asserted`: the receipt's own chain-wide claims (`entry_intact`,
      `chain_intact`, `sealed`) — echoed, not re-derived, since proving them needs
      the full ledger, not one receipt. Named honestly so a caller does not mistake
      an echo for an independent check.
    """
    entry = receipt.get("attestation") or {}
    recomputed = None
    try:
        recomputed = link_hash(entry["prev_hash"], entry)
    except (KeyError, TypeError):
        recomputed = None
    entry_hash_valid = recomputed is not None and recomputed == entry.get("entry_hash")
    content_matches = (
        None if content is None
        else hashlib.sha256(content.encode()).hexdigest() == entry.get("sha256")
    )
    return {
        "attestation_id": entry.get("id"),
        "sha256": entry.get("sha256"),
        "entry_hash_valid": bool(entry_hash_valid),
        "content_matches": content_matches,
        "asserted": {
            "entry_intact": receipt.get("entry_intact"),
            "chain_intact": receipt.get("chain_intact"),
            "sealed": receipt.get("sealed"),
        },
    }


def verify_digest(bundle: dict[str, Any], key: str | None = None) -> dict[str, Any]:
    """Cross-check a signed posture digest against the chain it ships with.

    A bundle from `/attestations/export` embeds the platform's signed status digest
    (`DECISIONS/0075`). Verifying the chain proves the record was not edited or
    rewritten; this proves the platform's *own summary* of that record is both
    genuine and consistent with what the bundle actually contains — a self-report
    that disagrees with its own ledger is caught here.

    Pure over the bundle. Reports:
    - `signature_valid`: the digest's HMAC validates under `key` (requires a key).
    - `chain_length_matches`: the digest's `chain_length` equals the bundle's
      attestation count.
    - `checkpoint_matches`: the digest's `checkpoint_head` equals the bundle's
      latest checkpoint head (or both absent).
    - `consistent`: the two cross-checks agree — the signed posture describes this
      exact chain, independent of the key.
    """
    digest = bundle.get("digest") or {}
    attestations = bundle.get("attestations", [])
    checkpoints = bundle.get("checkpoints", [])
    cp_head = checkpoints[-1]["head_hash"] if checkpoints else None

    chain_length_matches = digest.get("chain_length") == len(attestations)
    checkpoint_matches = digest.get("checkpoint_head") == cp_head
    signature_valid = bool(key) and status_digest.verify(
        digest, digest.get("signature"), key
    )
    return {
        "present": True,
        "signature_valid": signature_valid,
        "chain_length_matches": chain_length_matches,
        "checkpoint_matches": checkpoint_matches,
        "consistent": bool(chain_length_matches and checkpoint_matches),
    }


def current_ids(bundle: dict[str, Any]) -> list[int]:
    """The attestation ids no supersession replaces — the current versions.

    Read purely from the bundle's `attestations` and `supersessions`, so an
    offline holder can tell which versions are current without a service. A
    bundle with no supersession graph reports every attestation as current.
    """
    superseded = {s["old_id"] for s in bundle.get("supersessions", [])}
    return [a["id"] for a in bundle.get("attestations", []) if a["id"] not in superseded]


def full_report(bundle: dict[str, Any], key: str | None = None) -> dict[str, Any]:
    """The complete verification report for a bundle — one source for both verifiers.

    Assembles chain integrity and the seal (`verify_bundle`), the version-graph
    counts when the bundle carries supersessions, and the embedded-digest
    cross-check when it carries a digest. The offline CLI (`main`) and the online
    twin (`/attestations/verify-bundle`) both call this, so a caller gets the same
    report whichever verifier they reach — the twin cannot fall behind the CLI.
    """
    report = verify_bundle(bundle, key=key)
    # surface the version graph when the bundle carries one — chain verification is
    # unchanged; this only reports which attestations are current.
    if bundle.get("supersessions"):
        current = current_ids(bundle)
        report["current_attestations"] = len(current)
        report["superseded_attestations"] = len(bundle.get("attestations", [])) - len(current)
    # cross-check the embedded signed posture digest against this chain, when present
    if bundle.get("digest"):
        report["digest"] = verify_digest(bundle, key=key)
    return report


def _is_trustworthy(report: dict[str, Any], key: str | None) -> bool:
    """Success = chain intact, and — when a key was given — trustworthy too.

    An embedded digest that contradicts its own chain fails regardless of the key
    (consistency is key-independent), and an invalid signature fails when a key was
    given — a self-report that disagrees with the record it ships with is not a
    trustworthy bundle, even if the chain itself is intact.
    """
    if not report["intact"]:
        return False
    digest = report.get("digest")
    if digest:
        if not digest["consistent"]:
            return False
        if key and not digest["signature_valid"]:
            return False
    if key and report.get("checkpointed"):
        return bool(report.get("trustworthy"))
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "bundle",
        help="path to an exported ledger bundle, or '-' to read from stdin",
    )
    parser.add_argument(
        "--key",
        default=None,
        help="signing key, to validate the checkpoint signature (optional)",
    )
    args = parser.parse_args(argv)

    raw = sys.stdin.read() if args.bundle == "-" else open(args.bundle).read()
    bundle = json.loads(raw)

    report = full_report(bundle, key=args.key)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if _is_trustworthy(report, args.key) else 1


if __name__ == "__main__":
    raise SystemExit(main())

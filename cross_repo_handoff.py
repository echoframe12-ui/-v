from __future__ import annotations

"""Cross-repository state handoff engine for the Ω∞ Oceanic stack.

Manages durable, hash-verifiable state handoffs across repositories (A → B → C → A → ∞),
preserving ledger continuity, attestation lineage, and MOOD integrity across token-limited
and distributed runtime boundaries.
"""

import hashlib
import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

from attestation_protocol import hash_json
from continuous_becoming import BecomingTransition, ContinuousBecomingEngine


@dataclass(frozen=True)
class HandoffPacket:
    packet_id: str
    source_repo: str
    target_repo: str
    sequence: int
    state_hash: str
    ledger_head_hash: str
    payload: dict[str, Any]
    timestamp: str
    attestation_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> HandoffPacket:
        return cls(
            packet_id=str(data["packet_id"]),
            source_repo=str(data["source_repo"]),
            target_repo=str(data["target_repo"]),
            sequence=int(data["sequence"]),
            state_hash=str(data["state_hash"]),
            ledger_head_hash=str(data["ledger_head_hash"]),
            payload=dict(data.get("payload", {})),
            timestamp=str(data["timestamp"]),
            attestation_id=data.get("attestation_id"),
        )


class CrossRepoHandoffEngine:
    """Engine for exporting, importing, and verifying cross-repository state handoffs."""

    def __init__(self, ledger: Any | None = None) -> None:
        self._ledger = ledger
        self._becoming_engine = ContinuousBecomingEngine()

    def export_handoff(
        self,
        source_repo: str,
        target_repo: str,
        payload: dict[str, Any],
        *,
        sequence: int = 1,
        attestation_id: str | None = None,
    ) -> HandoffPacket:
        """Package and record a state handoff from source_repo to target_repo."""
        packet_id = f"handoff-{uuid.uuid4().hex[:12]}"
        timestamp = datetime.now(timezone.utc).isoformat()
        state_hash = hash_json(payload)

        ledger_head = ""
        if self._ledger is not None:
            if not self._ledger.verify_chain():
                raise ValueError("Ledger chain invalid prior to handoff export")
            history = self._ledger.history()
            ledger_head = history[-1].event_digest if history else ""

        packet = HandoffPacket(
            packet_id=packet_id,
            source_repo=source_repo,
            target_repo=target_repo,
            sequence=sequence,
            state_hash=state_hash,
            ledger_head_hash=ledger_head,
            payload=payload,
            timestamp=timestamp,
            attestation_id=attestation_id,
        )

        if self._ledger is not None:
            self._ledger.append(
                event_type="handoff.exported",
                entity_id=packet_id,
                payload=packet.to_dict(),
            )

        return packet

    def import_handoff(
        self,
        packet: HandoffPacket | dict[str, Any],
        *,
        expected_sequence: int | None = None,
    ) -> dict[str, Any]:
        """Import, verify integrity of, and accept a handoff packet."""
        pkt = packet if isinstance(packet, HandoffPacket) else HandoffPacket.from_dict(packet)

        # 1. Re-verify state hash
        recomputed_hash = hash_json(pkt.payload)
        if recomputed_hash != pkt.state_hash:
            raise ValueError(
                f"Handoff packet state hash mismatch: computed {recomputed_hash}, got {pkt.state_hash}"
            )

        # 2. Sequence check if expected_sequence provided
        if expected_sequence is not None and pkt.sequence != expected_sequence:
            raise ValueError(
                f"Handoff sequence mismatch: expected {expected_sequence}, got {pkt.sequence}"
            )

        # 3. Ledger recording if available
        if self._ledger is not None:
            self._ledger.append(
                event_type="handoff.imported",
                entity_id=pkt.packet_id,
                payload=pkt.to_dict(),
            )
            self._ledger.append(
                event_type="handoff.verified",
                entity_id=pkt.packet_id,
                payload={"verified_state_hash": pkt.state_hash, "valid": True},
            )


        transition = BecomingTransition(
            current_state="handoff_received",
            next_state="continued",
            action="continue_becoming",
            loop=True,
            reason=f"Handoff {pkt.packet_id} successfully imported from {pkt.source_repo} into {pkt.target_repo}",
            provenance=(pkt.source_repo, pkt.target_repo, pkt.packet_id),
            verification_hash=pkt.state_hash,
        )

        return {
            "valid": True,
            "packet_id": pkt.packet_id,
            "source_repo": pkt.source_repo,
            "target_repo": pkt.target_repo,
            "sequence": pkt.sequence,
            "state_hash": pkt.state_hash,
            "attestation_id": pkt.attestation_id,
            "transition": self._becoming_engine.to_dict(transition),
        }

    def verify_cycle(self, packets: list[HandoffPacket | dict[str, Any]]) -> dict[str, Any]:
        """Validate a continuous cross-repository handoff cycle (A → B → C → A → ∞)."""
        if not packets:
            return {"valid": False, "error": "No packets provided for cycle verification"}

        parsed_packets = [
            p if isinstance(p, HandoffPacket) else HandoffPacket.from_dict(p) for p in packets
        ]

        # Verify individual packet state hashes
        for i, pkt in enumerate(parsed_packets):
            if hash_json(pkt.payload) != pkt.state_hash:
                return {
                    "valid": False,
                    "error": f"Packet {i} ({pkt.packet_id}) has invalid state hash",
                }

        # Verify contiguous sequence and topology (target_repo of step i matches source_repo of step i+1)
        for i in range(len(parsed_packets) - 1):
            curr = parsed_packets[i]
            nxt = parsed_packets[i + 1]
            if curr.target_repo != nxt.source_repo:
                return {
                    "valid": False,
                    "error": f"Break in cycle sequence between step {i} ({curr.target_repo}) and step {i+1} ({nxt.source_repo})",
                }

        # Check cycle loop (last target matches first source if 2+ packets)
        is_loop = (
            len(parsed_packets) > 1 and parsed_packets[-1].target_repo == parsed_packets[0].source_repo
        )

        return {
            "valid": True,
            "packets_count": len(parsed_packets),
            "is_closed_loop": is_loop,
            "flow": " -> ".join([p.source_repo for p in parsed_packets] + [parsed_packets[-1].target_repo]),
            "head_packet_id": parsed_packets[-1].packet_id,
        }

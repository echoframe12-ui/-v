from __future__ import annotations

"""Autonomous Verification & Production Attestation Engine for Ω∞v OceanicOS.

Continuously audits event ledger hash integrity, attestation ledger hash integrity,
system drift posture, and continuous becoming state transitions.
Generates cryptographically sealed attestation proofs and records periodic checkpoint events.
"""

import hashlib
import hmac
import json
import os
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from attestation import AttestationEngine, checkpoint_signature
from continuous_becoming import ContinuousBecomingEngine
from drift_audit import DriftAuditLog
from mood_integrity import assess_perspectives
from oceanic_event_ledger import EventLedger
from perspectives import PerspectiveRegistry



class AutonomousAttestationEngine:
    """Background verification engine running periodic attestation cycles.

    Verifies state integrity across all system layers and emits sealed proof
    events into the EventLedger.
    """

    def __init__(
        self,
        db_path: str | Path | None = None,
        ledger_path: str | Path | None = None,
        secret_key: str | None = None,
    ) -> None:
        self.db_path = Path(db_path or os.getenv("OCEANICOS_DB", "oceanicos.db"))
        self.ledger_path = Path(
            ledger_path or os.getenv("OCEANICOS_EVENT_LEDGER", "oceanic_lifecycle.jsonl")
        )
        self.secret_key = secret_key or os.getenv("OCEANICOS_SECRET_KEY", "oceanicos-default-secret-key")

        self.event_ledger = EventLedger(self.ledger_path)
        self.attestation_ledger = AttestationEngine(db_path=self.db_path)
        self.drift_log = DriftAuditLog(db_path=str(self.db_path))
        self.becoming_engine = ContinuousBecomingEngine()


        self._lock = threading.Lock()
        self._daemon_thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._last_cycle_result: dict[str, Any] | None = None
        self._cycle_count = 0

    def run_verification_cycle(self) -> dict[str, Any]:
        """Execute a full verification cycle across all ledger and state layers."""
        with self._lock:
            timestamp = datetime.now(timezone.utc).isoformat()

            # 1. Event Ledger Chain Integrity
            event_ledger_valid = self.event_ledger.verify_chain()
            event_history = self.event_ledger.history()
            event_count = len(event_history)
            head_event_digest = event_history[-1].event_digest if event_history else "sha256:genesis"

            # 2. Attestation Ledger Chain Integrity
            att_verification = self.attestation_ledger.verify_chain()
            att_valid = att_verification.get("intact", False)
            att_length = att_verification.get("length", 0)
            att_head_hash = att_verification.get("head", "0" * 64)


            # 3. Drift Audit Record & History
            drift_record = self.drift_log.record(
                {"intact": event_ledger_valid, "trustworthy": att_valid, "length": att_length}
            )
            drift_history = self.drift_log.list(limit=5)


            # 4. MOOD Assessment over chain integrity & posture
            from mood import MoodSignal, assess

            signals = [
                MoodSignal("event_ledger_integrity", event_ledger_valid, "event_ledger"),
                MoodSignal("attestation_ledger_integrity", att_valid, "attestation_ledger"),
            ]
            mood_assessment = assess(signals)





            # 5. Determine Overall Posture
            all_valid = event_ledger_valid and att_valid and (mood_assessment.status == "clear")
            status = "clear" if all_valid else "dissent"

            # 6. Generate Checkpoint Signature
            proof_data = {
                "timestamp": timestamp,
                "cycle_number": self._cycle_count + 1,
                "status": status,
                "event_ledger": {
                    "valid": event_ledger_valid,
                    "count": event_count,
                    "head_digest": head_event_digest,
                },
                "attestation_ledger": {
                    "valid": att_valid,
                    "length": att_length,
                    "head_hash": att_head_hash,
                },
                "drift_record": drift_record,

                "mood_assessment": {
                    "status": mood_assessment.status,
                    "route": mood_assessment.route,
                    "gaps": mood_assessment.gaps,
                },
            }

            proof_canonical = json.dumps(proof_data, sort_keys=True, separators=(",", ":"))
            proof_signature = hmac.new(
                self.secret_key.encode("utf-8"), proof_canonical.encode("utf-8"), hashlib.sha256
            ).hexdigest()

            proof_packet = {
                "proof_id": f"proof-{int(time.time())}-{self._cycle_count + 1}",
                "data": proof_data,
                "signature": proof_signature,
            }

            # 7. Record to Event Ledger
            event_type = "attestation.daemon_verified" if all_valid else "attestation.daemon_dissent"
            self.event_ledger.append(event_type, proof_packet["proof_id"], proof_packet)

            # 8. Record to Attestation SQL Engine
            self.attestation_ledger.attest(
                subject=f"daemon-cycle-{self._cycle_count + 1}",
                content=proof_canonical,
                sources=["autonomous_attestation_engine"],
                confidence=1.0 if all_valid else 0.5,
                actor="attestation-daemon",
            )


            self._cycle_count += 1
            self._last_cycle_result = proof_packet
            return proof_packet

    def verify_proof(self, proof_packet: dict[str, Any], key: str | None = None) -> dict[str, Any]:
        """Verify an attestation proof packet offline using the secret key."""
        sec_key = key or self.secret_key
        data = proof_packet.get("data")
        sig = proof_packet.get("signature")

        if not data or not sig:
            return {"valid": False, "reason": "Missing data or signature in proof packet"}

        proof_canonical = json.dumps(data, sort_keys=True, separators=(",", ":"))
        expected_sig = hmac.new(
            sec_key.encode("utf-8"), proof_canonical.encode("utf-8"), hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(sig, expected_sig):
            return {"valid": False, "reason": "Signature mismatch"}

        # Check internal ledger flags
        el = data.get("event_ledger", {})
        al = data.get("attestation_ledger", {})
        mood = data.get("mood_assessment", {})

        is_intact = el.get("valid") and al.get("valid") and (mood.get("status") == "clear")

        return {
            "valid": True,
            "intact": is_intact,
            "proof_id": proof_packet.get("proof_id"),
            "timestamp": data.get("timestamp"),
            "status": data.get("status"),
        }

    def start_daemon(self, interval_seconds: int = 30) -> None:
        """Start the background daemon loop."""
        with self._lock:
            if self._daemon_thread and self._daemon_thread.is_alive():
                return

            self._stop_event.clear()

            def _loop():
                while not self._stop_event.is_set():
                    try:
                        self.run_verification_cycle()
                    except Exception as e:
                        # Log error silently into event ledger as dissent
                        self.event_ledger.append(
                            "attestation.daemon_error",
                            "daemon-error",
                            {"error": str(e), "timestamp": datetime.now(timezone.utc).isoformat()},
                        )
                    self._stop_event.wait(timeout=interval_seconds)

            self._daemon_thread = threading.Thread(target=_loop, daemon=True, name="AttestationDaemon")
            self._daemon_thread.start()

    def stop_daemon(self) -> None:
        """Stop the background daemon loop."""
        with self._lock:
            if self._stop_event:
                self._stop_event.set()
            if self._daemon_thread and self._daemon_thread.is_alive():
                self._daemon_thread.join(timeout=5)
            self._daemon_thread = None

    def get_daemon_status(self) -> dict[str, Any]:
        """Return the current daemon operational status."""
        with self._lock:
            is_running = self._daemon_thread is not None and self._daemon_thread.is_alive()
            return {
                "running": is_running,
                "cycle_count": self._cycle_count,
                "last_cycle": self._last_cycle_result,
            }

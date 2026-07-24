# 0083 — Offline Receipt CLI

## Context

Round 82 (`DECISIONS/0082`) made the per-item receipt independently verifiable as a
*function* — `verify_ledger.verify_receipt` recomputes an entry's own `link_hash`
instead of trusting its asserted `entry_intact` flag, and can bind a receipt to held
content by SHA-256 — and gave the client SDK a `verify_receipt` method. But the
`oceanic-os` CLI toolkit stayed asymmetric. It already had a `digest` command that
both *emits* a signed posture from the local ledger and *verifies* a digest file
(`--verify FILE`), yet the receipt — the proof most likely to be forwarded on its own
— had no command at all. An operator with just the ledger, or an auditor handed a
single receipt file, had no one-command way to produce or check it.

## Decision

Add `oceanic-os receipt`, giving the receipt the same emit/verify treatment as
`digest`.

- **Emit**: `oceanic-os receipt <id>` prints the receipt for that attestation from the
  configured ledger (the same document `/attestations/<id>/receipt` serves); a missing
  id reports it and exits non-zero.
- **Verify**: `oceanic-os receipt --verify FILE` (or `-` for stdin) runs the round-82
  `verify_ledger.verify_receipt`, printing a one-line summary (or `--json` for the full
  result). `--content-file PATH` binds the receipt to the original attested content.
  Exit `0` when the entry hash recomputes **and** any supplied content matches; `1`
  otherwise — the same VALID/INVALID exit contract as `digest`, so it doubles as a
  CI/cron receipt gate.

## Consequences

- The offline CLI toolkit is now symmetric and complete: `verify` (chain), `gate`
  (policy), `digest` (emit/verify the signed posture), `receipt` (emit/verify a single
  proof), and `report` (the human page) — every artifact the platform produces has a
  command that works from the local ledger or a handed-over file, with no service.
- Verified live and offline: emitting receipt #1 prints the receipt and exits 0;
  verifying it alone is `VALID` (exit 0); with the correct `--content-file` it is
  `VALID · content matches`; with the wrong content `INVALID · content MISMATCH`
  (exit 1); and a forged receipt whose subject was edited while it still claims
  `entry_intact: true` is caught as `INVALID · entry hash TAMPERED` (exit 1) — the
  recomputation overrides the lie, exactly as the underlying function does.
- The honest split from round 82 is preserved in the CLI's own words: the summary
  labels `entry hash intact` and content binding (which are *recomputed*) separately
  from the `[asserted]` chain and seal claims (which are *echoed*, since one receipt
  cannot prove them without the ledger). The command surfaces the assertions but never
  presents them as independently verified.
- Additive and offline-only: a new subcommand over existing pure functions
  (`AttestationEngine.receipt`, `verify_ledger.verify_receipt`) — no new endpoint, no
  server change, nothing existing altered.

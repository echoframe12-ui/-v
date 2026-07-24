# 0082 — Offline Receipt Verification

## Context

The platform hands out three verifiable artifacts, and a recipient could
independently check two of them without trusting the platform's own word: the
signed status **digest** (`verify_digest`, client `verify_digest`) and the exported
**bundle** (`verify_ledger`, the online twin). The third — the per-item **receipt**,
the proof a client presents for a single attestation — could only be *read*. Its
`entry_intact` and `chain_intact` fields were the platform's assertions about the
record, and a holder had no way to recompute them. A receipt is exactly the artifact
most likely to be forwarded on its own ("here is proof we verified this output"), and
it was the one artifact whose claims the recipient had to take on faith.

## Decision

Add independent, offline receipt verification — recompute, don't trust.

- `verify_ledger.verify_receipt(receipt, content=None)` (pure over the receipt)
  recomputes the entry's own `link_hash(prev_hash, entry)` and confirms it equals
  the receipt's stored `entry_hash` (`entry_hash_valid`) — proving the entry's
  content and prev-linkage are self-consistent, using the very function the ledger
  hashes entries with. Given the original `content`, it also binds the receipt to it
  by recomputing the SHA-256 (`content_matches`).
- The receipt's chain-wide claims (`entry_intact`, `chain_intact`, `sealed`) are
  returned under `asserted` — echoed, not re-derived, because proving them needs the
  full ledger, not one receipt. Naming them `asserted` keeps the honesty explicit: a
  caller cannot mistake an echo for an independent check.
- `OceanicOSClient.verify_receipt(att_id, content=None)` fetches the receipt and
  verifies it through the same `verify_ledger.verify_receipt`, completing the
  recipient trilogy (digest, bundle, receipt) with one client call and no drift from
  the ledger's hashing.

## Consequences

- The receipt is now as trustworthy as the record it proves: verified live, a
  genuine receipt recomputes to `entry_hash_valid: true`; binding to the original
  content is `true` and to any other content `false`; and a receipt whose content
  was edited while it still *claims* `entry_intact: true` is caught —
  `entry_hash_valid: false` even though the asserted flag preserves the lie. The
  claim can no longer outrun the math.
- The recipient story is complete across every artifact: whatever the platform hands
  out — a signed posture, a whole record, or a single receipt — the party holding it
  can confirm it offline, from the artifact alone, using the platform's own hashing
  and signing functions. Trust is portable to the item level.
- Honest about the limits of one receipt: entry integrity and content binding are
  *recomputed*; the chain-wide and seal claims are *echoed* as `asserted`, because a
  single receipt cannot prove them without the ledger. The function verifies exactly
  what it can and labels the rest, rather than dressing an assertion as a proof.
- Additive and drift-proof: a new pure function beside `verify_digest`/`verify_bundle`
  and one client method that delegates to it. No endpoint, no server change, and the
  client checks an entry exactly the way the engine builds one — the same anti-drift
  discipline as client-side digest verification.

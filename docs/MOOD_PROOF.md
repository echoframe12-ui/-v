# MOOD Proof Capture

Use the GitHub Actions run for `Full Stack MOOD` as the authoritative proof source.

## Required green checks

1. Full test suite
2. Live full-stack MOOD verification
3. Container build

A screenshot should be captured from the successful Actions run log showing:

```text
OceanicOS full-stack verification
deployment         PASS
smoke              PASS
status_endpoint    PASS
request_id         PASS
integrity          PASS
MOOD               CLEAR
ROUTE              continue
VERIFIED           YES
```

Do not label a screenshot as proof unless these checks actually passed in CI.

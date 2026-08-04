# Full Stack MOOD CI Execution Gate

This repository contains a real end-to-end verification workflow at `.github/workflows/full-stack-mood.yml`.

The workflow intentionally does not report success from application code alone. A green release requires GitHub Actions to execute:

1. `make test`
2. `make verify`
3. `make docker-build`
4. publish `mood-verification.txt` as the `mood-verification-proof` artifact

## If no run appears

Check **Settings → Actions → General** and ensure Actions are allowed for the repository. If contributor approval is enabled, approve the pending workflow run. The workflow also supports `workflow_dispatch`, so it can be started manually from the Actions UI.

## Evidence rule

`make verify` exits non-zero unless all runtime evidence checks pass and MOOD is `clear`. Therefore a green workflow is the authoritative CI proof; screenshots are presentation evidence only.

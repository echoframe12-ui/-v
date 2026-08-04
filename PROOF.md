# Full-Stack MOOD Proof

Run:

```bash
make test
make verify
make docker-build
```

Expected verification contract:

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

The proof is valid only when produced by the repository's CI workflow `Full Stack MOOD`; this file is a contract, not a substitute for CI evidence.

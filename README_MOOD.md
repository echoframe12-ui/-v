# MOOD Full-Stack Verification

MOOD is integrated into the OceanicOS verification path.

```text
application
  -> deployment contract
  -> production smoke
  -> final E2E integrity
  -> MOOD assessment
  -> VERIFIED / HUMAN
```

The canonical local proof command is `make verify`.
The CI proof runs the full test suite, live verification, and container build.

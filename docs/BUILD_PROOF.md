# Build Proof

The repository's authoritative proof sequence is:

```text
make test
  -> make verify
  -> make docker-build
```

The `Full Stack MOOD` GitHub Actions workflow runs the same sequence in CI.

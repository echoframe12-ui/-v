# Tests

Integration and end-to-end tests for the Ω∞v Oceanicos system.

## Structure

- **integration/** — Full system integration tests
- **e2e/** — End-to-end user flow tests
- **fixtures/** — Test data and mocks

## Running Tests

```bash
# Run all tests
npm run test

# Run integration tests only
npm run test:integration

# Run with coverage
npm run test:coverage

# Watch mode
npm run test:watch
```

## Test Philosophy

Every test verifies:

1. **Correctness** — Does the code do what it's supposed to?
2. **Evidence** — Can we prove it works?
3. **Regression** — Does it still work after changes?
4. **Specification** — Does it match the design?

### Integration Test Template

```typescript
describe('Verification Loop', () => {
  it('should observe, verify, attest, and record', async () => {
    // Arrange
    const observation = {
      claim: 'Service is healthy',
      source: 'health-check',
      timestamp: new Date().toISOString(),
      confidence: 0.95,
    };

    // Act
    const result = await verificationLoop.execute(observation);

    // Assert
    expect(result.verified).toBe(true);
    expect(result.attestation).toBeDefined();
    expect(result.recordedId).toBeDefined();
  });
});
```

---

See [../../CONTRIBUTING.md](../../CONTRIBUTING.md) for test requirements.

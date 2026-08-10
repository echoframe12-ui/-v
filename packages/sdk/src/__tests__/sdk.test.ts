import { OceanicosClient } from '../index';

describe('OceanicosClient (SDK)', () => {
  it('should run full loop in local embedded mode', async () => {
    const client = new OceanicosClient({ mode: 'local' });

    const result = await client.runLoop({
      claim: 'Service gateway response time under limit',
      category: 'health-check',
      metadata: { statusCode: 200, responseTime: 35 },
    });

    expect(result.observation).toBeDefined();
    expect(result.verification.summary.passed).toBe(true);
    expect(result.attestation.verified).toBe(true);
    expect(result.attestation.signature).toMatch(/^0x/);

    expect(client.getLogEntries()).toHaveLength(3);
    expect(client.verifyIntegrity().valid).toBe(true);
  });

  it('should compute metrics correctly through SDK', async () => {
    const client = new OceanicosClient();
    await client.runLoop({ claim: 'Claim 1' });
    await client.runLoop({ claim: 'Claim 2' });

    const metrics = client.getMetrics();
    expect(metrics.totalObservations).toBe(2);
    expect(metrics.totalAttestations).toBe(2);
  });
});

import { AttestationService } from '../index';
import { VerificationResult } from '@omega-v/types';

describe('AttestationService', () => {
  let service: AttestationService;

  beforeEach(() => {
    service = new AttestationService('test-secret-key-v1', '1');
  });

  it('should generate a valid signed attestation from verification result', () => {
    const verificationResult: VerificationResult = {
      id: 'ver-test-1',
      observationId: 'obs-test-1',
      timestamp: new Date().toISOString(),
      summary: {
        passed: true,
        confidence: 0.95,
        rulesApplied: 2,
        rulesPassed: 2,
        rulesFailed: 0,
      },
      rules: [
        { name: 'response-time-threshold', passed: true, confidence: 0.95 },
        { name: 'status-code-check', passed: true, confidence: 0.98 },
      ],
      evidencePath: [],
      ruleVersions: { 'response-time-threshold': '1.0.5', 'status-code-check': '1.2.0' },
      status: 'completed',
    };

    const attestation = service.attest(verificationResult, {
      attestedBy: 'test-attestor',
    });

    expect(attestation).toBeDefined();
    expect(attestation.id).toMatch(/^att-/);
    expect(attestation.verified).toBe(true);
    expect(attestation.signature).toMatch(/^0x/);
    expect(attestation.status).toBe('signed');

    const isVerified = service.verify(attestation);
    expect(isVerified).toBe(true);
  });
});

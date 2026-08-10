import { VerificationEngine } from '../index';
import { Observation } from '@omega-v/types';

describe('VerificationEngine', () => {
  let engine: VerificationEngine;

  beforeEach(() => {
    engine = new VerificationEngine(1000);
    engine.registerRule({
      name: 'response-time-threshold',
      version: '1.0.5',
      appliesTo: ['health-check'],
      definition: 'responseTime < 100',
      description: 'Verify response time is below 100ms',
      createdAt: new Date().toISOString(),
      active: true,
    });
    engine.registerRule({
      name: 'status-code-check',
      version: '1.2.0',
      appliesTo: ['health-check'],
      definition: 'statusCode == 200',
      description: 'Verify HTTP status code is 200 OK',
      createdAt: new Date().toISOString(),
      active: true,
    });
  });

  it('should verify passing observation with evidence path', () => {
    const observation: Observation = {
      id: 'obs-test-1',
      claim: { statement: 'Service is fast', category: 'health-check' },
      source: { system: 'api', version: '1.0.0', environment: 'production' },
      timestamp: new Date().toISOString(),
      observedBy: 'monitor',
      metadata: { responseTime: 45, statusCode: 200 },
      confidence: 0.95,
      confidenceReason: 'Clean test run',
      status: 'normalized',
    };

    const result = engine.verify(observation);
    expect(result.summary.passed).toBe(true);
    expect(result.summary.rulesPassed).toBe(2);
    expect(result.evidencePath).toHaveLength(2);
    expect(result.evidencePath[0].passed).toBe(true);
  });

  it('should detect failing rule thresholds', () => {
    const observation: Observation = {
      id: 'obs-test-2',
      claim: { statement: 'Service is degraded', category: 'health-check' },
      source: { system: 'api', version: '1.0.0', environment: 'production' },
      timestamp: new Date().toISOString(),
      observedBy: 'monitor',
      metadata: { responseTime: 250, statusCode: 500 },
      confidence: 0.95,
      confidenceReason: 'Degraded run',
      status: 'normalized',
    };

    const result = engine.verify(observation);
    expect(result.summary.passed).toBe(false);
    expect(result.summary.rulesFailed).toBe(2);
  });
});

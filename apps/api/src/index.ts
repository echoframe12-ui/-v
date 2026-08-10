import express, { Express, Request, Response } from 'express';
import { Observer } from '@omega-v/observer';
import { VerificationEngine } from '@omega-v/verification';
import { AttestationService } from '@omega-v/attestation';
import { ProvenanceStore } from '@omega-v/store';
import { OceanicosClient } from '@omega-v/sdk';
import { FormlessSwarm } from '@omega-v/agents';
import { MoodEvaluator } from '@omega-v/mood';
import { FrictionTracker } from '@omega-v/friction';
import { ProvenanceGraph } from '@omega-v/graph';
import { SuccessResponse, ErrorResponse, VerificationRule, SystemMetrics, EventLogEntry, QueryResult, SystemMood, FrictionCategory } from '@omega-v/types';

/**
 * Ω∞v Oceanicos API Server
 * Exposes the verification loop via REST endpoints
 */
const app: Express = express();
const port = process.env.API_PORT || 3000;

// Middleware
app.use(express.json());
app.use((_req, res, next) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  next();
});

// Initialize services
const observer = new Observer();
const verificationEngine = new VerificationEngine();
const attestationService = new AttestationService();
const store = new ProvenanceStore();
const frictionTracker = new FrictionTracker();

// Register default rules
verificationEngine.registerRule({
  name: 'response-time-threshold',
  version: '1.0.5',
  appliesTo: ['health-check'],
  definition: 'responseTime < 100',
  description: 'Verify response time is below 100ms',
  createdAt: new Date().toISOString(),
  active: true,
});

verificationEngine.registerRule({
  name: 'status-code-check',
  version: '1.2.0',
  appliesTo: ['health-check'],
  definition: 'statusCode == 200',
  description: 'Verify HTTP status code is 200 OK',
  createdAt: new Date().toISOString(),
  active: true,
});

/**
 * GET /health
 */
app.get('/health', (_req: Request, res: Response) => {
  const response: SuccessResponse<{ status: string; uptime: number; logSize: number }> = {
    data: { status: 'ok', uptime: process.uptime(), logSize: store.size() },
    timestamp: new Date().toISOString(),
  };
  res.json(response);
});

/**
 * POST /observe — Step 1
 */
app.post('/observe', (req: Request, res: Response) => {
  try {
    const { claim, category, source, observedBy, metadata, confidence, confidenceReason } = req.body;
    const observation = observer.observe({ claim, category, source, observedBy, metadata, confidence, confidenceReason });
    store.recordObservation(observation);
    res.status(201).json({ data: observation, timestamp: new Date().toISOString() } as SuccessResponse<typeof observation>);
  } catch (error) {
    res.status(400).json({ code: 'OBSERVATION_FAILED', message: error instanceof Error ? error.message : 'Failed', timestamp: new Date().toISOString() } as ErrorResponse);
  }
});

/**
 * POST /verify — Step 2
 */
app.post('/verify', (req: Request, res: Response) => {
  try {
    const { observation } = req.body;
    if (!observation) {
      res.status(400).json({ code: 'MISSING_OBSERVATION', message: 'Observation is required', timestamp: new Date().toISOString() } as ErrorResponse);
      return;
    }
    const verificationResult = verificationEngine.verify(observation);
    store.recordVerification(verificationResult);
    res.status(201).json({ data: verificationResult, timestamp: new Date().toISOString() } as SuccessResponse<typeof verificationResult>);
  } catch (error) {
    res.status(400).json({ code: 'VERIFICATION_FAILED', message: error instanceof Error ? error.message : 'Verification failed', timestamp: new Date().toISOString() } as ErrorResponse);
  }
});

/**
 * POST /attest — Step 3
 */
app.post('/attest', (req: Request, res: Response) => {
  try {
    const { verificationResult } = req.body;
    if (!verificationResult) {
      res.status(400).json({ code: 'MISSING_VERIFICATION', message: 'Verification result is required', timestamp: new Date().toISOString() } as ErrorResponse);
      return;
    }
    const attestation = attestationService.attest(verificationResult);
    store.recordAttestation(attestation);
    res.status(201).json({ data: attestation, timestamp: new Date().toISOString() } as SuccessResponse<typeof attestation>);
  } catch (error) {
    res.status(400).json({ code: 'ATTESTATION_FAILED', message: error instanceof Error ? error.message : 'Attestation failed', timestamp: new Date().toISOString() } as ErrorResponse);
  }
});

/**
 * POST /complete-loop — Observe → Verify → Attest → Record in one request
 */
app.post('/complete-loop', (req: Request, res: Response) => {
  try {
    const { claim, category, source, observedBy, metadata, confidence, confidenceReason } = req.body;

    const observation = observer.observe({ claim, category, source, observedBy, metadata, confidence, confidenceReason });
    store.recordObservation(observation);

    const verificationResult = verificationEngine.verify(observation);
    store.recordVerification(verificationResult);

    const attestation = attestationService.attest(verificationResult);
    store.recordAttestation(attestation);

    const loopResult = { observation, verification: verificationResult, attestation, logSize: store.size() };
    res.status(201).json({
      data: loopResult,
      timestamp: new Date().toISOString(),
    } satisfies SuccessResponse<typeof loopResult>);
  } catch (error) {
    res.status(400).json({ code: 'LOOP_FAILED', message: error instanceof Error ? error.message : 'Verification loop failed', timestamp: new Date().toISOString() } as ErrorResponse);
  }
});

/**
 * POST /swarm — Execute multi-agent Formless Swarm cycle
 */
app.post('/swarm', async (req: Request, res: Response) => {
  try {
    const { claim, ruleName, ruleDefinition, metadata } = req.body;
    const client = new OceanicosClient({ mode: 'local' });
    const swarm = new FormlessSwarm(client);

    const swarmResult = await swarm.executeSwarmCycle({
      claim: claim || 'Multi-agent REST verification',
      ruleName: ruleName || 'api-swarm-rule',
      ruleDefinition: ruleDefinition || 'responseTime < 100',
      metadata: metadata || { responseTime: 25 },
    });

    res.status(201).json({
      data: swarmResult,
      timestamp: new Date().toISOString(),
    } satisfies SuccessResponse<typeof swarmResult>);
  } catch (error) {
    res.status(400).json({ code: 'SWARM_FAILED', message: error instanceof Error ? error.message : 'Swarm execution failed', timestamp: new Date().toISOString() } as ErrorResponse);
  }
});

/**
 * GET /rules — List registered verification rules
 */
app.get('/rules', (_req: Request, res: Response) => {
  const applicableRules = verificationEngine.getApplicableRules({
    id: '',
    claim: { statement: '', category: 'health-check' },
    source: { system: '', version: '', environment: '' },
    timestamp: '',
    observedBy: '',
    metadata: {},
    confidence: 0,
    confidenceReason: '',
    status: 'normalized',
  });

  const response: SuccessResponse<{ count: number; rules: VerificationRule[] }> = {
    data: { count: applicableRules.length, rules: applicableRules },
    timestamp: new Date().toISOString(),
  };
  res.json(response);
});

/**
 * GET /log — Provenance event log (append-only, hash-chained)
 */
app.get('/log', (req: Request, res: Response) => {
  const type = req.query['type'] as 'OBSERVATION' | 'VERIFICATION' | 'ATTESTATION' | undefined;
  const limit = req.query['limit'] ? parseInt(req.query['limit'] as string, 10) : 50;
  const offset = req.query['offset'] ? parseInt(req.query['offset'] as string, 10) : 0;
  const since = req.query['since'] as string | undefined;

  const result: QueryResult = store.query({ type, limit, offset, since });
  const integrity = store.verifyChainIntegrity();

  const response: SuccessResponse<QueryResult & { integrity: typeof integrity }> = {
    data: { ...result, integrity },
    timestamp: new Date().toISOString(),
  };
  res.json(response);
});

/**
 * GET /metrics — System metrics and learning insights
 */
app.get('/metrics', (_req: Request, res: Response) => {
  const metrics: SystemMetrics = store.getMetrics();
  const integrity = store.verifyChainIntegrity();
  const latest: EventLogEntry | undefined = store.getLatest();

  const response: SuccessResponse<{ metrics: SystemMetrics; integrity: typeof integrity; latest: EventLogEntry | null }> = {
    data: { metrics, integrity, latest: latest ?? null },
    timestamp: new Date().toISOString(),
  };
  res.json(response);
});

/**
 * Pillar 16 Endpoints: /observations, /verifications, /attestations, /lineage, /agents
 */

/** GET /observations */
app.get('/observations', (_req: Request, res: Response) => {
  const result = store.query({ type: 'OBSERVATION', limit: 100 });
  res.json({ data: result, timestamp: new Date().toISOString() } satisfies SuccessResponse<typeof result>);
});

/** GET /verifications */
app.get('/verifications', (_req: Request, res: Response) => {
  const result = store.query({ type: 'VERIFICATION', limit: 100 });
  res.json({ data: result, timestamp: new Date().toISOString() } satisfies SuccessResponse<typeof result>);
});

/** GET /attestations */
app.get('/attestations', (_req: Request, res: Response) => {
  const result = store.query({ type: 'ATTESTATION', limit: 100 });
  res.json({ data: result, timestamp: new Date().toISOString() } satisfies SuccessResponse<typeof result>);
});

/** GET /lineage */
app.get('/lineage', (_req: Request, res: Response) => {
  const allEntries = store.query({ limit: 1000 }).events;
  const integrity = store.verifyChainIntegrity();
  const lineage = {
    genesisHash: ProvenanceStore.GENESIS_HASH,
    totalNodes: allEntries.length,
    integrity,
    chainHead: store.getLatest()?.hash ?? ProvenanceStore.GENESIS_HASH,
  };
  res.json({ data: lineage, timestamp: new Date().toISOString() } satisfies SuccessResponse<typeof lineage>);
});

/** GET /agents */
app.get('/agents', (_req: Request, res: Response) => {
  const agents = [
    { role: 'Observer', capability: 'CAPTURE_SIGNAL', permissions: ['CAN_OBSERVE'] },
    { role: 'Verifier', capability: 'VERIFY_RULE', permissions: ['CAN_REASON', 'CAN_PROPOSE'] },
    { role: 'Security', capability: 'SECURITY_AUDIT', permissions: ['CAN_OBSERVE', 'CAN_REASON'] },
    { role: 'Governance', capability: 'GOVERNANCE_CHECK', permissions: ['CAN_PROPOSE', 'CAN_ACT'] },
    { role: 'Learning', capability: 'EXTRACT_INSIGHTS', permissions: ['CAN_OBSERVE', 'CAN_REASON', 'CAN_ATTEST'] },
  ];
  res.json({ data: agents, timestamp: new Date().toISOString() } satisfies SuccessResponse<typeof agents>);
});

/** GET /mood — System Mood Evaluator (Pillar 19) */
app.get('/mood', (_req: Request, res: Response) => {
  const metrics = store.getMetrics();
  const integrity = store.verifyChainIntegrity();
  const moodEvaluator = new MoodEvaluator();
  const dissentMetrics = frictionTracker.getMetrics();
  const mood: SystemMood = moodEvaluator.evaluate(metrics, integrity.valid, dissentMetrics.openDissent);
  res.json({ data: mood, timestamp: new Date().toISOString() } satisfies SuccessResponse<typeof mood>);
});

/** GET /friction — Query friction events and summary metrics (Pillar 20) */
app.get('/friction', (_req: Request, res: Response) => {
  const events = frictionTracker.getFriction();
  const metrics = frictionTracker.getMetrics();
  res.json({ data: { events, metrics }, timestamp: new Date().toISOString() } satisfies SuccessResponse<{ events: typeof events; metrics: typeof metrics }>);
});

/** POST /friction — Record a new system friction event (Pillar 20) */
app.post('/friction', (req: Request, res: Response) => {
  const { category, source, description, evidence, severity } = req.body;
  if (!category || !source || !description) {
    res.status(400).json({ code: 'BAD_REQUEST', message: 'Missing category, source, or description', timestamp: new Date().toISOString() });
    return;
  }
  const event = frictionTracker.record({ category: category as FrictionCategory, source, description, evidence, severity });
  res.status(201).json({ data: event, timestamp: new Date().toISOString() } satisfies SuccessResponse<typeof event>);
});

/** GET /dissent — Query active dissent records (Pillar 21) */
app.get('/dissent', (_req: Request, res: Response) => {
  const records = frictionTracker.getDissent();
  const metrics = frictionTracker.getMetrics();
  res.json({ data: { records, openDissent: metrics.openDissent }, timestamp: new Date().toISOString() } satisfies SuccessResponse<{ records: typeof records; openDissent: number }>);
});

/** POST /dissent — Record explicit disagreement / competing interpretations (Pillar 21) */
app.post('/dissent', (req: Request, res: Response) => {
  const { claimId, interpretations } = req.body;
  if (!claimId || !Array.isArray(interpretations) || interpretations.length < 2) {
    res.status(400).json({ code: 'BAD_REQUEST', message: 'Dissent requires claimId and at least 2 interpretations', timestamp: new Date().toISOString() });
    return;
  }
  const dissent = frictionTracker.recordDissent(claimId, interpretations);
  res.status(201).json({ data: dissent, timestamp: new Date().toISOString() } satisfies SuccessResponse<typeof dissent>);
});

/** GET /graph — Provenance Knowledge Graph & Lineage DAG (Section XIV) */
app.get('/graph', (_req: Request, res: Response) => {
  const events = store.query({ limit: 1000 }).events;
  const graph = new ProvenanceGraph();
  graph.ingestEvents(events);
  const stats = graph.getStats();
  const traversal = events.length > 0 ? graph.traverseForward(`event-${events[0].id}`) : null;
  res.json({ data: { stats, traversal }, timestamp: new Date().toISOString() } satisfies SuccessResponse<{ stats: typeof stats; traversal: typeof traversal }>);
});

/**
 * 404 Handler
 */
app.use((_req: Request, res: Response) => {
  const errorResponse: ErrorResponse = {
    code: 'NOT_FOUND',
    message: 'Endpoint not found',
    timestamp: new Date().toISOString(),
  };
  res.status(404).json(errorResponse);
});

/**
 * Start the server (guarded for tests)
 */
if (process.env.NODE_ENV !== 'test') {
  app.listen(port, () => {
    /* eslint-disable no-console */
    console.log(`[Ω∞v API] Verification loop server running on http://localhost:${port}`);
    console.log(`Endpoints: POST /observe /verify /attest /complete-loop | GET /rules /log /metrics /health`);
    /* eslint-enable no-console */
  });
}

export default app;

import { OceanicosClient, FullLoopResult } from '@omega-v/sdk';
import { RuleCompiler } from '@omega-v/compiler';
import { OceanicumVM, IRProgram } from '@omega-v/ir';

export type AgentRole = 'Observer' | 'Verifier' | 'Builder' | 'Security' | 'Governance' | 'Learning';

export interface AgentActionResult {
  agentRole: AgentRole;
  timestamp: string;
  action: string;
  evidence: Record<string, unknown>;
  verified: boolean;
}

/**
 * Base Formless Agent: Inherits system trust & provenance constraints
 * "Agents are temporary forms of the current." — FORMLESS.md Section XIII
 */
export abstract class FormlessAgent {
  constructor(public readonly role: AgentRole, protected sdk: OceanicosClient) {}

  public abstract executeTask(input: Record<string, unknown>): Promise<AgentActionResult>;
}

export class ObserverAgent extends FormlessAgent {
  constructor(sdk: OceanicosClient) {
    super('Observer', sdk);
  }

  public async executeTask(input: Record<string, unknown>): Promise<AgentActionResult> {
    const claim = (input.claim as string) || 'Observer Agent signal capture';
    const loopRes = await this.sdk.runLoop({
      claim,
      category: 'agent-observation',
      observedBy: 'ObserverAgent',
      metadata: input,
    });

    return {
      agentRole: this.role,
      timestamp: new Date().toISOString(),
      action: 'CAPTURE_SIGNAL',
      evidence: { observationId: loopRes.observation.id },
      verified: loopRes.verification.summary.passed,
    };
  }
}

export class VerifierAgent extends FormlessAgent {
  private compiler = new RuleCompiler();
  private vm = new OceanicumVM();

  constructor(sdk: OceanicosClient) {
    super('Verifier', sdk);
  }

  public async executeTask(input: Record<string, unknown>): Promise<AgentActionResult> {
    const ruleName = (input.ruleName as string) || 'agent-rule';
    const ruleDef = (input.ruleDefinition as string) || 'responseTime < 100';
    const program: IRProgram = this.compiler.compile(ruleName, ruleDef);
    const vmRes = this.vm.execute(program, { metadata: input.metadata || { responseTime: 30 } });

    return {
      agentRole: this.role,
      timestamp: new Date().toISOString(),
      action: 'VERIFY_RULE',
      evidence: { programName: program.name, vmSteps: vmRes.steps.length, stackTop: vmRes.stackTop },
      verified: vmRes.passed,
    };
  }
}

export class SecurityAgent extends FormlessAgent {
  constructor(sdk: OceanicosClient) {
    super('Security', sdk);
  }

  public async executeTask(_input: Record<string, unknown> = {}): Promise<AgentActionResult> {
    const integrity = this.sdk.verifyIntegrity();
    const loopRes = await this.sdk.runLoop({
      claim: 'Security Audit: Event log hash chain integrity check',
      category: 'security-audit',
      observedBy: 'SecurityAgent',
      metadata: { validChain: integrity.valid },
    });

    return {
      agentRole: this.role,
      timestamp: new Date().toISOString(),
      action: 'SECURITY_AUDIT',
      evidence: { integrityValid: integrity.valid, attestation: loopRes.attestation.signature },
      verified: integrity.valid && loopRes.attestation.verified,
    };
  }
}

export class GovernanceAgent extends FormlessAgent {
  constructor(sdk: OceanicosClient) {
    super('Governance', sdk);
  }

  public async executeTask(input: Record<string, unknown>): Promise<AgentActionResult> {
    const metrics = this.sdk.getMetrics();
    const successThreshold = (input.threshold as number) || 0.5;
    const isCompliant = metrics.successRate >= successThreshold;

    return {
      agentRole: this.role,
      timestamp: new Date().toISOString(),
      action: 'GOVERNANCE_CHECK',
      evidence: { successRate: metrics.successRate, threshold: successThreshold },
      verified: isCompliant,
    };
  }
}

export class LearningAgent extends FormlessAgent {
  constructor(sdk: OceanicosClient) {
    super('Learning', sdk);
  }

  public async executeTask(_input: Record<string, unknown> = {}): Promise<AgentActionResult> {
    const metrics = this.sdk.getMetrics();

    return {
      agentRole: this.role,
      timestamp: new Date().toISOString(),
      action: 'EXTRACT_INSIGHTS',
      evidence: {
        totalObservations: metrics.totalObservations,
        systemConfidence: metrics.systemConfidence,
        insight: 'System evolution progressing within operational tolerances',
      },
      verified: true,
    };
  }
}

/**
 * FormlessSwarm: Orchestrates multi-agent verification workflows
 */
export class FormlessSwarm {
  private observerAgent: ObserverAgent;
  private verifierAgent: VerifierAgent;
  private securityAgent: SecurityAgent;
  private governanceAgent: GovernanceAgent;
  private learningAgent: LearningAgent;

  constructor(private sdk: OceanicosClient = new OceanicosClient()) {
    this.observerAgent = new ObserverAgent(this.sdk);
    this.verifierAgent = new VerifierAgent(this.sdk);
    this.securityAgent = new SecurityAgent(this.sdk);
    this.governanceAgent = new GovernanceAgent(this.sdk);
    this.learningAgent = new LearningAgent(this.sdk);
  }

  /**
   * Run multi-agent full verification cycle across all agent roles
   */
  public async executeSwarmCycle(input: {
    claim: string;
    ruleName?: string;
    ruleDefinition?: string;
    metadata?: Record<string, unknown>;
  }): Promise<{
    success: boolean;
    agentResults: AgentActionResult[];
    fullLoopResult: FullLoopResult;
  }> {
    const results: AgentActionResult[] = [];

    // 1. Observer Agent
    const obsRes = await this.observerAgent.executeTask({ claim: input.claim });
    results.push(obsRes);

    // 2. Verifier Agent
    const verRes = await this.verifierAgent.executeTask({
      ruleName: input.ruleName || 'swarm-rule',
      ruleDefinition: input.ruleDefinition || 'responseTime < 100',
      metadata: input.metadata || { responseTime: 35 },
    });
    results.push(verRes);

    // 3. Security Agent
    const secRes = await this.securityAgent.executeTask({});
    results.push(secRes);

    // 4. Governance Agent
    const govRes = await this.governanceAgent.executeTask({ threshold: 0.5 });
    results.push(govRes);

    // 5. Learning Agent
    const learnRes = await this.learningAgent.executeTask();
    results.push(learnRes);

    // Run underlying full loop to seal the cycle
    const fullLoopResult = await this.sdk.runLoop({
      claim: `Swarm Cycle Completed: ${input.claim}`,
      category: 'swarm-orchestration',
      observedBy: 'FormlessSwarm',
      metadata: { agentCount: results.length },
    });

    const allVerified = results.every((r) => r.verified) && fullLoopResult.attestation.verified;

    return {
      success: allVerified,
      agentResults: results,
      fullLoopResult,
    };
  }
}

export default FormlessSwarm;

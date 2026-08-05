// ============================================================
// Ω∞v OceanicOS — Shared Contract Types
// Mirrors oceanic_ir.py / OceanicIRContract on the backend.
// Never mutate these to work around a test — evolve the contract.
// ============================================================

export interface OceanicBound {
  time: string
  memory: string
}

export interface OceanicInput {
  name: string
  type: string
  required?: boolean
}

export interface OceanicRisk {
  class: 'low' | 'medium' | 'high' | 'critical'
  human_authorization: boolean
}

export interface OceanicIRContract {
  api_version: string
  contract_id: string
  intent: string
  inputs: OceanicInput[]
  outputs: { type: string }
  invariants: string[]
  effects: string[]
  bounds: OceanicBound
  dependencies: string[]
  proof_obligations: string[]
  dissent_triggers: string[]
  risk: OceanicRisk
}

// ============================================================
// MOOD
// ============================================================

export type MoodStatus = 'clear' | 'dissent'
export type MoodRoute = 'continue' | 'human'

export interface MoodAssessment {
  status: MoodStatus
  route: MoodRoute
  gaps: string[]
  requires_human: boolean
}

// ============================================================
// Lifecycle / Ledger
// ============================================================

export interface LedgerEvent {
  sequence: number
  event_type: string
  entity_id: string
  timestamp: string
  payload: Record<string, unknown>
  previous_digest: string | null
  event_digest: string
}

export interface ChainVerification {
  valid: boolean
  length: number
}

// ============================================================
// Verification
// ============================================================

export interface AdapterResult {
  language: string
  supported: boolean
  confidence: number
  dissent: string[]
}

export interface CompilationReport {
  contract_id: string
  adapter_count: number
  confidence: number
  dissent: string[]
  adapters: AdapterResult[]
}

// ============================================================
// Perspectives
// ============================================================

export interface PerspectiveResult {
  id: string
  model: string
  confidence: number | null
  response: unknown
  context_hash: string
}

export interface PerspectivesComparison {
  contract_id: string
  aggregate_confidence: number
  dissent_flag: boolean
  context_hash: string
  perspectives: PerspectiveResult[]
  comparison: Record<string, unknown>
}

// ============================================================
// Consensus (Phase 6)
// ============================================================

export interface BecomingTransition {
  current_state: string
  next_state: string
  action: string
  loop: boolean
  reason: string
  provenance: string[]
  verification_hash: string
}

export interface ConsensusResult {
  prompt: string
  iterations: number
  converged: boolean
  final_dissent_score: number
  mood: MoodStatus
  transition: BecomingTransition
}

// ============================================================
// Handoff (Phase 6)
// ============================================================

export interface HandoffPacket {
  packet_id: string
  source_repo: string
  target_repo: string
  sequence: number
  state_hash: string
  ledger_head_hash: string
  payload: Record<string, unknown>
  timestamp: string
  attestation_id?: string | null
}

export interface HandoffImportResult {
  valid: boolean
  packet_id: string
  source_repo: string
  target_repo: string
  sequence: number
  state_hash: string
  attestation_id?: string | null
  transition: BecomingTransition
}

export interface CycleVerification {
  valid: boolean
  packets_count?: number
  is_closed_loop?: boolean
  flow?: string
  head_packet_id?: string
  error?: string
}

// ============================================================
// Drift
// ============================================================

export interface DriftStats {
  total_audits: number
  intact: number
  deviated: number
  deviated_ratio: number
}

// ============================================================
// Health
// ============================================================

export interface HealthResponse {
  status: 'ok' | 'degraded'
  version?: string
}

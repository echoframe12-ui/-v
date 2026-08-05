// ============================================================
// Ω∞v OceanicOS — Typed API Client
// All calls proxy through Vite dev server → Flask backend.
// ============================================================

import type {
  HealthResponse,
  OceanicIRContract,
  CompilationReport,
  PerspectivesComparison,
  LedgerEvent,
  ChainVerification,
  ConsensusResult,
  HandoffPacket,
  HandoffImportResult,
  CycleVerification,
  DriftStats,
} from '../contracts/oceanic'

const BASE = ''

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: res.statusText }))
    throw new Error(err.error || `API ${res.status}`)
  }
  return res.json()
}

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`)
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: res.statusText }))
    throw new Error(err.error || `API ${res.status}`)
  }
  return res.json()
}

// ---- Health ----
export const getHealth = () => get<HealthResponse>('/status')

// ---- Contracts ----
export const validateContract = (contract: OceanicIRContract) =>
  post<{ valid: boolean; contract: OceanicIRContract }>('/oceanic/contracts', contract)

// ---- Verification ----
export const verifyContract = (contract: OceanicIRContract) =>
  post<CompilationReport>('/oceanic/verify', contract)

// ---- Attestation ----
export const attestContract = (
  contract: OceanicIRContract,
  reviewer?: string,
  reason?: string
) =>
  post<Record<string, unknown>>('/oceanic/attest', {
    ...contract,
    ...(reviewer && { reviewer }),
    ...(reason && { reason }),
  })

// ---- Lifecycle ----
export const runLifecycle = (
  contract: OceanicIRContract,
  opts: { reviewer: string; reason: string; expected?: number; execute_value?: number }
) =>
  post<Record<string, unknown>>('/oceanic/lifecycle/run', { ...contract, ...opts })

export const getLifecycleEvents = () =>
  get<LedgerEvent[]>('/oceanic/lifecycle/events')

export const verifyChain = () =>
  get<ChainVerification>('/oceanic/lifecycle/chain/verify')

// ---- Perspectives ----
export const getPerspectives = (contract: OceanicIRContract) =>
  post<PerspectivesComparison>('/oceanic/perspectives', contract)

// ---- Drift ----
export const getDriftStats = () =>
  get<DriftStats>('/oceanic/drift/stats')

// ---- Consensus (Phase 6) ----
export const runConsensus = (prompt: string, maxIterations = 3) =>
  post<ConsensusResult>('/oceanic/consensus', {
    prompt,
    max_iterations: maxIterations,
  })

// ---- Handoff (Phase 6) ----
export const exportHandoff = (
  sourceRepo: string,
  targetRepo: string,
  payload: Record<string, unknown>,
  sequence = 1,
  attestationId?: string
) =>
  post<HandoffPacket>('/oceanic/handoff/export', {
    source_repo: sourceRepo,
    target_repo: targetRepo,
    payload,
    sequence,
    attestation_id: attestationId,
  })

export const importHandoff = (packet: HandoffPacket, expectedSequence?: number) =>
  post<HandoffImportResult>('/oceanic/handoff/import', {
    packet,
    expected_sequence: expectedSequence,
  })

export const verifyCycle = (packets: HandoffPacket[]) =>
  post<CycleVerification>('/oceanic/handoff/verify_cycle', { packets })

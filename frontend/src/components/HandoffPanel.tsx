import React, { useState } from 'react'
import type { HandoffPacket } from '../contracts/oceanic'
import { exportHandoff, importHandoff, verifyCycle } from '../api/client'

interface HandoffPanelProps {
  onPacketCreated?: (packet: HandoffPacket) => void
}

export const HandoffPanel: React.FC<HandoffPanelProps> = ({ onPacketCreated }) => {
  const [sourceRepo, setSourceRepo] = useState('oceanic-a')
  const [targetRepo, setTargetRepo] = useState('oceanic-b')
  const [payload, setPayload] = useState('{"msg": "handoff test"}')
  const [sequence, setSequence] = useState(1)
  const [result, setResult] = useState<string>('')
  const [loading, setLoading] = useState(false)

  const [packets, setPackets] = useState<HandoffPacket[]>([])
  const [cycleResult, setCycleResult] = useState<string>('')

  const handleExport = async () => {
    setLoading(true)
    setResult('')
    try {
      const parsed = JSON.parse(payload)
      const pkt = await exportHandoff(sourceRepo, targetRepo, parsed, sequence)
      setResult(JSON.stringify(pkt, null, 2))
      setPackets((prev) => [...prev, pkt])
      setSequence((s) => s + 1)
      onPacketCreated?.(pkt)
    } catch (err) {
      setResult(`ERROR: ${err instanceof Error ? err.message : String(err)}`)
    } finally {
      setLoading(false)
    }
  }

  const handleImport = async () => {
    if (packets.length === 0) {
      setResult('No packets to import. Export one first.')
      return
    }
    setLoading(true)
    setResult('')
    try {
      const lastPacket = packets[packets.length - 1]
      const importRes = await importHandoff(lastPacket)
      setResult(JSON.stringify(importRes, null, 2))
    } catch (err) {
      setResult(`ERROR: ${err instanceof Error ? err.message : String(err)}`)
    } finally {
      setLoading(false)
    }
  }

  const handleVerifyCycle = async () => {
    if (packets.length < 2) {
      setCycleResult('Need at least 2 packets to verify a cycle.')
      return
    }
    setLoading(true)
    setCycleResult('')
    try {
      const res = await verifyCycle(packets)
      setCycleResult(JSON.stringify(res, null, 2))
    } catch (err) {
      setCycleResult(`ERROR: ${err instanceof Error ? err.message : String(err)}`)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div
      style={{
        background: 'rgba(0, 0, 0, 0.4)',
        border: '1px solid #222',
        backdropFilter: 'blur(12px)',
        padding: '1rem',
      }}
    >
      <div
        style={{
          fontSize: '0.66rem',
          letterSpacing: '0.1em',
          textTransform: 'uppercase',
          color: '#7fb3bf',
          marginBottom: '0.75rem',
        }}
      >
        Cross-Repo Handoff — A → B → C → A → ∞
      </div>

      <div style={{ display: 'grid', gap: '0.5rem', marginBottom: '0.75rem' }}>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <div style={{ flex: 1 }}>
            <label style={labelStyle}>Source Repo</label>
            <input
              value={sourceRepo}
              onChange={(e) => setSourceRepo(e.target.value)}
              style={inputStyle}
            />
          </div>
          <div style={{ flex: 1 }}>
            <label style={labelStyle}>Target Repo</label>
            <input
              value={targetRepo}
              onChange={(e) => setTargetRepo(e.target.value)}
              style={inputStyle}
            />
          </div>
        </div>

        <div>
          <label style={labelStyle}>Payload (JSON)</label>
          <textarea
            value={payload}
            onChange={(e) => setPayload(e.target.value)}
            rows={2}
            style={{ ...inputStyle, resize: 'vertical' }}
          />
        </div>

        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button onClick={handleExport} disabled={loading} style={btnStyle}>
            Export Packet
          </button>
          <button onClick={handleImport} disabled={loading} style={ghostBtnStyle}>
            Import Last
          </button>
          <button onClick={handleVerifyCycle} disabled={loading} style={ghostBtnStyle}>
            Verify Cycle
          </button>
        </div>
      </div>

      {/* Packet count */}
      {packets.length > 0 && (
        <div style={{ color: '#555', fontSize: '0.68rem', marginBottom: '0.5rem' }}>
          {packets.length} packet{packets.length !== 1 ? 's' : ''} in session
        </div>
      )}

      {/* Result */}
      {result && (
        <pre
          style={{
            background: '#000',
            color: '#cfcfcf',
            padding: '0.75rem',
            border: '1px solid #222',
            overflowX: 'auto',
            maxHeight: '12rem',
            fontSize: '0.72rem',
            whiteSpace: 'pre-wrap',
            wordBreak: 'break-all',
          }}
        >
          {result}
        </pre>
      )}

      {/* Cycle result */}
      {cycleResult && (
        <pre
          style={{
            background: '#000',
            color: '#7fb3bf',
            padding: '0.75rem',
            border: '1px solid #1a3a3a',
            overflowX: 'auto',
            maxHeight: '8rem',
            fontSize: '0.72rem',
            whiteSpace: 'pre-wrap',
            wordBreak: 'break-all',
            marginTop: '0.5rem',
          }}
        >
          {cycleResult}
        </pre>
      )}
    </div>
  )
}

const labelStyle: React.CSSProperties = {
  color: '#777',
  fontSize: '0.66rem',
  textTransform: 'uppercase',
  letterSpacing: '0.1em',
  display: 'block',
  marginBottom: '0.2rem',
}

const inputStyle: React.CSSProperties = {
  font: 'inherit',
  padding: '0.45rem',
  background: '#0a0a0a',
  color: '#e6e6e6',
  border: '1px solid #333',
  width: '100%',
  fontFamily: '"IBM Plex Mono", monospace',
  fontSize: '0.76rem',
}

const btnStyle: React.CSSProperties = {
  font: 'inherit',
  padding: '0.45rem 0.8rem',
  background: '#e6e6e6',
  color: '#000',
  border: '1px solid #e6e6e6',
  cursor: 'pointer',
  textTransform: 'uppercase',
  letterSpacing: '0.1em',
  fontSize: '0.72rem',
  fontFamily: '"IBM Plex Mono", monospace',
}

const ghostBtnStyle: React.CSSProperties = {
  ...btnStyle,
  background: '#0a0a0a',
  color: '#e6e6e6',
  border: '1px solid #444',
}

export default HandoffPanel

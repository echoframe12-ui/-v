import React, { useEffect, useState, useCallback } from 'react'
import {
  getHealth,
  verifyChain,
  getLifecycleEvents,
  getDriftStats,
} from '../api/client'
import type {
  HealthResponse,
  ChainVerification,
  LedgerEvent,
  DriftStats,
} from '../contracts/oceanic'
import MoodBadge from '../components/MoodBadge'
import LedgerTimeline from '../components/LedgerTimeline'

export const ConsolePage: React.FC = () => {
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [chain, setChain] = useState<ChainVerification | null>(null)
  const [events, setEvents] = useState<LedgerEvent[]>([])
  const [drift, setDrift] = useState<DriftStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const refresh = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [h, c, e, d] = await Promise.all([
        getHealth().catch(() => null),
        verifyChain().catch(() => null),
        getLifecycleEvents().catch(() => []),
        getDriftStats().catch(() => null),
      ])
      setHealth(h)
      setChain(c)
      setEvents(e)
      setDrift(d)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    refresh()
    const interval = setInterval(refresh, 15_000)
    return () => clearInterval(interval)
  }, [refresh])

  return (
    <div>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1.5rem' }}>
        <h1 style={h1Style}>
          Ω∞v Verification Console
          <span style={cursorStyle} />
        </h1>
        {health && (
          <MoodBadge
            status={health.status === 'ok' ? 'clear' : 'dissent'}
            size="md"
          />
        )}
      </div>

      {error && (
        <div style={errorBannerStyle}>
          DISSENT: {error}
        </div>
      )}

      {/* Status Tiles */}
      <div style={tilesStyle}>
        <Tile
          label="System"
          value={loading ? '…' : health ? health.status.toUpperCase() : 'OFFLINE'}
          color={health?.status === 'ok' ? '#7fbf7f' : '#bf7f7f'}
        />
        <Tile
          label="Ledger Chain"
          value={chain ? (chain.valid ? 'INTACT' : 'BROKEN') : '—'}
          color={chain?.valid ? '#7fbf7f' : '#bf7f7f'}
        />
        <Tile
          label="Events"
          value={chain?.length?.toString() ?? events.length.toString()}
          color="#7fb3bf"
        />
        <Tile
          label="Drift"
          value={
            drift
              ? `${(drift.deviated_ratio * 100).toFixed(1)}%`
              : '—'
          }
          color={drift && drift.deviated_ratio > 0 ? '#bf9f7f' : '#7fbf7f'}
        />
        <Tile
          label="Intact"
          value={drift?.intact?.toString() ?? '—'}
          color="#7fbf9f"
        />
        <Tile
          label="Deviated"
          value={drift?.deviated?.toString() ?? '—'}
          color={drift && drift.deviated > 0 ? '#bf7f7f' : '#7fbf7f'}
        />
      </div>

      {/* Refresh button */}
      <div style={{ margin: '1rem 0' }}>
        <button onClick={refresh} disabled={loading} style={btnStyle}>
          {loading ? 'Refreshing…' : 'Refresh'}
        </button>
      </div>

      {/* Ledger Timeline */}
      <LedgerTimeline events={events} maxVisible={100} />

      {/* Footer */}
      <div style={footerStyle}>
        checksum 0xΩ∞v · observer online · attest, don't assert
      </div>
    </div>
  )
}

// ---- Sub-components ----

const Tile: React.FC<{ label: string; value: string; color: string }> = ({
  label,
  value,
  color,
}) => (
  <div
    style={{
      background: 'rgba(0, 0, 0, 0.5)',
      border: '1px solid #222',
      backdropFilter: 'blur(12px)',
      padding: '0.75rem',
    }}
  >
    <div
      style={{
        color: '#777',
        fontSize: '0.6rem',
        textTransform: 'uppercase',
        letterSpacing: '0.12em',
      }}
    >
      {label}
    </div>
    <div
      style={{
        fontSize: '1.5rem',
        marginTop: '0.25rem',
        color,
        fontWeight: 500,
        fontVariantNumeric: 'tabular-nums',
      }}
    >
      {value}
    </div>
  </div>
)

// ---- Styles ----

const h1Style: React.CSSProperties = {
  fontSize: '1.1rem',
  letterSpacing: '0.08em',
  textTransform: 'uppercase',
  borderBottom: 'none',
  paddingBottom: 0,
  margin: 0,
}

const cursorStyle: React.CSSProperties = {
  display: 'inline-block',
  width: '0.6em',
  height: '1em',
  background: '#e6e6e6',
  verticalAlign: 'text-bottom',
  marginLeft: '0.3rem',
  animation: 'blink 1.06s steps(1) infinite',
}

const tilesStyle: React.CSSProperties = {
  display: 'grid',
  gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))',
  gap: '0.75rem',
}

const btnStyle: React.CSSProperties = {
  font: 'inherit',
  padding: '0.5rem 1rem',
  background: '#e6e6e6',
  color: '#000',
  border: '1px solid #e6e6e6',
  cursor: 'pointer',
  textTransform: 'uppercase',
  letterSpacing: '0.1em',
  fontSize: '0.72rem',
  fontFamily: '"IBM Plex Mono", monospace',
}

const errorBannerStyle: React.CSSProperties = {
  background: 'rgba(90, 45, 45, 0.2)',
  border: '1px solid #5a2d2d',
  color: '#bf7f7f',
  padding: '0.75rem',
  marginBottom: '1rem',
  fontSize: '0.76rem',
  fontFamily: '"IBM Plex Mono", monospace',
}

const footerStyle: React.CSSProperties = {
  color: '#555',
  fontSize: '0.7rem',
  marginTop: '1.5rem',
  borderTop: '1px solid #222',
  paddingTop: '0.5rem',
}

export default ConsolePage

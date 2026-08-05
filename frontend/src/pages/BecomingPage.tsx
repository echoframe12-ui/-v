import React, { useEffect, useState, useCallback } from 'react'
import { getLifecycleEvents, verifyChain } from '../api/client'
import type { LedgerEvent, ChainVerification } from '../contracts/oceanic'
import MoodBadge from '../components/MoodBadge'

// The lifecycle states in Ω∞v order
const STATES = [
  'THOUGHT', 'POSSIBILITY', 'CHARTER', 'COMPILE', 'VERIFY',
  'OBSERVE', 'CONSENSUS', 'ATTEST', 'EVIDENCE', 'ACTION',
  'CONSEQUENCE', 'LEARNING', 'DRIFT', 'RECOMPILE', 'BECOMING',
]

const stateColor = (state: string): string => {
  const idx = STATES.indexOf(state)
  if (idx < 0) return '#777'
  const hue = (idx / STATES.length) * 280 + 120 // green → violet
  return `hsl(${hue}, 45%, 60%)`
}

export const BecomingPage: React.FC = () => {
  const [events, setEvents] = useState<LedgerEvent[]>([])
  const [chain, setChain] = useState<ChainVerification | null>(null)
  const [loading, setLoading] = useState(true)
  const [currentState, setCurrentState] = useState('THOUGHT')

  const refresh = useCallback(async () => {
    setLoading(true)
    try {
      const [e, c] = await Promise.all([
        getLifecycleEvents().catch(() => []),
        verifyChain().catch(() => null),
      ])
      setEvents(e)
      setChain(c)

      // Determine current state from last lifecycle event
      if (e.length > 0) {
        const last = e[e.length - 1]
        const p = last.payload as Record<string, unknown>
        const s = (p?.state as string) ?? (p?.next_state as string) ?? 'THOUGHT'
        setCurrentState(s.toUpperCase())
      }
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    refresh()
    const interval = setInterval(refresh, 10_000)
    return () => clearInterval(interval)
  }, [refresh])

  // Extract mood from most recent mood event
  const lastMoodEvent = [...events].reverse().find(
    (e) => e.event_type.startsWith('mood.')
  )
  const moodStatus = lastMoodEvent?.event_type === 'mood.dissent' ? 'dissent' : 'clear'

  return (
    <div>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1.5rem' }}>
        <h1 style={h1Style}>
          Continuous Becoming
          <span style={cursorStyle} />
        </h1>
        <MoodBadge status={moodStatus} />
      </div>

      {/* Lifecycle ring visualization */}
      <div
        style={{
          background: 'rgba(0, 0, 0, 0.4)',
          border: '1px solid #222',
          backdropFilter: 'blur(12px)',
          padding: '1.5rem',
          marginBottom: '1rem',
        }}
      >
        <div style={sectionTitle}>Lifecycle Ring</div>
        <div
          style={{
            display: 'flex',
            flexWrap: 'wrap',
            gap: '0.25rem',
            alignItems: 'center',
          }}
        >
          {STATES.map((state, i) => {
            const isCurrent = state === currentState
            return (
              <React.Fragment key={state}>
                <span
                  style={{
                    padding: '0.25rem 0.5rem',
                    fontSize: '0.68rem',
                    letterSpacing: '0.08em',
                    fontFamily: '"IBM Plex Mono", monospace',
                    color: isCurrent ? '#000' : stateColor(state),
                    background: isCurrent ? stateColor(state) : 'transparent',
                    border: `1px solid ${isCurrent ? stateColor(state) : '#222'}`,
                    fontWeight: isCurrent ? 600 : 400,
                    transition: 'all 0.4s ease',
                    boxShadow: isCurrent
                      ? `0 0 12px ${stateColor(state)}40`
                      : 'none',
                  }}
                >
                  {state}
                </span>
                {i < STATES.length - 1 && (
                  <span style={{ color: '#333', fontSize: '0.7rem' }}>→</span>
                )}
              </React.Fragment>
            )
          })}
          <span style={{ color: '#333', fontSize: '0.7rem' }}>→ ∞</span>
        </div>
      </div>

      {/* Chain integrity */}
      <div
        style={{
          background: 'rgba(0, 0, 0, 0.4)',
          border: '1px solid #222',
          backdropFilter: 'blur(12px)',
          padding: '1rem',
          marginBottom: '1rem',
          display: 'grid',
          gridTemplateColumns: '1fr 1fr 1fr',
          gap: '1rem',
        }}
      >
        <div>
          <div style={sectionTitle}>Chain</div>
          <div style={{ color: chain?.valid ? '#7fbf7f' : '#bf7f7f', fontSize: '1.2rem' }}>
            {loading ? '…' : chain?.valid ? 'INTACT' : 'UNVERIFIED'}
          </div>
        </div>
        <div>
          <div style={sectionTitle}>Length</div>
          <div style={{ color: '#7fb3bf', fontSize: '1.2rem' }}>
            {chain?.length ?? events.length}
          </div>
        </div>
        <div>
          <div style={sectionTitle}>Current State</div>
          <div style={{ color: stateColor(currentState), fontSize: '1.2rem' }}>
            {currentState}
          </div>
        </div>
      </div>

      {/* Recent transitions */}
      <div
        style={{
          background: 'rgba(0, 0, 0, 0.4)',
          border: '1px solid #222',
          backdropFilter: 'blur(12px)',
          padding: '1rem',
        }}
      >
        <div style={sectionTitle}>Recent Transitions</div>
        {events.length === 0 && (
          <div style={{ color: '#555', fontSize: '0.76rem' }}>
            No lifecycle events yet. The system awaits its first becoming.
          </div>
        )}
        {events
          .slice(-20)
          .reverse()
          .map((ev) => {
            const p = ev.payload as Record<string, unknown>
            return (
              <div
                key={`${ev.sequence}-${ev.event_digest}`}
                style={{
                  display: 'grid',
                  gridTemplateColumns: '3rem 1fr auto',
                  gap: '0.5rem',
                  padding: '0.3rem 0',
                  borderBottom: '1px solid #1a1a1a',
                  fontSize: '0.72rem',
                }}
              >
                <span style={{ color: '#555' }}>#{ev.sequence}</span>
                <span>
                  <span style={{ color: stateColor(String(p?.current_state ?? '')) }}>
                    {String(p?.current_state ?? ev.event_type)}
                  </span>
                  {p?.next_state && (
                    <>
                      <span style={{ color: '#333' }}> → </span>
                      <span style={{ color: stateColor(String(p.next_state)) }}>
                        {String(p.next_state)}
                      </span>
                    </>
                  )}
                </span>
                <span style={{ color: '#3a5a3a', fontSize: '0.64rem' }}>
                  {ev.event_digest.slice(0, 8)}…
                </span>
              </div>
            )
          })}
      </div>

      {/* Refresh */}
      <div style={{ marginTop: '1rem' }}>
        <button onClick={refresh} disabled={loading} style={btnStyle}>
          {loading ? 'Refreshing…' : 'Refresh'}
        </button>
      </div>
    </div>
  )
}

const h1Style: React.CSSProperties = {
  fontSize: '1.1rem',
  letterSpacing: '0.08em',
  textTransform: 'uppercase',
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

const sectionTitle: React.CSSProperties = {
  fontSize: '0.62rem',
  letterSpacing: '0.1em',
  textTransform: 'uppercase',
  color: '#777',
  marginBottom: '0.5rem',
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

export default BecomingPage

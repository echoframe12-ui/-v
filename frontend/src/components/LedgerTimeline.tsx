import React from 'react'
import type { LedgerEvent } from '../contracts/oceanic'

interface LedgerTimelineProps {
  events: LedgerEvent[]
  maxVisible?: number
}

const eventColor = (type: string): string => {
  if (type.startsWith('mood.dissent')) return '#bf7f7f'
  if (type.startsWith('mood.')) return '#7fbf7f'
  if (type.startsWith('handoff.')) return '#7fb3bf'
  if (type.startsWith('consensus.')) return '#bf9f7f'
  if (type.startsWith('lifecycle.')) return '#9f7fbf'
  if (type.startsWith('attestation.')) return '#7fbf9f'
  return '#999'
}

const truncHash = (h: string | null): string =>
  h ? `${h.slice(0, 8)}…` : '—'

export const LedgerTimeline: React.FC<LedgerTimelineProps> = ({
  events,
  maxVisible = 50,
}) => {
  const visible = events.slice(-maxVisible).reverse()

  return (
    <div
      style={{
        background: 'rgba(0, 0, 0, 0.4)',
        border: '1px solid #222',
        backdropFilter: 'blur(12px)',
        padding: '1rem',
        maxHeight: '28rem',
        overflowY: 'auto',
      }}
    >
      <div
        style={{
          fontSize: '0.66rem',
          letterSpacing: '0.1em',
          textTransform: 'uppercase',
          color: '#777',
          marginBottom: '0.75rem',
        }}
      >
        Event Ledger — {events.length} entries
      </div>

      {visible.length === 0 && (
        <div style={{ color: '#555', fontSize: '0.76rem' }}>
          No events recorded yet.
        </div>
      )}

      {visible.map((ev) => (
        <div
          key={`${ev.sequence}-${ev.event_digest}`}
          style={{
            display: 'grid',
            gridTemplateColumns: '3rem 1fr auto',
            gap: '0.5rem',
            padding: '0.35rem 0',
            borderBottom: '1px solid #1a1a1a',
            alignItems: 'start',
            fontSize: '0.74rem',
            animation: 'ledgerFadeIn 0.3s ease-out',
          }}
        >
          {/* Sequence number */}
          <span style={{ color: '#555', fontVariantNumeric: 'tabular-nums' }}>
            #{ev.sequence}
          </span>

          {/* Event type + entity */}
          <div>
            <span
              style={{
                color: eventColor(ev.event_type),
                fontWeight: 500,
              }}
            >
              {ev.event_type}
            </span>
            <span style={{ color: '#555', marginLeft: '0.4rem' }}>
              {ev.entity_id}
            </span>
          </div>

          {/* Digest */}
          <span
            style={{
              color: '#3a5a3a',
              fontFamily: '"IBM Plex Mono", monospace',
              fontSize: '0.66rem',
            }}
            title={ev.event_digest}
          >
            {truncHash(ev.event_digest)}
          </span>
        </div>
      ))}
    </div>
  )
}

export default LedgerTimeline

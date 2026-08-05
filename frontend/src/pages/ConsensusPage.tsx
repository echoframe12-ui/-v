import React, { useState } from 'react'
import { runConsensus } from '../api/client'
import type { ConsensusResult } from '../contracts/oceanic'
import MoodBadge from '../components/MoodBadge'
import HandoffPanel from '../components/HandoffPanel'

export const ConsensusPage: React.FC = () => {
  const [prompt, setPrompt] = useState('')
  const [maxIter, setMaxIter] = useState(3)
  const [result, setResult] = useState<ConsensusResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleRun = async () => {
    if (!prompt.trim()) return
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const res = await runConsensus(prompt.trim(), maxIter)
      setResult(res)
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      {/* Header */}
      <h1 style={h1Style}>
        Multi-Agent Consensus
        <span style={cursorStyle} />
      </h1>
      <p style={{ color: '#777', fontSize: '0.76rem', margin: '0.5rem 0 1.5rem' }}>
        Iterative perspective evaluation with MOOD-gated convergence.
        Dissent is data.
      </p>

      {/* Consensus input */}
      <div
        style={{
          background: 'rgba(0, 0, 0, 0.4)',
          border: '1px solid #222',
          backdropFilter: 'blur(12px)',
          padding: '1rem',
          marginBottom: '1rem',
        }}
      >
        <div style={sectionTitle}>Run Consensus Loop</div>

        <div style={{ display: 'grid', gap: '0.5rem' }}>
          <div>
            <label style={labelStyle}>Consensus Prompt</label>
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="What should the agents evaluate?"
              rows={3}
              style={{ ...inputStyle, resize: 'vertical' }}
            />
          </div>

          <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'end' }}>
            <div style={{ width: '8rem' }}>
              <label style={labelStyle}>Max Iterations</label>
              <input
                type="number"
                min={1}
                max={10}
                value={maxIter}
                onChange={(e) => setMaxIter(Number(e.target.value))}
                style={inputStyle}
              />
            </div>
            <button onClick={handleRun} disabled={loading || !prompt.trim()} style={btnStyle}>
              {loading ? 'Running…' : 'Run Consensus'}
            </button>
          </div>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div style={errorStyle}>
          DISSENT: {error}
        </div>
      )}

      {/* Result */}
      {result && (
        <div
          style={{
            background: 'rgba(0, 0, 0, 0.4)',
            border: '1px solid #222',
            backdropFilter: 'blur(12px)',
            padding: '1rem',
            marginBottom: '1rem',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
            <div style={sectionTitle}>Consensus Result</div>
            <MoodBadge status={result.mood} size="sm" />
          </div>

          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))',
              gap: '0.75rem',
              marginBottom: '1rem',
            }}
          >
            <ResultTile label="Converged" value={result.converged ? 'YES' : 'NO'} color={result.converged ? '#7fbf7f' : '#bf7f7f'} />
            <ResultTile label="Iterations" value={result.iterations.toString()} color="#7fb3bf" />
            <ResultTile label="Dissent Score" value={result.final_dissent_score.toFixed(3)} color={result.final_dissent_score > 0.5 ? '#bf7f7f' : '#7fbf7f'} />
            <ResultTile label="Mood" value={result.mood.toUpperCase()} color={result.mood === 'clear' ? '#7fbf7f' : '#bf7f7f'} />
          </div>

          {/* Transition */}
          {result.transition && (
            <div style={{ marginTop: '0.5rem' }}>
              <div style={sectionTitle}>State Transition</div>
              <div style={{ fontSize: '0.76rem' }}>
                <span style={{ color: '#bf9f7f' }}>{result.transition.current_state}</span>
                <span style={{ color: '#333' }}> → </span>
                <span style={{ color: '#7fbf9f' }}>{result.transition.next_state}</span>
                <span style={{ color: '#555', marginLeft: '0.5rem' }}>
                  [{result.transition.action}]
                </span>
              </div>
              <div style={{ color: '#555', fontSize: '0.68rem', marginTop: '0.25rem' }}>
                {result.transition.reason}
              </div>
              <div style={{ color: '#3a5a3a', fontSize: '0.62rem', marginTop: '0.25rem' }}>
                hash: {result.transition.verification_hash?.slice(0, 16)}…
              </div>
            </div>
          )}
        </div>
      )}

      {/* Handoff panel */}
      <div style={{ marginTop: '1.5rem' }}>
        <HandoffPanel />
      </div>
    </div>
  )
}

const ResultTile: React.FC<{ label: string; value: string; color: string }> = ({
  label, value, color,
}) => (
  <div style={{ background: '#000', border: '1px solid #222', padding: '0.5rem' }}>
    <div style={{ color: '#777', fontSize: '0.58rem', textTransform: 'uppercase', letterSpacing: '0.1em' }}>
      {label}
    </div>
    <div style={{ color, fontSize: '1.1rem', marginTop: '0.15rem', fontWeight: 500 }}>
      {value}
    </div>
  </div>
)

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
  padding: '0.5rem 1rem',
  background: '#e6e6e6',
  color: '#000',
  border: '1px solid #e6e6e6',
  cursor: 'pointer',
  textTransform: 'uppercase',
  letterSpacing: '0.1em',
  fontSize: '0.72rem',
  fontFamily: '"IBM Plex Mono", monospace',
  whiteSpace: 'nowrap',
}

const errorStyle: React.CSSProperties = {
  background: 'rgba(90, 45, 45, 0.2)',
  border: '1px solid #5a2d2d',
  color: '#bf7f7f',
  padding: '0.75rem',
  marginBottom: '1rem',
  fontSize: '0.76rem',
}

export default ConsensusPage

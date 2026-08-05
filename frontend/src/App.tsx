import React from 'react'
import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import ConsolePage from './pages/ConsolePage'
import BecomingPage from './pages/BecomingPage'
import ConsensusPage from './pages/ConsensusPage'

const navItems = [
  { to: '/', label: 'Console' },
  { to: '/becoming', label: 'Becoming' },
  { to: '/consensus', label: 'Consensus' },
]

const App: React.FC = () => {
  return (
    <BrowserRouter>
      <div style={{ minHeight: '100vh', background: '#0a0a0a', color: '#e6e6e6' }}>
        {/* Navigation */}
        <nav style={navStyle}>
          <div style={navBrandStyle}>
            <span style={{ color: '#7fbf9f', fontWeight: 600 }}>Ω∞v</span>
            <span style={{ color: '#777', marginLeft: '0.4rem' }}>OceanicOS</span>
          </div>
          <div style={{ display: 'flex', gap: '0.25rem' }}>
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === '/'}
                style={({ isActive }) => ({
                  ...navLinkStyle,
                  background: isActive ? 'rgba(127, 191, 159, 0.12)' : 'transparent',
                  borderColor: isActive ? '#2d5a3d' : 'transparent',
                  color: isActive ? '#7fbf9f' : '#777',
                })}
              >
                {item.label}
              </NavLink>
            ))}
          </div>
        </nav>

        {/* Page content */}
        <main style={mainStyle}>
          <Routes>
            <Route path="/" element={<ConsolePage />} />
            <Route path="/becoming" element={<BecomingPage />} />
            <Route path="/consensus" element={<ConsensusPage />} />
          </Routes>
        </main>

        {/* System footer */}
        <footer style={footerStyle}>
          <span>Each step contains all steps. Each end is a new beginning.</span>
          <span style={{ color: '#333' }}>·</span>
          <span>Ω∞v</span>
        </footer>
      </div>
    </BrowserRouter>
  )
}

const navStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
  padding: '0.75rem 1.5rem',
  borderBottom: '1px solid #1a1a1a',
  background: 'rgba(0, 0, 0, 0.6)',
  backdropFilter: 'blur(16px)',
  position: 'sticky',
  top: 0,
  zIndex: 100,
}

const navBrandStyle: React.CSSProperties = {
  fontFamily: '"IBM Plex Mono", monospace',
  fontSize: '0.82rem',
  letterSpacing: '0.08em',
  textTransform: 'uppercase',
}

const navLinkStyle: React.CSSProperties = {
  fontFamily: '"IBM Plex Mono", monospace',
  fontSize: '0.7rem',
  letterSpacing: '0.08em',
  textTransform: 'uppercase',
  textDecoration: 'none',
  padding: '0.35rem 0.65rem',
  border: '1px solid transparent',
  transition: 'all 0.25s ease',
}

const mainStyle: React.CSSProperties = {
  maxWidth: '960px',
  margin: '0 auto',
  padding: '1.5rem',
}

const footerStyle: React.CSSProperties = {
  display: 'flex',
  justifyContent: 'center',
  gap: '0.5rem',
  padding: '1rem',
  color: '#333',
  fontSize: '0.62rem',
  fontFamily: '"IBM Plex Mono", monospace',
  letterSpacing: '0.08em',
  borderTop: '1px solid #111',
}

export default App

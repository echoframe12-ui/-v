import React from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import ConsolePage from '../pages/ConsolePage'

describe('ConsolePage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders title and loading state initially', async () => {
    // Mock API responses
    ;(global.fetch as any).mockImplementation((url: string) => {
      if (url.endsWith('/status')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ status: 'ok', version: '0.1.0' }),
        })
      }
      if (url.endsWith('/lifecycle/chain/verify')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ valid: true, length: 12 }),
        })
      }
      if (url.endsWith('/lifecycle/events')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve([]),
        })
      }
      if (url.endsWith('/drift/stats')) {
        return Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve({
              total_audits: 10,
              intact: 10,
              deviated: 0,
              deviated_ratio: 0.0,
            }),
        })
      }
      return Promise.reject(new Error(`Unhandled URL: ${url}`))
    })

    render(<ConsolePage />)

    expect(screen.getByText(/Ω∞v Verification Console/i)).toBeInTheDocument()

    await waitFor(() => {
      expect(screen.getByText('INTACT')).toBeInTheDocument()
    })
  })
})

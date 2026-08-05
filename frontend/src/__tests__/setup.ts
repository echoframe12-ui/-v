import '@testing-library/jest-dom'
import { vi } from 'vitest'

// Mock fetch globally for Vitest
global.fetch = vi.fn()

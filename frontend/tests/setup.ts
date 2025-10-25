import '@testing-library/jest-dom'
import React from 'react'
import { vi } from 'vitest'

// Polyfill URL.createObjectURL / URL.revokeObjectURL for jsdom
if (!(URL as any).createObjectURL) {
  Object.defineProperty(URL, 'createObjectURL', {
    writable: true,
    value: (() => 'blob:mock') as any,
  })
}
if (!(URL as any).revokeObjectURL) {
  Object.defineProperty(URL, 'revokeObjectURL', {
    writable: true,
    value: (() => {}) as any,
  })
}

// Polyfill Element.scrollTo for jsdom environment used by Vitest
if (!(Element.prototype as any).scrollTo) {
  Object.defineProperty(Element.prototype, 'scrollTo', {
    writable: true,
    value: (() => {}) as any,
  })
}

// Mock window.matchMedia for tests
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {}, // deprecated, but needed for some libs
    removeListener: () => {}, // deprecated, but needed for some libs
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
})

// Mock IntersectionObserver
// Provide minimal fields/methods expected by code and DOM types
global.IntersectionObserver = class IntersectionObserver {
  root: Element | null = null
  rootMargin: string = ''
  thresholds: ReadonlyArray<number> = []

  constructor() {}

  observe(_target: Element) {}
  disconnect() {}
  unobserve(_target: Element) {}
  takeRecords(): IntersectionObserverEntry[] { return [] }
}

// Mock ResizeObserver
global.ResizeObserver = class ResizeObserver {
  cb: any
  constructor(cb: any) {
    this.cb = cb
  }
  observe(_target?: Element) {}
  disconnect() {}
  unobserve(_target?: Element) {}
}

// Mock AuthProvider/useAuth so components can render in tests without real auth
vi.mock('@/contexts/AuthContext', () => ({
  AuthProvider: ({ children }: { children: React.ReactNode }) =>
    React.createElement('div', { 'data-testid': 'auth-provider' }, children),
  useAuth: () => ({
    user: { id: 'test-user' },
    isAuthenticated: true,
    isLoading: false,
    login: vi.fn(),
    register: vi.fn(),
    logout: vi.fn(),
    refreshUser: vi.fn(),
  }) as any,
}))

// Global mock for i18n to avoid undefined i18n.language in components/hooks
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string, defaultValue?: string) => (defaultValue ?? key),
    i18n: {
      language: 'en',
      changeLanguage: vi.fn(),
    },
  }),
  Trans: ({ children }: any) => children,
}))

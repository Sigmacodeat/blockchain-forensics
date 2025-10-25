import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import React from 'react'
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import AIAgentPage from '@/pages/AIAgentPage'

// Mock i18n to avoid full init
vi.mock('@/i18n/config-optimized', () => ({ default: { language: 'en' } }))
// Mock api to avoid real network in fallback
vi.mock('@/lib/api', () => ({ api: { post: vi.fn(), get: vi.fn() } }))

class MockEventSource {
  static instances: MockEventSource[] = []
  url: string
  listeners: Record<string, ((...args: any[]) => void)[]>
  onerror: ((this: EventSource, ev: Event) => any) | null = null
  constructor(url: string) {
    this.url = url
    this.listeners = {}
    MockEventSource.instances.push(this)
  }
  addEventListener(type: string, cb: any) {
    this.listeners[type] ||= []
    this.listeners[type].push(cb)
  }
  close() { /* no-op */ }
  emit(type: string, data: any) {
    const ev = { data: typeof data === 'string' ? data : JSON.stringify(data) } as MessageEvent
    for (const cb of this.listeners[type] || []) cb(ev)
  }
}

function renderAgent() {
  return render(
    <MemoryRouter initialEntries={['/en/ai-agent']}>
      <AIAgentPage />
    </MemoryRouter>
  )
}

describe('AI Agent SSE stream', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.stubGlobal('EventSource', MockEventSource)
    MockEventSource.instances = []
  })
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('renders assistant reply and context via SSE events', async () => {
    renderAgent()

    const input = screen.getByLabelText(/Nachricht eingeben/i)
    fireEvent.change(input, { target: { value: 'Hello Agent' } })

    const send = screen.getByRole('button', { name: /Senden/i })
    fireEvent.click(send)

    // Acquire created SSE instance
    await waitFor(() => expect(MockEventSource.instances.length).toBeGreaterThan(0))
    const es = MockEventSource.instances[0]

    // Emit tools and context first
    await act(async () => {
      es.emit('chat.tools', { tool_calls: [{ tool: 'risk_score' }, { tool: 'find_path' }] })
      es.emit('chat.context', { snippets: [ { source: 'https://example.com/doc', snippet: 'relevant snippet' } ] })
      // Then final answer
      es.emit('chat.answer', { reply: 'Antwort vom Agenten' })
    })

    // Verify UI updated
    await screen.findByText(/Antwort vom Agenten/i)
    await screen.findByText(/\(Tools\): risk_score, find_path/i)
    await screen.findByText(/relevant snippet/i)
  })
})

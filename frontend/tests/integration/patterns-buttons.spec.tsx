import { describe, it, expect, vi, beforeEach } from 'vitest'
import React from 'react'
import { render, screen, waitFor, within, act } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import PatternsPage from '@/pages/PatternsPage'

vi.mock('@/lib/api', () => ({ api: { get: vi.fn() } }))
const { api } = await import('@/lib/api')

function wrap(ui: React.ReactElement, initial: string = '/en/patterns') {
  const qc = new QueryClient()
  return (
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={[initial]}>
        {ui}
      </MemoryRouter>
    </QueryClientProvider>
  )
}

describe('PatternsPage evidence action buttons', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('öffnet Investigator-Links mit korrekten Parametern', async () => {
    ;(api.get as any).mockResolvedValue({
      data: {
        address: '0xabc123456789',
        findings: [
          {
            pattern: 'peel_chain',
            score: 0.7,
            explanation: 'Mock',
            evidence: [
              {
                tx_hash: '0xtest',
                from_address: '0xFROM12345678',
                to_address: '0xTO123456789',
                amount: 1.0,
                timestamp: '2025-01-01T10:00:00Z',
              },
            ],
          },
        ],
      },
    })

    const openSpy = vi.spyOn(window, 'open').mockImplementation(() => null as any)

    render(wrap(<PatternsPage debounceMs={0} />))

    const input = screen.getByLabelText(/Adresse/i)
    await userEvent.clear(input)
    await userEvent.type(input, '0xabc123456789')
    await act(async () => { await new Promise((resolve) => setTimeout(resolve, 0)) })

    const analyze = screen.getByRole('button', { name: /analysieren/i })
    await userEvent.click(analyze)
    await screen.findByText(/patterns.results.title/i)

    const investigatorButtons = screen.getAllByRole('button', { name: /investigator/i })
    await userEvent.click(investigatorButtons[0])

    await waitFor(() => expect(openSpy).toHaveBeenCalled())
    const firstUrl = new URL(openSpy.mock.calls[0][0] as string, 'http://localhost')
    expect(firstUrl.searchParams.get('address')?.toLowerCase()).toBe('0xtest')

    openSpy.mockRestore()
  })
})

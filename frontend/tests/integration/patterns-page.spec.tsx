import { describe, it, expect, vi, beforeEach } from 'vitest'
import React from 'react'
import { render, screen, waitFor, act } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import { I18nextProvider } from 'react-i18next'
import i18n from 'i18next'
import PatternsPage from '@/pages/PatternsPage'

vi.mock('@/lib/api', () => {
  return {
    api: {
      get: vi.fn(),
    }
  }
})

const { api } = await import('@/lib/api')

// Setup i18n for tests with German translations
const testI18n = i18n.createInstance()
testI18n.init({
  lng: 'de',
  fallbackLng: 'de',
  ns: ['translation'],
  defaultNS: 'translation',
  interpolation: { escapeValue: false },
  resources: {
    de: {
      translation: {
        'patterns.title': 'Muster-Erkennung',
        'patterns.subtitle': 'Erkennung verdächtiger Transaktionsmuster',
        'patterns.analysis.title': 'Analyse',
        'patterns.analysis.description': 'Analysieren Sie Blockchain-Adressen',
        'patterns.form.address': 'Adresse',
        'patterns.form.addressPlaceholder': 'z.B. 0x...',
        'patterns.form.patterns': 'Muster',
        'patterns.form.patternsPlaceholder': 'z.B. peel_chain',
        'patterns.form.minScore': 'Min. Score',
        'patterns.form.limit': 'Limit',
        'patterns.form.analyzing': 'Analysieren...',
        'patterns.form.analyze': 'Analysieren',
        'patterns.form.askAssistant': 'Ask Assistant',
        'patterns.form.openInvestigator': 'In Investigator öffnen',
        'patterns.form.expandInvestigator': 'In Investigator erweitern',
        'patterns.results.title': 'Ergebnisse für',
        'patterns.results.noPatterns': 'Keine Muster gefunden',
        'patterns.results.patternsFound': '{{count}} Muster gefunden',
        'patterns.results.export.csv': 'CSV Export',
        'patterns.results.export.json': 'JSON Export',
        'patterns.table.tx': 'Tx',
        'patterns.table.from': 'From',
        'patterns.table.to': 'To',
        'patterns.table.amount': 'Amount',
        'patterns.table.time': 'Timestamp',
        'patterns.table.actions': 'Aktionen',
        'patterns.table.investigator': 'Investigator',
        'patterns.table.expand': 'Erweitern',
        'patterns.table.path': 'Pfad',
        'patterns.table.copy': 'Kopieren',
        'patterns.pattern.score': '{{score}}%',
        'patterns.pattern.evidence': 'Beweise',
        'patterns.pattern.noEvidence': 'Keine Beweise',
        'patterns.status.analyzing': 'Analysiere...',
        'patterns.status.waiting': 'Bitte warten...',
        'patterns.status.complete': 'Fertig',
        'patterns.validation.invalidAddress': 'Ungültige Adresse',
        'patterns.error': 'Fehler bei der Analyse',
        'patterns.patterns.peel_chain': 'Peel Chain',
      }
    }
  }
})

function wrap(ui: React.ReactElement) {
  const qc = new QueryClient()
  return (
    <QueryClientProvider client={qc}>
      <I18nextProvider i18n={testI18n}>
        <MemoryRouter initialEntries={["/en/patterns"]}>
          {ui}
        </MemoryRouter>
      </I18nextProvider>
    </QueryClientProvider>
  )
}

describe('PatternsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('Ask Assistant is disabled for invalid address and enabled for valid', async () => {
    render(wrap(<PatternsPage debounceMs={0} />))
    const input = screen.getByLabelText(/Adresse/i)
    const askAssistant = screen.getByRole('button', { name: /Ask Assistant/i })

    await userEvent.clear(input)
    await userEvent.type(input, 'abc')
    await waitFor(() => expect(askAssistant).toBeDisabled())

    await userEvent.clear(input)
    await userEvent.type(input, '0xabc123456789')
    await waitFor(() => expect(askAssistant).not.toBeDisabled())
  })

  it('renders findings and evidence, supports CSV/JSON export', async () => {
    // mock API response (default for any GET in this test)
    ;(api.get as any).mockResolvedValue({ data: {
      address: '0xabc123456789',
      findings: [
        { pattern: 'peel_chain', score: 0.8, explanation: 'Mock', evidence: [
          { tx_hash: '0xtest', from_address: '0xfrom', to_address: '0xto', amount: 1.0, timestamp: '2025-01-01T10:00:00Z' }
        ]}
      ]
    } })

    const urlSpy = vi.spyOn(URL, 'createObjectURL').mockReturnValue('blob:dummy')
    const revokeSpy = vi.spyOn(URL, 'revokeObjectURL').mockImplementation(() => {})

    render(wrap(<PatternsPage debounceMs={0} />))

    const input = screen.getByLabelText(/Adresse/i)
    await userEvent.clear(input)
    await userEvent.type(input, '0xabc123456789')
    // simulate debounce propagation (not needed with 0ms, but keep act for safety)
    await act(async () => { await new Promise(r => setTimeout(r, 0)) })

    // ensure Ask Assistant enabled indicates addrValid propagated
    const askAssistantBtn = screen.getByRole('button', { name: /Ask Assistant/i })
    await waitFor(() => expect(askAssistantBtn).not.toBeDisabled())

    const analyze = screen.getByRole('button', { name: /Analysieren/i })
    await userEvent.click(analyze)
    await waitFor(() => expect((api.get as any)).toHaveBeenCalled())
    await Promise.resolve()

    // wait until results card is rendered (CSV Export button visible)
    const csvBtn = await screen.findByRole('button', { name: /CSV Export/i })

    // expect results section present (header + table headers)
    await screen.findByText(/Ergebnisse für/i)
    // presence of table headers confirms evidence rendered
    await screen.findByRole('columnheader', { name: /Tx/i })
    await screen.findByRole('columnheader', { name: /From/i })
    await screen.findByRole('columnheader', { name: /To/i })

    // CSV Export
    await userEvent.click(csvBtn)
    expect(urlSpy).toHaveBeenCalled()

    // JSON Export
    const jsonBtn = screen.getByRole('button', { name: /JSON Export/i })
    await userEvent.click(jsonBtn)
    expect(urlSpy).toHaveBeenCalled()

    revokeSpy.mockRestore()
    urlSpy.mockRestore()
  })
})

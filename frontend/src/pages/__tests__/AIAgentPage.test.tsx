import { describe, it, beforeEach, afterEach, expect, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter } from 'react-router-dom'

import AIAgentPage from '../AIAgentPage'

const useChatStreamMock = vi.fn()

vi.mock('@/hooks/useChatStream', () => ({
  useChatStream: (currentQuery: string) => useChatStreamMock(currentQuery),
}))

vi.mock('@/hooks/useAuth', () => ({
  useAuth: () => ({
    user: { id: '1', email: 'user@example.com', plan: 'plus', role: 'analyst' },
    isAuthenticated: true,
  }),
}))

vi.mock('@/components/BatchScreeningModal', () => ({
  BatchScreeningModal: () => null,
}))

const renderPage = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  })

  return render(
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AIAgentPage />
      </BrowserRouter>
    </QueryClientProvider>
  )
}

describe('AIAgentPage', () => {
  beforeEach(() => {
    useChatStreamMock.mockImplementation((currentQuery: string) => ({
      typing: false,
      deltaText: '',
      finalReply: currentQuery ? 'Mocked AI reply' : '',
      toolCalls: [],
      contextSnippets: [],
      error: null,
      start: vi.fn(),
      stop: vi.fn(),
    }))
  })

  afterEach(() => {
    vi.resetAllMocks()
  })

  it('rendert Begrüßung und Beispiel-Templates', () => {
    renderPage()

    expect(screen.getByText(/AI Forensic Agent/i)).toBeInTheDocument()
    expect(screen.getByText(/Beispiel-Anfragen/i)).toBeInTheDocument()
    expect(screen.getAllByRole('button', { name: /→/i }).length).toBeGreaterThan(0)
  })

  it('sendet manuelle Anfrage und zeigt Antwort', async () => {
    renderPage()

    const user = userEvent.setup()
    const input = screen.getByLabelText(/Nachricht eingeben/i)

    await user.type(input, 'Trace 0x123')
    await user.click(screen.getByRole('button', { name: /Senden/i }))

    await waitFor(() => {
      expect(screen.getByText('Trace 0x123')).toBeInTheDocument()
      expect(screen.getByText('Mocked AI reply')).toBeInTheDocument()
      expect(input).toHaveValue('')
    })
  })

  it('nutzt Quick-Template und triggert Streaming-Hook', async () => {
    renderPage()

    const user = userEvent.setup()
    const templateButton = screen.getAllByRole('button', { name: /→/i })[0]
    const templateText = templateButton.textContent?.replace('→', '').trim()

    await user.click(templateButton)

    await waitFor(() => {
      expect(useChatStreamMock).toHaveBeenCalledWith(expect.stringContaining(templateText || 'Trace all funds'))
      expect(screen.getByText('Mocked AI reply')).toBeInTheDocument()
    })
  })

  describe('Accessibility', () => {
    it('should have proper ARIA labels', () => {
      renderPage();
      
      expect(screen.getByLabelText(/message input/i)).toBeInTheDocument();
    });

    it('should be keyboard navigable', async () => {
      const user = userEvent.setup();
      renderPage();

      await user.tab();
      expect(screen.getByPlaceholderText(/Ask me anything/i)).toHaveFocus();
    });

    it('should announce new messages to screen readers', async () => {
      const user = userEvent.setup();
      renderPage();

      await user.type(screen.getByPlaceholderText(/Ask me anything/i), 'Test');
      await user.click(screen.getByRole('button', { name: /Send/i }));

      await waitFor(() => {
        expect(screen.getByRole('status')).toBeInTheDocument();
      });
    });
  });
});

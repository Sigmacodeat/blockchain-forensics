import type { ReactNode } from 'react'
import { describe, it, beforeEach, afterEach, expect, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter } from 'react-router-dom'
import CasesPage from '../CasesPage'

const mockUseCases = vi.fn()
const mockUseCreateCase = vi.fn()
const mockToastSuccess = vi.fn()
const mockToastError = vi.fn()

vi.mock('@/hooks/useCases', () => ({
  useCases: () => mockUseCases(),
  useCreateCase: () => mockUseCreateCase(),
  useCaseExport: () => ({ data: null }),
  useCaseExportCsv: () => ({ data: null }),
  useCaseChecksum: () => ({ data: null }),
}))

vi.mock('@/hooks/useAuth', () => ({
  useAuth: () => ({
    user: { id: '1', email: 'user@example.com', plan: 'pro', role: 'user' },
    isAuthenticated: true,
  }),
}))

vi.mock('@/components/BatchScreeningModal', () => ({
  BatchScreeningModal: () => null,
}))

vi.mock('@/components/ui/toast', () => ({
  ToastProvider: ({ children }: { children: ReactNode }) => children,
  useToastSuccess: () => mockToastSuccess,
  useToastError: () => mockToastError,
}))

const renderCasesPage = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  })

  const utils = render(
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <CasesPage />
      </BrowserRouter>
    </QueryClientProvider>
  )

  return {
    ...utils,
    queryClient,
  }
}

describe('CasesPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()

    mockUseCases.mockReturnValue({
      data: {
        cases: [],
      },
      isLoading: false,
      error: null,
    })

    mockUseCreateCase.mockReturnValue({ mutateAsync: vi.fn(), isPending: false })
  })

  afterEach(() => {
    vi.resetAllMocks()
  })

  it('rendert Cases-Übersicht und Suchfeld', async () => {
    mockUseCases.mockReturnValue({
      data: {
        cases: [
          {
            case_id: 'CASE-123',
            title: 'High-risk bridge transfer',
            status: 'active',
            lead_investigator: 'Jane Doe',
            created_at: '2025-10-19T10:00:00Z',
          },
        ],
      },
      isLoading: false,
      error: null,
    })

    renderCasesPage()

    expect(await screen.findByText(/Cases/i)).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/Search cases/i)).toBeInTheDocument()
    expect(screen.getByText(/High-risk bridge transfer/i)).toBeInTheDocument()
  })

  it('öffnet Create-Modal und validiert Pflichtfelder', async () => {
    renderCasesPage()

    const user = userEvent.setup()
    await user.click(screen.getByRole('button', { name: /New Case/i }))

    expect(await screen.findByLabelText(/Case ID/i)).toBeInTheDocument()

    const submitButtons = screen.getAllByRole('button', { name: /Create Case/i })
    await user.click(submitButtons[submitButtons.length - 1])

    expect(await screen.findByText(/Case ID is required/i)).toBeInTheDocument()
    expect(screen.getByText(/Title is required/i)).toBeInTheDocument()
    expect(screen.getByText(/Lead investigator is required/i)).toBeInTheDocument()
  })

  it('erstellt einen neuen Case und schließt das Modal', async () => {
    const mutateSpy = vi.fn().mockResolvedValue({ case_id: 'CASE-99' })
    mockUseCreateCase.mockReturnValue({ mutateAsync: mutateSpy, isPending: false })

    renderCasesPage()

    const user = userEvent.setup()
    await user.click(screen.getByRole('button', { name: /New Case/i }))
    await user.type(screen.getByLabelText(/Case ID/i), 'CASE-99')
    await user.type(screen.getByLabelText(/Title/i), 'Network Investigation')
    await user.type(screen.getByLabelText(/Lead Investigator/i), 'Alice')

    const submitButtons = screen.getAllByRole('button', { name: /Create Case/i })
    await user.click(submitButtons[submitButtons.length - 1])

    await waitFor(() => {
      expect(mutateSpy).toHaveBeenCalledWith(
        expect.objectContaining({
          case_id: 'CASE-99',
          title: 'Network Investigation',
          lead_investigator: 'Alice',
        })
      )
      expect(screen.queryByText(/Create New Case/i)).not.toBeInTheDocument()
    })
  })

  it('filtert Cases anhand des Suchbegriffs', async () => {
    mockUseCases.mockReturnValue({
      data: {
        cases: [
          { case_id: 'CASE-1', title: 'Bridge Exploit', status: 'active', lead_investigator: 'Alice', created_at: '2025-10-10T00:00:00Z' },
          { case_id: 'CASE-2', title: 'Routine Check', status: 'active', lead_investigator: 'Bob', created_at: '2025-10-11T00:00:00Z' },
        ],
      },
      isLoading: false,
      error: null,
    })

    renderCasesPage()

    const user = userEvent.setup()
    const searchInput = screen.getByPlaceholderText(/Search cases/i)
    await user.type(searchInput, 'Bridge')

    await waitFor(() => {
      expect(screen.getByText(/Bridge Exploit/i)).toBeInTheDocument()
      expect(screen.queryByText(/Routine Check/i)).not.toBeInTheDocument()
    })
  })
})

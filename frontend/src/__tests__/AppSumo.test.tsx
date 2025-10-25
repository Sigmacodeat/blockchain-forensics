import { describe, it, beforeEach, afterEach, expect, vi } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter } from 'react-router-dom'

import AppSumoRedemption from '@/pages/AppSumoRedemption'
import MainDashboard from '@/pages/MainDashboard'
import AppSumoManager from '@/pages/admin/AppSumoManager'
import { AuthContext } from '@/contexts/AuthContext'

const apiMock = {
  post: vi.fn(),
  get: vi.fn(),
}

vi.mock('@/lib/api', () => ({
  __esModule: true,
  default: apiMock,
}))

const renderWithProviders = (ui: React.ReactNode, { user }:{ user: any }) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })

  return render(
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthContext.Provider value={{
          user,
          isAuthenticated: true,
          isLoading: false,
          login: vi.fn(),
          register: vi.fn(),
          logout: vi.fn(),
          refreshUser: vi.fn(),
        }}>
          {ui}
        </AuthContext.Provider>
      </BrowserRouter>
    </QueryClientProvider>
  )
}

describe('AppSumo Integration', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.resetAllMocks()
  })

  describe('Code Redemption Flow', () => {
    it('zeigt Formular zum Einlösen des Codes', () => {
      renderWithProviders(<AppSumoRedemption />, {
        user: { plan: 'community', role: 'viewer' },
      })

      expect(screen.getByText(/Redeem Your AppSumo Deal/i)).toBeInTheDocument()
      expect(screen.getByPlaceholderText(/CHAT-ABC123-XYZ789/i)).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /Validate Code/i })).toBeInTheDocument()
    })

    it('validiert Code-Format vor API-Aufruf', async () => {
      renderWithProviders(<AppSumoRedemption />, {
        user: { plan: 'community', role: 'viewer' },
      })

      fireEvent.change(screen.getByPlaceholderText(/CHAT-ABC123-XYZ789/i), { target: { value: 'invalid' } })
      fireEvent.click(screen.getByRole('button', { name: /Validate Code/i }))

      await waitFor(() => {
        expect(screen.getByText(/Invalid code/i)).toBeInTheDocument()
      })
      expect(apiMock.post).not.toHaveBeenCalled()
    })

    it('löst gültigen Code ein und zeigt Erfolg', async () => {
      apiMock.post.mockImplementation(async (url: string) => {
        if (url.endsWith('/validate-code')) {
          return { data: { product: 'chatbot', tier: 2 } }
        }
        if (url.endsWith('/redeem')) {
          return {
            data: {
              product: 'chatbot',
              tier: 2,
              user: { id: 'user-123', email: 'test@example.com' },
              access_token: 'token-abc',
            },
          }
        }
        throw new Error('unexpected URL')
      })

      renderWithProviders(<AppSumoRedemption />, {
        user: { plan: 'community', role: 'viewer' },
      })

      fireEvent.change(screen.getByPlaceholderText(/CHAT-ABC123-XYZ789/i), {
        target: { value: 'CHATBOT-2-ABC123XYZ' },
      })
      fireEvent.click(screen.getByRole('button', { name: /Validate Code/i }))

      await screen.findByRole('button', { name: /Create Account/i })

      fireEvent.change(screen.getByLabelText(/Email/i), { target: { value: 'john@example.com' } })
      fireEvent.change(screen.getByLabelText(/Password/i), { target: { value: 'password123' } })
      fireEvent.click(screen.getByRole('button', { name: /Create Account/i }))

      await waitFor(() => {
        expect(screen.getByText(/Code redeemed successfully/i)).toBeInTheDocument()
      })
    })
  })

  describe('Dashboard Products Section', () => {
    it('zeigt gekaufte AppSumo-Produkte des Users', async () => {
      apiMock.get.mockImplementation(async (url: string) => {
        if (url.endsWith('/appsumo/my-products')) {
          return {
            data: {
              products: [
                {
                  product: 'chatbot',
                  product_name: 'ChatBot Pro',
                  tier: 2,
                  activated_at: '2025-10-19T10:00:00Z',
                },
              ],
              count: 1,
            },
          }
        }
        return { data: {} }
      })

      renderWithProviders(<MainDashboard />, {
        user: { plan: 'community', role: 'viewer' },
      })

      await waitFor(() => {
        expect(screen.getByText(/My AppSumo Products/i)).toBeInTheDocument()
        expect(screen.getByText(/ChatBot Pro/i)).toBeInTheDocument()
        expect(screen.getByText(/Tier 2/i)).toBeInTheDocument()
      })
    })

    it('verbirgt Abschnitt, wenn keine Produkte vorhanden', async () => {
      apiMock.get.mockResolvedValueOnce({ data: { products: [], count: 0 } })

      renderWithProviders(<MainDashboard />, {
        user: { plan: 'community', role: 'viewer' },
      })

      await waitFor(() => {
        expect(screen.queryByText(/My AppSumo Products/i)).not.toBeInTheDocument()
      })
    })
  })

  describe('Admin Manager', () => {
    it('zeigt Code-Generator Formular an', () => {
      renderWithProviders(<AppSumoManager />, {
        user: { plan: 'business', role: 'admin' },
      })

      expect(screen.getByText(/AppSumo Manager/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/Product/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/Tier/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/Count/i)).toBeInTheDocument()
    })

    it('validiert Mengenbegrenzung', async () => {
      renderWithProviders(<AppSumoManager />, {
        user: { plan: 'business', role: 'admin' },
      })

      const countInput = screen.getByLabelText(/Count/i)
      fireEvent.change(countInput, { target: { value: '10000' } })

      await waitFor(() => {
        expect(screen.getByText(/maximum 1000 codes/i)).toBeInTheDocument()
      })
    })
  })
})

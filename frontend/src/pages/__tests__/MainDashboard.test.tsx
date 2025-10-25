import { describe, it, beforeEach, afterEach, expect, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter } from 'react-router-dom'

import MainDashboard from '../MainDashboard'
import type { User } from '@/lib/auth'

const apiGetMock = vi.fn()

const translations: Record<string, string> = {
  'dashboard.title': 'Forensics Dashboard',
  'dashboard.system_overview': 'Echtzeit-Überwachung & Analytics für Blockchain-Forensik',
  'dashboard.false_positive_rate': 'False Positive Rate',
  'dashboard.mttr': 'MTTR',
  'dashboard.sla_breach_rate': 'SLA Breach Rate',
  'dashboard.sanctions_hits': 'Sanctions Hits',
  'dashboard.transaction_tracing': 'Transaction Tracing',
  'dashboard.case_management': 'Case Management',
  'dashboard.alert_monitoring': 'Alert Monitoring',
  'dashboard.graph_explorer': 'Graph Explorer',
  'dashboard.correlation_analysis': 'Correlation Analysis',
  'common.refresh': 'Aktualisieren',
  'accessibility.skip_to_content': 'Skip to content',
  'dashboard.quick_access': 'Quick Access',
  // Add more as needed
}

vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string, fallback?: string) => translations[key] || fallback || key,
    i18n: {
      language: 'en',
      changeLanguage: vi.fn(),
    },
  }),
}))

vi.mock('@/hooks/useAccessibility', () => ({
  useAccessibility: () => ({ announceToScreenReader: vi.fn() }),
}))

const hasFeatureMock = vi.fn<(user: User | null, feature: string) => boolean>(() => true)

vi.mock('@/lib/features', () => ({
  hasFeature: (user: User | null, feature: string) => hasFeatureMock(user, feature),
}))

vi.mock('@/lib/api', () => ({
  __esModule: true,
  default: { get: (url: string, config?: unknown) => apiGetMock(url, config) },
}))

vi.mock('@/components/onboarding/OnboardingTour', () => ({
  OnboardingTour: () => null,
  OnboardingBanner: () => null,
}))

vi.mock('@/components/dashboard/LiveAlertsFeed', () => ({
  LiveAlertsFeed: () => <div data-testid="live-alerts" />,}) )

vi.mock('@/components/dashboard/TrendCharts', () => ({
  TrendCharts: () => <div data-testid="trend-charts">trend chart placeholder</div>,
}))

vi.mock('@/components/chat/InlineChatPanel', () => ({
  __esModule: true,
  default: () => null,
}))

vi.mock('@/hooks/useAuth', () => ({
  useAuth: () => ({
    user: { id: '1', email: 'user@example.com', plan: 'pro', role: 'user' },
    isAuthenticated: true,
  }),
}))

const buildQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  })

const renderDashboard = () =>
  render(
    <QueryClientProvider client={buildQueryClient()}>
      <BrowserRouter>
        <MainDashboard />
      </BrowserRouter>
    </QueryClientProvider>
  )

describe('MainDashboard', () => {
  beforeEach(() => {
    apiGetMock.mockImplementation((url: string) => {
      switch (url) {
        case '/api/v1/system/health':
          return Promise.resolve({
            data: {
              status: 'healthy',
              uptime: 3600,
              database: { connected: true, response_time: 12 },
              services: { alert_engine: true, graph_db: true, ml_service: true },
            },
          })
        case '/api/v1/alerts/kpis':
          return Promise.resolve({
            data: { fpr: 0.123, mttr: 1, sla_breach_rate: 0.05, sanctions_hits: 2 },
          })
        case '/api/v1/alerts/summary':
          return Promise.resolve({
            data: {
              total_alerts: 5,
              suppression_rate: 0.9,
              by_severity: { high: 3, medium: 2 },
              by_type: {},
              recent_alerts: [],
            },
          })
        case '/api/v1/cases/stats':
          return Promise.resolve({
            data: {
              total_cases: 7,
              by_status: { open: 4, closed: 3 },
              by_priority: { high: 2, medium: 3, low: 2 },
            },
          })
        case '/api/v1/graph-analytics/stats/network':
          return Promise.resolve({
            data: {
              total_nodes: 100,
              total_edges: 250,
              network_density: 0.1,
              communities_detected: 5,
              high_risk_clusters: 1,
            },
          })
        case '/api/v1/alerts/ops':
          return Promise.resolve({ data: { aging: { '24h': 1, '3d': 2, '7d': 0, '>7d': 0 } } })
        case '/api/v1/alerts/rules/effectiveness':
          return Promise.resolve({ data: [] })
        case '/api/v1/ml/models':
          return Promise.resolve({ data: [] })
        case '/api/v1/appsumo/my-products':
          return Promise.resolve({ data: { products: [], count: 0 } })
        default:
          return Promise.resolve({ data: {} })
      }
    })
    hasFeatureMock.mockImplementation(() => true)
  })

  afterEach(() => {
    vi.resetAllMocks()
    hasFeatureMock.mockReset()
  })

  it('rendert Titel und Live-Metriken', async () => {
    renderDashboard()

    expect(screen.getByText('Forensics Dashboard')).toBeInTheDocument()
    expect(screen.getByText('Total Transactions')).toBeInTheDocument()
    expect(screen.getByText('High Risk Addresses')).toBeInTheDocument()
    expect(screen.getByText('Active Cases')).toBeInTheDocument()

    expect(screen.getByText('1,234')).toBeInTheDocument()
    expect(screen.getByText('56')).toBeInTheDocument()
    expect(screen.getByText('12')).toBeInTheDocument()

    await waitFor(() => {
      expect(apiGetMock).toHaveBeenCalledWith('/api/v1/system/health', undefined)
    })
  })

  it('zeigt KPI-Karten mit Werten aus dem API-Mock', async () => {
    renderDashboard()

    await waitFor(() => {
      expect(screen.getByText('12%')).toBeInTheDocument()
    })

    expect(screen.getByText('1h')).toBeInTheDocument()
    expect(screen.getByText('5%')).toBeInTheDocument()
    expect(screen.getByText('2')).toBeInTheDocument()
  })

  it('beinhaltet Trend-Analytics-Abschnitt, wenn Feature aktiviert ist', async () => {
    hasFeatureMock.mockReturnValueOnce(true)
    renderDashboard()

    await waitFor(() => {
      expect(screen.getByTestId('trend-charts')).toBeInTheDocument()
    })
  })

  it('versteckt Trend-Analytics ohne Feature-Gate', async () => {
    hasFeatureMock.mockReturnValue(false)
    renderDashboard()

    await waitFor(() => {
      expect(screen.queryByTestId('trend-charts')).not.toBeInTheDocument()
    })
  })

  describe('Quick Actions', () => {
    it('zeigt generelle Schnellzugriffe', async () => {
      renderDashboard()

      expect(screen.getAllByText(translations['dashboard.transaction_tracing']).length).toBeGreaterThan(0)
      expect(screen.getAllByText(translations['dashboard.case_management']).length).toBeGreaterThan(0)
      expect(screen.getAllByText(translations['dashboard.alert_monitoring']).length).toBeGreaterThan(0)
    })

    it('blendet planabhängige Aktionen ohne Feature aus', async () => {
      hasFeatureMock.mockImplementation((_user, feature) => feature === 'analytics.trends')
      renderDashboard()

      expect(screen.queryByText(translations['dashboard.graph_explorer'])).not.toBeInTheDocument()
      expect(screen.queryByText('AI Agent')).not.toBeInTheDocument()
      expect(screen.queryByText(translations['dashboard.correlation_analysis'])).not.toBeInTheDocument()
    })

    it('zeigt planabhängige Aktionen bei aktivem Feature', async () => {
      hasFeatureMock.mockImplementation((_user, feature) => feature !== 'unused')
      renderDashboard()

      expect(screen.getAllByText(translations['dashboard.graph_explorer']).length).toBeGreaterThan(0)
      expect(screen.getAllByText('AI Agent').length).toBeGreaterThan(0)
      expect(screen.getAllByText(translations['dashboard.correlation_analysis']).length).toBeGreaterThan(0)
    })
  })

  it('ermöglicht Aktualisierungsschaltfläche', async () => {
    renderDashboard()

    const user = userEvent.setup()
    const refreshButton = screen.getByRole('button', { name: /Aktualisieren/i })
    expect(refreshButton).toBeInTheDocument()

    await user.click(refreshButton)

    await waitFor(() => {
      expect(apiGetMock).toHaveBeenCalledWith('/api/v1/system/health', undefined)
    })
  })
})

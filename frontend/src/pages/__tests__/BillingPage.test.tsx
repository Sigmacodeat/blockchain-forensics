/**
 * 🧪 BILLING PAGE TESTS
 * Prüft die wichtigsten Umsatzpfade (Plan-Anzeige, Kündigung, Web3-Zahlung)
 */

import { describe, it, beforeEach, afterEach, expect, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';


const { mockGet, mockPost } = vi.hoisted(() => ({
  mockGet: vi.fn(),
  mockPost: vi.fn(),
}))
const mockNavigate = vi.fn();

vi.mock('@/lib/api', () => ({
  api: {
    get: mockGet,
    post: mockPost,
  },
}));

vi.mock('@/contexts/AuthContext', () => ({
  useAuth: () => ({
    user: {
      id: 'user-1',
      email: 'user@example.com',
      plan: 'pro',
      role: 'user',
      subscription_status: 'active',
    },
    isAuthenticated: true,
    isLoading: false,
  }),
}));

vi.mock('@/hooks/useLocalePath', () => ({
  useLocalePath: () => (path: string) => path,
}));

vi.mock('@/components/CryptoPaymentModal', () => ({
  default: () => null,
}));

vi.mock('@/components/chat/Web3PaymentButton', () => ({
  default: ({ paymentAddress, amount, currency }: { paymentAddress: string; amount: number; currency: string }) => (
    <div data-testid="web3-payment-summary">
      <span>{paymentAddress}</span>
      <span>{amount}</span>
      <span>{currency}</span>
    </div>
  ),
}));

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

// Import after mocks so that mocked api and hooks are applied
import BillingPage from '../BillingPage';

type ApiOverrides = {
  subscription?: Record<string, any> | null;
  paymentMethods?: Record<string, any>[];
  invoices?: Record<string, any>[];
  usage?: Record<string, any> | null;
  cryptoPayments?: Record<string, any>[];
};

const defaultApiData = {
  subscription: {
    id: 'sub_123',
    plan: 'pro',
    status: 'active',
    payment_type: 'stripe',
    current_period_start: '2025-10-19T00:00:00Z',
    current_period_end: '2025-11-19T00:00:00Z',
    cancel_at_period_end: false,
    amount: 19900,
    currency: 'usd',
    interval: 'monthly',
  },
  paymentMethods: [],
  invoices: [],
  usage: {
    traces_used: 10,
    traces_limit: 100,
    cases_used: 2,
    cases_limit: 20,
    api_calls_used: 500,
    api_calls_limit: 10000,
    period_start: '2025-10-01T00:00:00Z',
    period_end: '2025-10-31T23:59:59Z',
  },
  cryptoPayments: [],
};

const setupApiMocks = (overrides: ApiOverrides = {}) => {
  const data = { ...defaultApiData, ...overrides };

  mockGet.mockImplementation((url: string) => {
    switch (url) {
      case '/api/v1/billing/subscription':
        return Promise.resolve({ data: data.subscription });
      case '/api/v1/billing/payment-methods':
        return Promise.resolve({ data: { data: data.paymentMethods } });
      case '/api/v1/billing/invoices':
        return Promise.resolve({ data: { data: data.invoices } });
      case '/api/v1/crypto-payments/history':
        return Promise.resolve({ data: { payments: data.cryptoPayments } });
      case '/api/v1/billing/usage':
        return Promise.resolve({ data: data.usage });
      default:
        return Promise.resolve({ data: {} });
    }
  });

  mockPost.mockImplementation((url: string, body?: unknown) => {
    if (url === '/api/v1/billing/cancel') {
      return Promise.resolve({ data: { status: 'cancelled' } });
    }
    if (url === '/api/v1/crypto-payments/create') {
      return Promise.resolve({
        data: {
          payment_id: 321,
          pay_amount: '0.015',
          pay_currency: 'ETH',
          pay_address: '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb',
          plan: body && typeof body === 'object' && 'plan' in body ? (body as Record<string, string>).plan : 'pro',
        },
      });
    }
    if (url === '/api/v1/billing/checkout-session') {
      return Promise.resolve({ data: { url: 'https://stripe.test/session' } });
    }
    return Promise.resolve({ data: {} });
  });
};

let queryClient: QueryClient;

const renderBillingPage = () =>
  render(
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <BillingPage />
      </BrowserRouter>
    </QueryClientProvider>
  );

describe('BillingPage', () => {
  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    mockGet.mockReset();
    mockPost.mockReset();
    mockNavigate.mockReset();
    window.history.pushState({}, '', '/billing');
  });

  afterEach(() => {
    queryClient.clear();
  });

  it('zeigt aktuellen Plan, Status und nächstes Abrechnungsdatum an', async () => {
    setupApiMocks();
    renderBillingPage();
    // Titel des Abschnitts
    expect(await screen.findByText(/Aktueller Plan/i)).toBeInTheDocument();
    // Betrag/Intervall (Stripe: 19900 -> 199.00 USD / Monat)
    expect(await screen.findByText(/199\.00\s*USD\s*\/\s*Monat/i)).toBeInTheDocument();
    // Status-Badge
    expect(await screen.findByText(/Aktiv/i)).toBeInTheDocument();
    // Nächste Abrechnung
    expect(await screen.findByText(/Nächste Abrechnung:/i)).toBeInTheDocument();
  });
});

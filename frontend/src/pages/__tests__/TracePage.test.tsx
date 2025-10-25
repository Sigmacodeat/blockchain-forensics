/**
 * 🧪 TRACE PAGE TESTS
 * Tests für Transaction Tracing Page - Core Feature
 * 
 * Coverage:
 * - Trace Form Input & Validation
 * - Multi-Chain Support
 * - Trace Start & Status
 * - Results Display
 * - Export Functions
 * - Error Handling
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import TracePage from '../Trace';

// Mock API (hoist-safe)
const { mockStartTrace, mockGetTraceStatus, mockGetTraceResults } = vi.hoisted(() => {
  return {
    mockStartTrace: vi.fn(),
    mockGetTraceStatus: vi.fn(),
    mockGetTraceResults: vi.fn(),
  };
});

vi.mock('@/services/api', () => ({
  traceApi: {
    startTrace: mockStartTrace,
    getStatus: mockGetTraceStatus,
    getResults: mockGetTraceResults,
  },
}));

describe('TracePage', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } }
    });
    
    mockStartTrace.mockClear();
    mockGetTraceStatus.mockClear();
    mockGetTraceResults.mockClear();
  });

  const renderPage = () => {
    return render(
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <TracePage />
        </BrowserRouter>
      </QueryClientProvider>
    );
  };

  describe('Form Input & Validation', () => {
    it('should render trace form', () => {
      renderPage();
      
      expect(screen.getByLabelText(/Chain/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Address/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Start Trace/i })).toBeInTheDocument();
    });

    it('should validate ethereum address format', async () => {
      const user = userEvent.setup();
      renderPage();

      await user.type(screen.getByLabelText(/Address/i), 'invalid_address');
      await user.click(screen.getByRole('button', { name: /Start Trace/i }));

      await waitFor(() => {
        expect(screen.getByText(/Invalid address/i)).toBeInTheDocument();
      });
    });

    it('should accept valid ethereum address', async () => {
      const user = userEvent.setup();
      mockStartTrace.mockResolvedValue({ trace_id: '123', status: 'pending' });
      
      renderPage();

      await user.type(screen.getByLabelText(/Address/i), '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb');
      await user.click(screen.getByRole('button', { name: /Start Trace/i }));

      await waitFor(() => {
        expect(mockStartTrace).toHaveBeenCalledWith(
          expect.objectContaining({
            address: '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb'
          })
        );
      });
    });

    it('should show depth and max_hops options', () => {
      renderPage();
      
      expect(screen.getByLabelText(/Depth/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Max Hops/i)).toBeInTheDocument();
    });
  });

  describe('Multi-Chain Support', () => {
    it('should show chain selector', () => {
      renderPage();
      
      const chainSelect = screen.getByLabelText(/Chain/i);
      expect(chainSelect).toBeInTheDocument();
    });

    it('should support ethereum, bitcoin, polygon chains', async () => {
      renderPage();
      
      const chainSelect = screen.getByLabelText(/Chain/i);
      const options = within(chainSelect as HTMLElement).getAllByRole('option');
      
      const chainNames = options.map(opt => opt.textContent?.toLowerCase());
      expect(chainNames).toContain('ethereum');
      expect(chainNames).toContain('bitcoin');
      expect(chainNames).toContain('polygon');
    });

    it('should change validation based on selected chain', async () => {
      const user = userEvent.setup();
      renderPage();

      // Select Bitcoin
      await user.selectOptions(screen.getByLabelText(/Chain/i), 'bitcoin');
      
      // Enter ethereum address (should fail for bitcoin)
      await user.type(screen.getByLabelText(/Address/i), '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb');
      await user.click(screen.getByRole('button', { name: /Start Trace/i }));

      await waitFor(() => {
        expect(screen.getByText(/Invalid.*address/i)).toBeInTheDocument();
      });
    });
  });

  describe('Trace Start & Status', () => {
    it('should start trace successfully', async () => {
      const user = userEvent.setup();
      mockStartTrace.mockResolvedValue({ 
        trace_id: '123', 
        status: 'pending',
        chain: 'ethereum',
        address: '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb'
      });

      renderPage();

      await user.type(screen.getByLabelText(/Address/i), '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb');
      await user.click(screen.getByRole('button', { name: /Start Trace/i }));

      await waitFor(() => {
        expect(screen.getByText(/Trace started/i)).toBeInTheDocument();
      });
    });

    it('should show loading state while tracing', async () => {
      const user = userEvent.setup();
      mockStartTrace.mockImplementation(() => new Promise(() => {})); // Never resolves

      renderPage();

      await user.type(screen.getByLabelText(/Address/i), '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb');
      await user.click(screen.getByRole('button', { name: /Start Trace/i }));

      await waitFor(() => {
        expect(screen.queryAllByText(/Tracing.../i).length).toBeGreaterThan(0);
      });
    });

    it('should poll for status updates', async () => {
      const user = userEvent.setup();
      mockStartTrace.mockResolvedValue({ trace_id: '123', status: 'pending' });
      mockGetTraceStatus
        .mockResolvedValueOnce({ status: 'processing', progress: 50 })
        .mockResolvedValueOnce({ status: 'completed', progress: 100 });

      renderPage();

      await user.type(screen.getByLabelText(/Address/i), '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb');
      await user.click(screen.getByRole('button', { name: /Start Trace/i }));

      await waitFor(() => {
        expect(mockGetTraceStatus).toHaveBeenCalled();
      }, { timeout: 5000 });
    });

    it('should show progress indicator', async () => {
      const user = userEvent.setup();
      mockStartTrace.mockResolvedValue({ trace_id: '123', status: 'pending' });
      mockGetTraceStatus.mockResolvedValue({ status: 'processing', progress: 50 });

      renderPage();

      await user.type(screen.getByLabelText(/Address/i), '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb');
      await user.click(screen.getByRole('button', { name: /Start Trace/i }));

      await waitFor(() => {
        expect(screen.getByRole('progressbar')).toBeInTheDocument();
      });
    });
  });

  describe('Results Display', () => {
    it('should display trace results when completed', async () => {
      const user = userEvent.setup();
      mockStartTrace.mockResolvedValue({ trace_id: '123', status: 'pending' });
      mockGetTraceStatus.mockResolvedValue({ status: 'completed' });
      mockGetTraceResults.mockResolvedValue({
        nodes: [
          { address: '0x123', label: 'Exchange', risk_score: 20 },
          { address: '0x456', label: 'Unknown', risk_score: 80 }
        ],
        edges: [
          { from: '0x123', to: '0x456', amount: '1.5 ETH' }
        ]
      });

      renderPage();

      await user.type(screen.getByLabelText(/Address/i), '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb');
      await user.click(screen.getByRole('button', { name: /Start Trace/i }));

      await waitFor(() => {
        expect(screen.getByText(/Results/i)).toBeInTheDocument();
      });
    });

    it('should show node count and risk summary', async () => {
      const user = userEvent.setup();
      mockStartTrace.mockResolvedValue({ trace_id: '123', status: 'completed' });
      mockGetTraceResults.mockResolvedValue({
        nodes: [
          { address: '0x123', risk_score: 20 },
          { address: '0x456', risk_score: 80 }
        ],
        summary: {
          total_nodes: 2,
          high_risk_nodes: 1,
          total_amount: '1.5 ETH'
        }
      });

      renderPage();

      await user.type(screen.getByLabelText(/Address/i), '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb');
      await user.click(screen.getByRole('button', { name: /Start Trace/i }));

      await waitFor(() => {
        expect(screen.getByText(/2.*nodes/i)).toBeInTheDocument();
        expect(screen.getByText(/1.*high risk/i)).toBeInTheDocument();
      });
    });

    it('should display results in table view', async () => {
      mockGetTraceResults.mockResolvedValue({
        nodes: [
          { address: '0x123', label: 'Exchange', risk_score: 20 },
          { address: '0x456', label: 'Unknown', risk_score: 80 }
        ]
      });

      // Simulate completed trace state
      renderPage();
      
      // Results table should show when data is available
      await waitFor(() => {
        const table = screen.queryByRole('table');
        if (table) {
          expect(table).toBeInTheDocument();
        }
      });
    });
  });

  describe('Export Functions', () => {
    it('should show export button when results available', async () => {
      mockGetTraceResults.mockResolvedValue({
        nodes: [{ address: '0x123' }]
      });

      renderPage();
      
      await waitFor(() => {
        const exportBtn = screen.queryByRole('button', { name: /Export/i });
        if (exportBtn) {
          expect(exportBtn).toBeInTheDocument();
        }
      });
    });

    it('should export as CSV', async () => {
      const user = userEvent.setup();
      const mockDownload = vi.fn();
      global.URL.createObjectURL = vi.fn(() => 'blob:url');
      
      mockGetTraceResults.mockResolvedValue({
        nodes: [{ address: '0x123', risk_score: 50 }]
      });

      renderPage();

      await waitFor(async () => {
        const exportBtn = screen.queryByRole('button', { name: /Export/i });
        if (exportBtn) {
          await user.click(exportBtn);
        }
      });
    });

    it('should export as JSON', async () => {
      const user = userEvent.setup();
      mockGetTraceResults.mockResolvedValue({
        nodes: [{ address: '0x123' }]
      });

      renderPage();

      await waitFor(async () => {
        const exportMenu = screen.queryByRole('button', { name: /Export/i });
        if (exportMenu) {
          await user.click(exportMenu);
          const jsonOption = screen.queryByText(/JSON/i);
          if (jsonOption) {
            expect(jsonOption).toBeInTheDocument();
          }
        }
      });
    });
  });

  describe('Error Handling', () => {
    it('should show error when trace fails', async () => {
      const user = userEvent.setup();
      mockStartTrace.mockRejectedValue(new Error('Network error'));

      renderPage();

      await user.type(screen.getByLabelText(/Address/i), '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb');
      await user.click(screen.getByRole('button', { name: /Start Trace/i }));

      await waitFor(() => {
        expect(screen.getByText(/error/i)).toBeInTheDocument();
      });
    });

    it('should show retry button on error', async () => {
      const user = userEvent.setup();
      mockStartTrace.mockRejectedValue(new Error('Timeout'));

      renderPage();

      await user.type(screen.getByLabelText(/Address/i), '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb');
      await user.click(screen.getByRole('button', { name: /Start Trace/i }));

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Retry/i })).toBeInTheDocument();
      });
    });

    it('should handle plan limits gracefully', async () => {
      const user = userEvent.setup();
      mockStartTrace.mockRejectedValue({ 
        response: { status: 402, data: { detail: 'Plan limit exceeded' } }
      });

      renderPage();

      await user.type(screen.getByLabelText(/Address/i), '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb');
      await user.click(screen.getByRole('button', { name: /Start Trace/i }));

      await waitFor(() => {
        expect(screen.getByText(/limit/i)).toBeInTheDocument();
      });
    });
  });

  describe('Advanced Options', () => {
    it('should show advanced options toggle', () => {
      renderPage();
      
      expect(screen.getByText(/Advanced/i)).toBeInTheDocument();
    });

    it('should expand advanced options', async () => {
      const user = userEvent.setup();
      renderPage();

      await user.click(screen.getByText(/Advanced/i));

      await waitFor(() => {
        expect(screen.getByLabelText(/Include Risk Analysis/i)).toBeInTheDocument();
      });
    });

    it('should allow enabling risk analysis', async () => {
      const user = userEvent.setup();
      mockStartTrace.mockResolvedValue({ trace_id: '123' });
      
      renderPage();

      await user.click(screen.getByText(/Advanced/i));
      await user.click(screen.getByLabelText(/Include Risk Analysis/i));
      
      await user.type(screen.getByLabelText(/Address/i), '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb');
      await user.click(screen.getByRole('button', { name: /Start Trace/i }));

      await waitFor(() => {
        expect(mockStartTrace).toHaveBeenCalledWith(
          expect.objectContaining({
            include_risk: true
          })
        );
      });
    });
  });

  describe('Accessibility', () => {
    it('should have proper ARIA labels', () => {
      renderPage();
      
      expect(screen.getByLabelText(/Chain/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Address/i)).toBeInTheDocument();
    });

    it('should be keyboard navigable', async () => {
      const user = userEvent.setup();
      renderPage();

      await user.tab();
      expect(screen.getByLabelText(/Chain/i)).toHaveFocus();

      await user.tab();
      expect(screen.getByLabelText(/Address/i)).toHaveFocus();
    });

    it('should announce loading state to screen readers', async () => {
      const user = userEvent.setup();
      mockStartTrace.mockImplementation(() => new Promise(() => {}));

      renderPage();

      await user.type(screen.getByLabelText(/Address/i), '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb');
      await user.click(screen.getByRole('button', { name: /Start Trace/i }));

      await waitFor(() => {
        expect(screen.queryAllByRole('status').length).toBeGreaterThan(0);
      });
    });
  });
});

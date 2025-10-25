import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { NodeDetailsPanel } from '../NodeDetailsPanel';

vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string, defaultValue: string) => defaultValue,
  }),
}));

vi.mock('@/components/RiskCopilot', () => ({
  RiskCopilot: () => <div data-testid="risk-copilot">Risk Copilot</div>,
}));

describe('NodeDetailsPanel', () => {
  const mockNode = {
    id: '0xabc123',
    address: '0xabc123',
    chain: 'ethereum',
    taint_score: 0.65,
    risk_level: 'HIGH',
    labels: ['Exchange', 'Mixer'],
    tx_count: 150,
    balance: 5.2,
    first_seen: '2024-01-01',
    last_seen: '2025-01-15',
  };

  const mockGraphControls = {
    zoomIn: vi.fn(),
    zoomOut: vi.fn(),
    zoomToFit: vi.fn(),
    centerOn: vi.fn(),
  };

  it('renders node address', () => {
    render(
      <NodeDetailsPanel
        selectedAddress="0xabc123"
        node={mockNode}
        graphControls={mockGraphControls}
        onPatternDetect={vi.fn()}
        onAiTracePath={vi.fn()}
        onAiMonitor={vi.fn()}
        onFindPath={vi.fn()}
        patternsPending={false}
      />
    );
    
    expect(screen.getByText('0xabc123')).toBeInTheDocument();
  });

  it('displays risk level badge', () => {
    render(
      <NodeDetailsPanel
        selectedAddress="0xabc123"
        node={mockNode}
        graphControls={mockGraphControls}
        onPatternDetect={vi.fn()}
        onAiTracePath={vi.fn()}
        onAiMonitor={vi.fn()}
        onFindPath={vi.fn()}
        patternsPending={false}
      />
    );
    
    expect(screen.getByText('HIGH')).toBeInTheDocument();
    expect(screen.getByText('(65.0%)')).toBeInTheDocument();
  });

  it('displays transaction count', () => {
    render(
      <NodeDetailsPanel
        selectedAddress="0xabc123"
        node={mockNode}
        graphControls={mockGraphControls}
        onPatternDetect={vi.fn()}
        onAiTracePath={vi.fn()}
        onAiMonitor={vi.fn()}
        onFindPath={vi.fn()}
        patternsPending={false}
      />
    );
    
    expect(screen.getByText('150')).toBeInTheDocument();
  });

  it('displays labels', () => {
    render(
      <NodeDetailsPanel
        selectedAddress="0xabc123"
        node={mockNode}
        graphControls={mockGraphControls}
        onPatternDetect={vi.fn()}
        onAiTracePath={vi.fn()}
        onAiMonitor={vi.fn()}
        onFindPath={vi.fn()}
        patternsPending={false}
      />
    );
    
    expect(screen.getByText('Exchange')).toBeInTheDocument();
    expect(screen.getByText('Mixer')).toBeInTheDocument();
  });

  it('calls onPatternDetect when clicking Patterns button', () => {
    const mockOnPatternDetect = vi.fn();
    render(
      <NodeDetailsPanel
        selectedAddress="0xabc123"
        node={mockNode}
        graphControls={mockGraphControls}
        onPatternDetect={mockOnPatternDetect}
        onAiTracePath={vi.fn()}
        onAiMonitor={vi.fn()}
        onFindPath={vi.fn()}
        patternsPending={false}
      />
    );
    
    const button = screen.getByText('Patterns');
    fireEvent.click(button);
    
    expect(mockOnPatternDetect).toHaveBeenCalledTimes(1);
  });

  it('disables Patterns button when pending', () => {
    render(
      <NodeDetailsPanel
        selectedAddress="0xabc123"
        node={mockNode}
        graphControls={mockGraphControls}
        onPatternDetect={vi.fn()}
        onAiTracePath={vi.fn()}
        onAiMonitor={vi.fn()}
        onFindPath={vi.fn()}
        patternsPending={true}
      />
    );
    
    const button = screen.getByText('Detecting…');
    expect(button).toBeDisabled();
  });

  it('renders RiskCopilot component', () => {
    render(
      <NodeDetailsPanel
        selectedAddress="0xabc123"
        node={mockNode}
        graphControls={mockGraphControls}
        onPatternDetect={vi.fn()}
        onAiTracePath={vi.fn()}
        onAiMonitor={vi.fn()}
        onFindPath={vi.fn()}
        patternsPending={false}
      />
    );
    
    expect(screen.getByTestId('risk-copilot')).toBeInTheDocument();
  });

  it('calls Copy when clicking copy button', () => {
    Object.assign(navigator, {
      clipboard: {
        writeText: vi.fn(),
      },
    });

    render(
      <NodeDetailsPanel
        selectedAddress="0xabc123"
        node={mockNode}
        graphControls={mockGraphControls}
        onPatternDetect={vi.fn()}
        onAiTracePath={vi.fn()}
        onAiMonitor={vi.fn()}
        onFindPath={vi.fn()}
        patternsPending={false}
      />
    );
    
    const copyButton = screen.getByText('Copy');
    fireEvent.click(copyButton);
    
    expect(navigator.clipboard.writeText).toHaveBeenCalledWith('0xabc123');
  });
});

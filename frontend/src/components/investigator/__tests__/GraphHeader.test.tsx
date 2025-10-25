import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { GraphHeader } from '../GraphHeader';

// Mock i18next
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string, defaultValue: string) => defaultValue,
  }),
}));

describe('GraphHeader', () => {
  it('renders header title and subtitle', () => {
    render(<GraphHeader localGraph={null} timelineEvents={[]} />);
    
    expect(screen.getByText('Investigator Graph Explorer')).toBeInTheDocument();
    expect(screen.getByText('Interaktive Graph-Exploration mit Pfadsuche und Timeline-Analyse')).toBeInTheDocument();
  });

  it('displays stats when localGraph is provided', () => {
    const mockGraph = {
      nodes: {
        '0xabc': { id: '0xabc', address: '0xabc', chain: 'ethereum', taint_score: 0.5, risk_level: 'MEDIUM', labels: [], tx_count: 10, balance: 1.5, first_seen: '', last_seen: '' },
        '0xdef': { id: '0xdef', address: '0xdef', chain: 'ethereum', taint_score: 0.2, risk_level: 'LOW', labels: [], tx_count: 5, balance: 0.8, first_seen: '', last_seen: '' },
      },
      links: [
        { source: '0xabc', target: '0xdef', tx_hash: '0x123', value: 1, timestamp: '', event_type: 'transaction' },
      ],
    };

    render(<GraphHeader localGraph={mockGraph} timelineEvents={[]} />);
    
    expect(screen.getByText('2')).toBeInTheDocument(); // 2 Nodes
    expect(screen.getByText('Nodes')).toBeInTheDocument();
    expect(screen.getByText('1')).toBeInTheDocument(); // 1 Connection
    expect(screen.getByText('Connections')).toBeInTheDocument();
  });

  it('displays timeline events count when provided', () => {
    const mockGraph = {
      nodes: { '0xabc': { id: '0xabc', address: '0xabc', chain: 'ethereum', taint_score: 0, risk_level: 'LOW', labels: [], tx_count: 0, balance: 0, first_seen: '', last_seen: '' } },
      links: [],
    };
    const mockEvents = [
      { timestamp: '2025-01-01', address: '0xabc', event_type: 'transfer', value: 1, tx_hash: '0x123', risk_score: 50 },
      { timestamp: '2025-01-02', address: '0xabc', event_type: 'transfer', value: 2, tx_hash: '0x456', risk_score: 30 },
    ];

    render(<GraphHeader localGraph={mockGraph} timelineEvents={mockEvents} />);
    
    expect(screen.getByText('2')).toBeInTheDocument();
    expect(screen.getByText('Events')).toBeInTheDocument();
  });

  it('does not display stats when localGraph is null', () => {
    render(<GraphHeader localGraph={null} timelineEvents={[]} />);
    
    expect(screen.queryByText('Nodes')).not.toBeInTheDocument();
    expect(screen.queryByText('Connections')).not.toBeInTheDocument();
  });
});

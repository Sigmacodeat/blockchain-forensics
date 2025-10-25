import { describe, bench, vi } from 'vitest';
import { render } from '@testing-library/react';
import React from 'react';
import { GraphHeader } from '../GraphHeader';
import { AddressSearchPanel } from '../AddressSearchPanel';
import { GraphSettingsPanel } from '../GraphSettingsPanel';
import { NodeDetailsPanel } from '../NodeDetailsPanel';
import { PatternFindings } from '../PatternFindings';
import { TimelinePanel } from '../TimelinePanel';
import type { LocalGraph, GraphNode, TimelineEvent } from '../types';

// Mock i18next
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string, defaultValue: string) => defaultValue,
  }),
}));

vi.mock('@/components/RiskCopilot', () => ({
  RiskCopilot: () => React.createElement('div', null, 'Risk Copilot'),
}));

// Generate large mock data
const generateLargeGraph = (nodeCount: number): LocalGraph => ({
  nodes: Object.fromEntries(
    Array.from({ length: nodeCount }, (_, i) => [
      `0x${i}`,
      {
        id: `0x${i}`,
        address: `0x${i}`,
        chain: 'ethereum',
        taint_score: Math.random(),
        risk_level: ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'][Math.floor(Math.random() * 4)],
        labels: Math.random() > 0.5 ? ['Label1', 'Label2'] : [],
        tx_count: Math.floor(Math.random() * 1000),
        balance: Math.random() * 100,
        first_seen: '2024-01-01',
        last_seen: '2025-01-15',
      } as GraphNode,
    ])
  ),
  links: Array.from({ length: nodeCount * 2 }, (_, i) => ({
    source: `0x${Math.floor(Math.random() * nodeCount)}`,
    target: `0x${Math.floor(Math.random() * nodeCount)}`,
    tx_hash: `0x${i}`,
    value: Math.random() * 10,
    timestamp: '2025-01-01',
    event_type: 'transaction',
  })),
});

const generateTimelineEvents = (count: number): TimelineEvent[] =>
  Array.from({ length: count }, (_, i) => ({
    timestamp: `2025-01-${String((i % 30) + 1).padStart(2, '0')}T10:00:00Z`,
    address: `0x${Math.floor(Math.random() * 50)}`,
    event_type: ['transfer', 'swap', 'approval'][Math.floor(Math.random() * 3)],
    value: Math.random() * 10,
    tx_hash: `0x${i}`,
    risk_score: Math.floor(Math.random() * 100),
  }));

describe('Investigator Components Performance', () => {
  bench('GraphHeader with 10 nodes', () => {
    const graph = generateLargeGraph(10);
    render(React.createElement(GraphHeader, { localGraph: graph, timelineEvents: [] }));
  });

  bench('GraphHeader with 100 nodes', () => {
    const graph = generateLargeGraph(100);
    render(React.createElement(GraphHeader, { localGraph: graph, timelineEvents: [] }));
  });

  bench('GraphHeader with 1000 nodes', () => {
    const graph = generateLargeGraph(1000);
    render(React.createElement(GraphHeader, { localGraph: graph, timelineEvents: [] }));
  });

  bench('AddressSearchPanel render', () => {
    render(
      React.createElement(AddressSearchPanel, {
        searchQuery: '0xabc123',
        onSearchQueryChange: () => {},
        onSearch: () => {},
      })
    );
  });

  bench('GraphSettingsPanel render', () => {
    render(
      React.createElement(GraphSettingsPanel, {
        maxHops: 3,
        onMaxHopsChange: () => {},
        includeBridges: true,
        onIncludeBridgesChange: () => {},
        timeRange: { from: '', to: '' },
        onTimeRangeChange: () => {},
        minTaint: 0,
        onMinTaintChange: () => {},
      })
    );
  });

  bench('NodeDetailsPanel render', () => {
    const mockNode: GraphNode = {
      id: '0xabc123',
      address: '0xabc123',
      chain: 'ethereum',
      taint_score: 0.65,
      risk_level: 'HIGH',
      labels: ['Exchange', 'Mixer', 'High Risk'],
      tx_count: 150,
      balance: 5.2,
      first_seen: '2024-01-01',
      last_seen: '2025-01-15',
    };

    render(
      React.createElement(NodeDetailsPanel, {
        selectedAddress: '0xabc123',
        node: mockNode,
        graphControls: null,
        onPatternDetect: () => {},
        onAiTracePath: () => {},
        onAiMonitor: () => {},
        onFindPath: () => {},
        patternsPending: false,
      })
    );
  });

  bench('PatternFindings with 5 patterns', () => {
    const findings = Array.from({ length: 5 }, (_, i) => ({
      pattern: `Pattern ${i}`,
      score: Math.random(),
      explanation: 'Explanation text',
      evidence: Array.from({ length: 5 }, (_, j) => ({
        tx_hash: `0x${j}`,
        amount: Math.random() * 10,
        timestamp: '2025-01-01T10:00:00Z',
      })),
    }));

    render(React.createElement(PatternFindings, { findings, onOpenTx: () => {} }));
  });

  bench('TimelinePanel with 20 events', () => {
    const events = generateTimelineEvents(20);
    render(React.createElement(TimelinePanel, { events, onExportCSV: () => {} }));
  });

  bench('TimelinePanel with 100 events', () => {
    const events = generateTimelineEvents(100);
    render(React.createElement(TimelinePanel, { events, onExportCSV: () => {} }));
  });
});

describe('Data Processing Performance', () => {
  bench('Filter graph with 100 nodes (50% filtered)', () => {
    const graph = generateLargeGraph(100);
    const minTaint = 50;

    Object.entries(graph.nodes).reduce((acc, [addr, node]) => {
      const pct = node.taint_score * 100;
      if (pct >= minTaint) {
        acc[addr] = node;
      }
      return acc;
    }, {} as Record<string, GraphNode>);
  });

  bench('Calculate network metrics for 100 nodes', () => {
    const graph = generateLargeGraph(100);
    const nodeCount = Object.keys(graph.nodes).length;
    const linkCount = graph.links.length;
    const maxPossibleLinks = (nodeCount * (nodeCount - 1)) / 2;
    const density = maxPossibleLinks > 0 ? (linkCount / maxPossibleLinks) * 100 : 0;

    Object.entries(graph.nodes)
      .filter(([_, node]) => node.risk_level === 'HIGH' || node.risk_level === 'CRITICAL')
      .slice(0, 5);
  });

  bench('Sort timeline events (100 events)', () => {
    const events = generateTimelineEvents(100);
    events.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
  });

  bench('Export timeline to CSV (100 events)', () => {
    const events = generateTimelineEvents(100);
    const headers = ['timestamp', 'address', 'event_type', 'value', 'tx_hash', 'risk_score'];
    const rows = events.map((e) => [
      e.timestamp,
      e.address,
      e.event_type,
      String(e.value),
      e.tx_hash,
      String(e.risk_score),
    ]);
    [headers, ...rows]
      .map((r) => r.map((v) => String(v).replace(/"/g, '""')).join(','))
      .join('\n');
  });
});

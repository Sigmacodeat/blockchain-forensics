import type { Meta, StoryObj } from '@storybook/react';
import { GraphHeader } from './GraphHeader';

const meta = {
  title: 'Investigator/GraphHeader',
  component: GraphHeader,
  parameters: {
    layout: 'fullscreen',
  },
  tags: ['autodocs'],
} satisfies Meta<typeof GraphHeader>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Empty: Story = {
  args: {
    localGraph: null,
    timelineEvents: [],
  },
};

export const WithGraph: Story = {
  args: {
    localGraph: {
      nodes: {
        '0xabc': {
          id: '0xabc',
          address: '0xabc',
          chain: 'ethereum',
          taint_score: 0.5,
          risk_level: 'MEDIUM',
          labels: ['Exchange'],
          tx_count: 10,
          balance: 1.5,
          first_seen: '2024-01-01',
          last_seen: '2025-01-15',
        },
        '0xdef': {
          id: '0xdef',
          address: '0xdef',
          chain: 'ethereum',
          taint_score: 0.2,
          risk_level: 'LOW',
          labels: [],
          tx_count: 5,
          balance: 0.8,
          first_seen: '2024-06-01',
          last_seen: '2025-01-10',
        },
      },
      links: [
        {
          source: '0xabc',
          target: '0xdef',
          tx_hash: '0x123',
          value: 1,
          timestamp: '2025-01-01',
          event_type: 'transaction',
        },
      ],
    },
    timelineEvents: [],
  },
};

export const WithGraphAndTimeline: Story = {
  args: {
    localGraph: {
      nodes: {
        '0xabc': {
          id: '0xabc',
          address: '0xabc',
          chain: 'ethereum',
          taint_score: 0.8,
          risk_level: 'HIGH',
          labels: ['Mixer', 'High Risk'],
          tx_count: 150,
          balance: 12.5,
          first_seen: '2023-01-01',
          last_seen: '2025-01-15',
        },
        '0xdef': {
          id: '0xdef',
          address: '0xdef',
          chain: 'polygon',
          taint_score: 0.3,
          risk_level: 'MEDIUM',
          labels: ['DeFi'],
          tx_count: 75,
          balance: 5.2,
          first_seen: '2024-01-01',
          last_seen: '2025-01-12',
        },
        '0x789': {
          id: '0x789',
          address: '0x789',
          chain: 'ethereum',
          taint_score: 0.1,
          risk_level: 'LOW',
          labels: [],
          tx_count: 25,
          balance: 2.1,
          first_seen: '2024-08-01',
          last_seen: '2025-01-08',
        },
      },
      links: [
        {
          source: '0xabc',
          target: '0xdef',
          tx_hash: '0x123',
          value: 5,
          timestamp: '2025-01-01',
          event_type: 'transaction',
        },
        {
          source: '0xdef',
          target: '0x789',
          tx_hash: '0x456',
          value: 2,
          timestamp: '2025-01-05',
          event_type: 'transaction',
        },
      ],
    },
    timelineEvents: [
      {
        timestamp: '2025-01-01T10:00:00Z',
        address: '0xabc',
        event_type: 'transfer',
        value: 5,
        tx_hash: '0x123',
        risk_score: 75,
      },
      {
        timestamp: '2025-01-05T14:30:00Z',
        address: '0xdef',
        event_type: 'swap',
        value: 2,
        tx_hash: '0x456',
        risk_score: 35,
      },
      {
        timestamp: '2025-01-10T08:15:00Z',
        address: '0x789',
        event_type: 'transfer',
        value: 1,
        tx_hash: '0x789',
        risk_score: 15,
      },
    ],
  },
};

export const LargeGraph: Story = {
  args: {
    localGraph: {
      nodes: Object.fromEntries(
        Array.from({ length: 50 }, (_, i) => [
          `0x${i}`,
          {
            id: `0x${i}`,
            address: `0x${i}`,
            chain: 'ethereum',
            taint_score: Math.random(),
            risk_level: ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'][Math.floor(Math.random() * 4)],
            labels: Math.random() > 0.5 ? ['Label1'] : [],
            tx_count: Math.floor(Math.random() * 1000),
            balance: Math.random() * 100,
            first_seen: '2024-01-01',
            last_seen: '2025-01-15',
          },
        ])
      ),
      links: Array.from({ length: 80 }, (_, i) => ({
        source: `0x${Math.floor(Math.random() * 50)}`,
        target: `0x${Math.floor(Math.random() * 50)}`,
        tx_hash: `0x${i}`,
        value: Math.random() * 10,
        timestamp: '2025-01-01',
        event_type: 'transaction',
      })),
    },
    timelineEvents: Array.from({ length: 100 }, (_, i) => ({
      timestamp: `2025-01-${String(i % 30 + 1).padStart(2, '0')}T10:00:00Z`,
      address: `0x${Math.floor(Math.random() * 50)}`,
      event_type: ['transfer', 'swap', 'approval'][Math.floor(Math.random() * 3)],
      value: Math.random() * 10,
      tx_hash: `0x${i}`,
      risk_score: Math.floor(Math.random() * 100),
    })),
  },
};

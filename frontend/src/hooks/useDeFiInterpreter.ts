import { useMutation, useQuery } from '@tanstack/react-query';
import api from '@/lib/api';

// Types
export interface DeFiAction {
  type: string;
  description: string;
  protocol?: string;
  from?: string;
  to?: string;
  amount?: string;
  details?: Record<string, any>;
}

export interface DeFiInterpretation {
  tx_hash: string;
  chain: string;
  protocol: string;
  protocol_version?: string;
  type: string;
  complexity: 'simple' | 'moderate' | 'complex' | 'very_complex';
  description: string;
  human_readable: string;
  actions: DeFiAction[];
  function_signature?: string;
  decoded_input?: Record<string, any>;
  risk_assessment?: {
    risk_score: number;
    risk_level: 'low' | 'medium' | 'high' | 'critical';
    risk_factors: string[];
    warnings: string[];
    recommendations: string[];
  };
}

export interface BatchInterpretationResult {
  total: number;
  successful: number;
  failed: number;
  interpretations: DeFiInterpretation[];
  errors: Array<{
    tx_hash: string;
    error: string;
  }>;
}

export interface ProtocolInfo {
  name: string;
  version?: string;
  category: string;
  supported_functions: string[];
}

// Hooks
export function useInterpretTransaction() {
  return useMutation<DeFiInterpretation, Error, {
    tx_hash: string;
    chain: string;
    include_risk?: boolean;
  }>({
    mutationFn: async (data) => {
      const response = await api.post('/api/v1/defi-interpreter/interpret', data);
      return response.data;
    },
  });
}

export function useBatchInterpret() {
  return useMutation<BatchInterpretationResult, Error, {
    tx_hashes: string[];
    chain: string;
    include_risk?: boolean;
  }>({
    mutationFn: async (data) => {
      const response = await api.post('/api/v1/defi-interpreter/interpret/batch', data);
      return response.data;
    },
  });
}

export function useProtocols() {
  return useQuery<{
    total_protocols: number;
    protocols: string[];
    protocol_details: Record<string, ProtocolInfo>;
    supported_transaction_types: string[];
  }>({
    queryKey: ['defi-interpreter', 'protocols'],
    queryFn: async () => {
      const response = await api.get('/api/v1/defi-interpreter/protocols');
      return response.data;
    },
    staleTime: 3600000, // 1 hour
  });
}

// Helper functions
export function getComplexityColor(complexity: string): string {
  switch (complexity) {
    case 'very_complex':
      return 'text-red-600 bg-red-50 border-red-200';
    case 'complex':
      return 'text-orange-600 bg-orange-50 border-orange-200';
    case 'moderate':
      return 'text-yellow-600 bg-yellow-50 border-yellow-200';
    case 'simple':
    default:
      return 'text-green-600 bg-green-50 border-green-200';
  }
}

export function getProtocolLogo(protocol: string): string {
  const logos: Record<string, string> = {
    uniswap: '🦄',
    aave: '👻',
    compound: '🏦',
    curve: '🔵',
    balancer: '⚖️',
    sushiswap: '🍣',
    'pancakeswap': '🥞',
    tornado: '🌪️',
    lido: '🛡️',
    'maker': '🏛️',
    'instadapp': '📱',
    '1inch': '1️⃣',
    'rocket-pool': '🚀',
    'railgun': '🚂',
    'dydx': '📈',
    'gmx': '💹',
  };
  
  return logos[protocol.toLowerCase()] || '🔷';
}

export function getProtocolColor(protocol: string): string {
  const colors: Record<string, string> = {
    uniswap: 'text-pink-600 bg-pink-50',
    aave: 'text-purple-600 bg-purple-50',
    compound: 'text-green-600 bg-green-50',
    curve: 'text-blue-600 bg-blue-50',
    balancer: 'text-indigo-600 bg-indigo-50',
    sushiswap: 'text-orange-600 bg-orange-50',
    pancakeswap: 'text-yellow-600 bg-yellow-50',
  };
  
  return colors[protocol.toLowerCase()] || 'text-gray-600 bg-gray-50';
}

export function getActionIcon(actionType: string): string {
  const icons: Record<string, string> = {
    swap: '🔄',
    add_liquidity: '➕',
    remove_liquidity: '➖',
    borrow: '💸',
    repay: '💰',
    stake: '🔒',
    unstake: '🔓',
    claim: '🎁',
    deposit: '⬇️',
    withdraw: '⬆️',
    approve: '✅',
    transfer: '↔️',
  };
  
  return icons[actionType.toLowerCase()] || '📝';
}

export function formatActionDescription(action: DeFiAction): string {
  const parts: string[] = [];
  
  if (action.from) {
    parts.push(`from ${action.from}`);
  }
  
  if (action.to) {
    parts.push(`to ${action.to}`);
  }
  
  if (action.amount) {
    parts.push(`amount: ${action.amount}`);
  }
  
  return parts.join(' • ');
}

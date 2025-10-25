import { useMutation, useQuery } from '@tanstack/react-query';
import api from '@/lib/api';

// Types
export interface WalletBalance {
  chain: string;
  native_balance: string;
  native_balance_usd: number;
  tokens: Array<{
    symbol: string;
    name: string;
    balance: string;
    balance_usd: number;
    contract_address?: string;
  }>;
}

export function useScanAddresses() {
  return useMutation<WalletScanResult, Error, {
    addresses: Array<{ chain: string; address: string }>;
    check_history?: boolean;
    check_illicit?: boolean;
  }>({
    mutationFn: async (data) => {
      const response = await api.post('/api/v1/wallet-scanner/scan/addresses', data);
      return response.data;
    },
  });
}

export interface WalletAddress {
  chain: string;
  address: string;
  balance: WalletBalance;
  transaction_count: number;
  first_seen?: string;
  last_seen?: string;
  risk_score: number;
  risk_level: 'low' | 'medium' | 'high' | 'critical';
  illicit_connections: Array<{
    address: string;
    chain: string;
    type: string;
    risk_score: number;
  }>;
}

export interface WalletScanResult {
  scan_id: string;
  wallet_type: 'seed_phrase' | 'private_key';
  total_balance_usd: number;
  total_transactions: number;
  activity_level: 'none' | 'low' | 'moderate' | 'high' | 'very_high';
  risk_score: number;
  risk_level: 'low' | 'medium' | 'high' | 'critical';
  addresses: WalletAddress[];
  recommendations: string[];
  warnings: string[];
}

export interface BulkScanResult {
  total_scanned: number;
  successful_scans: number;
  failed_scans: number;
  total_balance_found_usd: number;
  results: WalletScanResult[];
  errors: Array<{
    index: number;
    error: string;
  }>;
}

// Hooks
export function useScanSeedPhrase() {
  return useMutation<WalletScanResult, Error, {
    seed_phrase: string;
    chains?: string[];
    check_history?: boolean;
    check_illicit?: boolean;
  }>({
    mutationFn: async (data) => {
      const response = await api.post('/api/v1/wallet-scanner/scan/seed-phrase', data);
      return response.data;
    },
  });
}

export function useScanPrivateKey() {
  return useMutation<WalletScanResult, Error, {
    private_key: string;
    chain: string;
    check_history?: boolean;
    check_illicit?: boolean;
  }>({
    mutationFn: async (data) => {
      const response = await api.post('/api/v1/wallet-scanner/scan/private-key', data);
      return response.data;
    },
  });
}

export function useBulkScan() {
  return useMutation<BulkScanResult, Error, {
    credentials: Array<{
      type: 'seed_phrase' | 'private_key';
      value: string;
    }>;
    chains?: string[];
    check_history?: boolean;
    check_illicit?: boolean;
  }>({
    mutationFn: async (data) => {
      const response = await api.post('/api/v1/wallet-scanner/scan/bulk', data);
      return response.data;
    },
  });
}

// Helper functions
export function formatBalance(balance: number): string {
  if (balance >= 1000000) {
    return `$${(balance / 1000000).toFixed(2)}M`;
  } else if (balance >= 1000) {
    return `$${(balance / 1000).toFixed(2)}K`;
  } else {
    return `$${balance.toFixed(2)}`;
  }
}

export function getRiskColor(riskLevel: string): string {
  switch (riskLevel) {
    case 'critical':
      return 'text-red-600 bg-red-50 border-red-200';
    case 'high':
      return 'text-orange-600 bg-orange-50 border-orange-200';
    case 'medium':
      return 'text-yellow-600 bg-yellow-50 border-yellow-200';
    case 'low':
    default:
      return 'text-green-600 bg-green-50 border-green-200';
  }
}

export function getActivityColor(activityLevel: string): string {
  switch (activityLevel) {
    case 'very_high':
      return 'text-purple-600 bg-purple-50';
    case 'high':
      return 'text-blue-600 bg-blue-50';
    case 'moderate':
      return 'text-indigo-600 bg-indigo-50';
    case 'low':
      return 'text-gray-600 bg-gray-50';
    case 'none':
    default:
      return 'text-slate-600 bg-slate-50';
  }
}

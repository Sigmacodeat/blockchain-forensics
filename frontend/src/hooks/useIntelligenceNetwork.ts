import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';

// Types
export interface IntelligenceFlag {
  id: string;
  address: string;
  chain: string;
  reason: 'ransomware' | 'scam' | 'fraud' | 'sanctions' | 'darknet' | 'terrorism' | 'other';
  description: string;
  amount_usd?: number;
  flagged_by: string;
  flagged_at: string;
  confirmed_by: string[];
  confirmation_count: number;
  auto_traced: boolean;
  status: 'pending' | 'confirmed' | 'disputed' | 'resolved';
  evidence: Array<{
    type: string;
    value: string;
  }>;
}

export interface IntelligenceCheckResult {
  address: string;
  chain: string;
  is_flagged: boolean;
  direct_flags: number;
  related_flags: number;
  risk_score: number;
  recommended_action: 'freeze' | 'review' | 'monitor' | 'allow';
  flags: IntelligenceFlag[];
  related_addresses: Array<{
    address: string;
    chain: string;
    relationship: string;
    flags: number;
  }>;
}

export interface NetworkStats {
  total_investigators: number;
  total_flags: number;
  confirmed_flags: number;
  pending_flags: number;
  total_checks: number;
  addresses_monitored: number;
  funds_frozen_usd: number;
  funds_recovered_usd: number;
}

export interface Investigator {
  id: string;
  org_name: string;
  tier: 'basic' | 'verified_security_firm' | 'law_enforcement' | 'exchange' | 'government';
  trust_score: number;
  flags_submitted: number;
  confirmed_flags: number;
  joined_at: string;
}

// Hooks
export function useIntelligenceStats() {
  return useQuery<NetworkStats>({
    queryKey: ['intelligence-network', 'stats'],
    queryFn: async () => {
      const response = await api.get('/api/v1/intelligence-network/stats');
      return response.data;
    },
    refetchInterval: 30000, // 30 seconds
  });
}

export function useIntelligenceFlags(params?: {
  address?: string;
  chain?: string;
  reason?: string;
  status?: string;
  limit?: number;
}) {
  return useQuery<{ flags: IntelligenceFlag[]; total: number }>({
    queryKey: ['intelligence-network', 'flags', params],
    queryFn: async () => {
      const response = await api.get('/api/v1/intelligence-network/flags', { params });
      return response.data;
    },
    refetchInterval: 15000, // 15 seconds
  });
}

export function useCheckAddress() {
  return useMutation<IntelligenceCheckResult, Error, {
    address: string;
    chain: string;
    check_related?: boolean;
  }>({
    mutationFn: async (data) => {
      const response = await api.post('/api/v1/intelligence-network/check', data);
      return response.data;
    },
  });
}

export function useFlagAddress() {
  const queryClient = useQueryClient();
  
  return useMutation<IntelligenceFlag, Error, {
    address: string;
    chain: string;
    reason: string;
    description: string;
    amount_usd?: number;
    evidence?: Array<{ type: string; value: string }>;
    auto_trace?: boolean;
  }>({
    mutationFn: async (data) => {
      const response = await api.post('/api/v1/intelligence-network/flags', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['intelligence-network'] });
    },
  });
}

export function useConfirmFlag() {
  const queryClient = useQueryClient();
  
  return useMutation<IntelligenceFlag, Error, {
    flag_id: string;
    evidence?: Array<{ type: string; value: string }>;
  }>({
    mutationFn: async ({ flag_id, evidence }) => {
      const response = await api.post(
        `/api/v1/intelligence-network/flags/${flag_id}/confirm`,
        { evidence }
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['intelligence-network'] });
    },
  });
}

export function useRegisterInvestigator() {
  const queryClient = useQueryClient();
  
  return useMutation<Investigator, Error, {
    org_name: string;
    tier: string;
    contact_info: {
      email: string;
      phone?: string;
    };
  }>({
    mutationFn: async (data) => {
      const response = await api.post('/api/v1/intelligence-network/investigators/register', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['intelligence-network'] });
    },
  });
}

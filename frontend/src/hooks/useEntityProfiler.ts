import { useMutation, useQuery } from '@tanstack/react-query';
import api from '@/lib/api';

// Types
export interface AttributionSignal {
  type: string;
  value: string;
  confidence: 'high' | 'medium' | 'low' | 'speculative';
  source: string;
  timestamp?: string;
}

export interface EntityAttribution {
  confidence: 'confirmed' | 'high' | 'medium' | 'low' | 'speculative';
  attributed_name?: string;
  attributed_type?: string;
  signals: AttributionSignal[];
}

export interface BlockchainData {
  total_transactions: number;
  total_volume_usd: number;
  unique_counterparties: number;
  first_activity?: string;
  last_activity?: string;
  balance_usd?: number;
}

export interface OSINTFinding {
  source: string;
  type: string;
  data: Record<string, any>;
  confidence: string;
  timestamp: string;
}

export interface OSINTData {
  identified_names: string[];
  social_profiles: Array<{
    platform: string;
    username: string;
    url: string;
  }>;
  websites: string[];
  email_addresses: string[];
  phone_numbers: string[];
  company_info?: Record<string, any>;
  news_mentions: Array<{
    title: string;
    url: string;
    date: string;
    source: string;
  }>;
  github_repos?: Array<{
    name: string;
    url: string;
    stars: number;
  }>;
  findings: OSINTFinding[];
}

export interface BehaviorAnalysis {
  activity_pattern: '24/7' | 'business_hours' | 'irregular' | 'inactive';
  transaction_frequency: 'very_high' | 'high' | 'moderate' | 'low' | 'very_low';
  typical_transaction_size_usd: number;
  counterparty_diversity: 'very_high' | 'high' | 'moderate' | 'low';
  transaction_patterns: Record<string, any>;
  anomalies: Array<{
    type: string;
    description: string;
    severity: string;
  }>;
}

export interface RelatedEntity {
  address: string;
  chain: string;
  relationship_type: string;
  confidence: number;
  entity_type?: string;
}

export interface EntityProfile {
  address: string;
  chain: string;
  entity_type: 'exchange' | 'mixer' | 'gambling' | 'defi_protocol' | 'bridge' | 'ransomware' | 'scam' | 'darknet_service' | 'payment_processor' | 'merchant' | 'individual' | 'unknown';
  attribution: EntityAttribution;
  blockchain_data: BlockchainData;
  osint_data?: OSINTData;
  behavior_analysis: BehaviorAnalysis;
  related_entities: RelatedEntity[];
  risk_assessment: {
    risk_score: number;
    risk_level: 'low' | 'medium' | 'high' | 'critical';
    risk_factors: string[];
    warnings: string[];
    recommendations: string[];
  };
  labels: string[];
  tags: string[];
}

export interface BulkProfileResult {
  total: number;
  successful: number;
  failed: number;
  profiles: EntityProfile[];
  errors: Array<{
    address: string;
    chain: string;
    error: string;
  }>;
}

export interface EntityType {
  type: string;
  description: string;
  risk_level: string;
  typical_indicators: string[];
}

// Hooks
export function useEntityProfile(
  address: string,
  chain: string,
  options?: {
    include_osint?: boolean;
    include_relationships?: boolean;
    depth?: number;
  }
) {
  return useQuery<EntityProfile>({
    queryKey: ['entity-profile', address, chain, options],
    queryFn: async () => {
      const response = await api.post('/api/v1/entity-profiler/profile', {
        address,
        chain,
        ...options,
      });
      return response.data;
    },
    enabled: !!address && !!chain,
    staleTime: 300000, // 5 minutes
  });
}

export function useProfileEntity() {
  return useMutation<EntityProfile, Error, {
    address: string;
    chain: string;
    include_osint?: boolean;
    include_relationships?: boolean;
    depth?: number;
  }>({
    mutationFn: async (data) => {
      const response = await api.post('/api/v1/entity-profiler/profile', data);
      return response.data;
    },
  });
}

export function useBulkProfile() {
  return useMutation<BulkProfileResult, Error, {
    addresses: Array<{ address: string; chain: string }>;
    include_osint?: boolean;
    include_relationships?: boolean;
  }>({
    mutationFn: async (data) => {
      const response = await api.post('/api/v1/entity-profiler/profile/bulk', data);
      return response.data;
    },
  });
}

export function useEntityTypes() {
  return useQuery<{ entity_types: EntityType[] }>({
    queryKey: ['entity-profiler', 'entity-types'],
    queryFn: async () => {
      const response = await api.get('/api/v1/entity-profiler/entity-types');
      return response.data;
    },
    staleTime: 3600000, // 1 hour
  });
}

// Helper functions
export function getEntityTypeIcon(entityType: string): string {
  const icons: Record<string, string> = {
    exchange: '🏦',
    mixer: '🌪️',
    gambling: '🎰',
    defi_protocol: '🏛️',
    bridge: '🌉',
    ransomware: '🔒',
    scam: '⚠️',
    darknet_service: '🕷️',
    payment_processor: '💳',
    merchant: '🛒',
    individual: '👤',
    unknown: '❓',
  };
  
  return icons[entityType] || '❓';
}

export function getEntityTypeColor(entityType: string): string {
  const colors: Record<string, string> = {
    exchange: 'text-blue-600 bg-blue-50 border-blue-200',
    mixer: 'text-red-600 bg-red-50 border-red-200',
    gambling: 'text-orange-600 bg-orange-50 border-orange-200',
    defi_protocol: 'text-purple-600 bg-purple-50 border-purple-200',
    bridge: 'text-indigo-600 bg-indigo-50 border-indigo-200',
    ransomware: 'text-red-700 bg-red-100 border-red-300',
    scam: 'text-orange-700 bg-orange-100 border-orange-300',
    darknet_service: 'text-gray-700 bg-gray-100 border-gray-300',
    payment_processor: 'text-green-600 bg-green-50 border-green-200',
    merchant: 'text-teal-600 bg-teal-50 border-teal-200',
    individual: 'text-slate-600 bg-slate-50 border-slate-200',
    unknown: 'text-gray-600 bg-gray-50 border-gray-200',
  };
  
  return colors[entityType] || 'text-gray-600 bg-gray-50 border-gray-200';
}

export function getConfidenceColor(confidence: string): string {
  switch (confidence) {
    case 'confirmed':
      return 'text-green-700 bg-green-50';
    case 'high':
      return 'text-blue-700 bg-blue-50';
    case 'medium':
      return 'text-yellow-700 bg-yellow-50';
    case 'low':
      return 'text-orange-700 bg-orange-50';
    case 'speculative':
    default:
      return 'text-gray-700 bg-gray-50';
  }
}

export function getActivityPatternColor(pattern: string): string {
  const colors: Record<string, string> = {
    '24/7': 'text-purple-600 bg-purple-50',
    business_hours: 'text-blue-600 bg-blue-50',
    irregular: 'text-orange-600 bg-orange-50',
    inactive: 'text-gray-600 bg-gray-50',
  };
  
  return colors[pattern] || 'text-gray-600 bg-gray-50';
}

export function formatVolume(volume: number): string {
  if (volume >= 1000000000) {
    return `$${(volume / 1000000000).toFixed(2)}B`;
  } else if (volume >= 1000000) {
    return `$${(volume / 1000000).toFixed(2)}M`;
  } else if (volume >= 1000) {
    return `$${(volume / 1000).toFixed(2)}K`;
  } else {
    return `$${volume.toFixed(2)}`;
  }
}

export function formatTransactionCount(count: number): string {
  if (count >= 1000000) {
    return `${(count / 1000000).toFixed(2)}M`;
  } else if (count >= 1000) {
    return `${(count / 1000).toFixed(2)}K`;
  } else {
    return count.toString();
  }
}

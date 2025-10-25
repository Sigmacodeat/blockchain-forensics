import { useQuery, UseQueryResult } from '@tanstack/react-query';
import axios from 'axios';

/**
 * Advanced Analytics Hooks
 * React Query hooks for premium analytics features
 */

const API_BASE = '/api/v1/analytics';

// Types
export interface RealTimeMetrics {
  active_traces: number;
  active_cases: number;
  critical_alerts: number;
  active_users: number;
  timestamp: string;
}

export interface ThreatCategory {
  category: string;
  count: number;
  avg_risk_score: number;
  percentage: number;
}

export interface RiskDistribution {
  date: string;
  critical: number;
  high: number;
  medium: number;
  low: number;
  total: number;
}

export interface GeographicData {
  country: string;
  count: number;
  avg_risk_score: number;
}

export interface EntityData {
  name: string;
  count: number;
  volume_usd: number;
}

export interface ComparisonData {
  period1: {
    total_traces: number;
    avg_risk_score: number;
    critical_alerts: number;
  };
  period2: {
    total_traces: number;
    avg_risk_score: number;
    critical_alerts: number;
  };
  changes: {
    total_traces_change: number;
    avg_risk_score_change: number;
    critical_alerts_change: number;
  };
}

export interface DrillDownAlert {
  id: string;
  address: string;
  risk_score: number;
  severity: string;
  message: string;
  created_at: string;
}

// ===================================
// HOOKS
// ===================================

export const useRealTimeMetrics = (
  refreshInterval: number = 30000 // 30 seconds
): UseQueryResult<RealTimeMetrics> => {
  return useQuery({
    queryKey: ['analytics', 'real-time'],
    queryFn: async () => {
      const { data } = await axios.get<RealTimeMetrics>(`${API_BASE}/real-time`);
      return data;
    },
    refetchInterval: refreshInterval,
    staleTime: 10000,
  });
};

export const useThreatCategories = (
  startDate?: string,
  endDate?: string,
  limit: number = 10
): UseQueryResult<ThreatCategory[]> => {
  return useQuery({
    queryKey: ['analytics', 'threat-categories', startDate, endDate, limit],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (startDate) params.append('start_date', startDate);
      if (endDate) params.append('end_date', endDate);
      params.append('limit', limit.toString());

      const { data } = await axios.get<ThreatCategory[]>(
        `${API_BASE}/threat-categories?${params}`
      );
      
      // Calculate percentages
      const total = data.reduce((sum, item) => sum + item.count, 0);
      return data.map(item => ({
        ...item,
        percentage: total > 0 ? (item.count / total) * 100 : 0,
      }));
    },
    staleTime: 60000, // 1 minute
  });
};

export const useRiskDistribution = (
  startDate?: string,
  endDate?: string,
  interval: 'day' | 'week' | 'month' = 'day'
): UseQueryResult<RiskDistribution[]> => {
  return useQuery({
    queryKey: ['analytics', 'risk-distribution', startDate, endDate, interval],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (startDate) params.append('start_date', startDate);
      if (endDate) params.append('end_date', endDate);
      params.append('interval', interval);

      const { data } = await axios.get<RiskDistribution[]>(
        `${API_BASE}/risk-distribution?${params}`
      );
      return data;
    },
    staleTime: 60000,
  });
};

export const useGeographicDistribution = (
  startDate?: string,
  endDate?: string
): UseQueryResult<GeographicData[]> => {
  return useQuery({
    queryKey: ['analytics', 'geographic', startDate, endDate],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (startDate) params.append('start_date', startDate);
      if (endDate) params.append('end_date', endDate);

      const { data } = await axios.get<GeographicData[]>(
        `${API_BASE}/geographic?${params}`
      );
      return data;
    },
    staleTime: 120000, // 2 minutes
  });
};

export const useTopEntities = (
  entityType: 'exchange' | 'mixer',
  startDate?: string,
  endDate?: string,
  limit: number = 10
): UseQueryResult<EntityData[]> => {
  return useQuery({
    queryKey: ['analytics', 'top-entities', entityType, startDate, endDate, limit],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (startDate) params.append('start_date', startDate);
      if (endDate) params.append('end_date', endDate);
      params.append('limit', limit.toString());

      const { data } = await axios.get<EntityData[]>(
        `${API_BASE}/top-entities/${entityType}?${params}`
      );
      return data;
    },
    staleTime: 120000,
  });
};

export const useComparison = (
  period1Start: string,
  period1End: string,
  period2Start: string,
  period2End: string,
  enabled: boolean = true
): UseQueryResult<ComparisonData> => {
  return useQuery({
    queryKey: ['analytics', 'comparison', period1Start, period1End, period2Start, period2End],
    queryFn: async () => {
      const params = new URLSearchParams({
        period1_start: period1Start,
        period1_end: period1End,
        period2_start: period2Start,
        period2_end: period2End,
      });

      const { data } = await axios.get<ComparisonData>(
        `${API_BASE}/comparison?${params}`
      );
      return data;
    },
    enabled,
    staleTime: 60000,
  });
};

export const useDrillDown = (
  category: string,
  startDate?: string,
  endDate?: string,
  limit: number = 50,
  enabled: boolean = false
): UseQueryResult<DrillDownAlert[]> => {
  return useQuery({
    queryKey: ['analytics', 'drill-down', category, startDate, endDate, limit],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (startDate) params.append('start_date', startDate);
      if (endDate) params.append('end_date', endDate);
      params.append('limit', limit.toString());

      const { data } = await axios.get<DrillDownAlert[]>(
        `${API_BASE}/drill-down/${encodeURIComponent(category)}?${params}`
      );
      return data;
    },
    enabled,
    staleTime: 60000,
  });
};

// ===================================
// EXPORT HELPERS
// ===================================

export const exportToCSV = async (
  dataType: string,
  startDate?: string,
  endDate?: string
): Promise<void> => {
  const params = new URLSearchParams({ data_type: dataType });
  if (startDate) params.append('start_date', startDate);
  if (endDate) params.append('end_date', endDate);

  const response = await axios.get(`${API_BASE}/export/csv?${params}`, {
    responseType: 'blob',
  });

  // Download file
  const url = window.URL.createObjectURL(new Blob([response.data]));
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', `analytics_${dataType}_${new Date().toISOString().split('T')[0]}.csv`);
  document.body.appendChild(link);
  link.click();
  link.remove();
};

export const exportToExcel = async (
  startDate?: string,
  endDate?: string
): Promise<void> => {
  const params = new URLSearchParams();
  if (startDate) params.append('start_date', startDate);
  if (endDate) params.append('end_date', endDate);

  const response = await axios.get(`${API_BASE}/export/excel?${params}`, {
    responseType: 'blob',
  });

  // Download file
  const url = window.URL.createObjectURL(new Blob([response.data]));
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', `analytics_report_${new Date().toISOString().split('T')[0]}.xlsx`);
  document.body.appendChild(link);
  link.click();
  link.remove();
};

export default {
  useRealTimeMetrics,
  useThreatCategories,
  useRiskDistribution,
  useGeographicDistribution,
  useTopEntities,
  useComparison,
  useDrillDown,
  exportToCSV,
  exportToExcel,
};

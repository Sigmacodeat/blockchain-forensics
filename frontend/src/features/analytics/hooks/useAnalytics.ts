import { useQuery } from '@tanstack/react-query';
import axios from 'axios';

export interface KPIMetrics {
  total_events: number;
  unique_users: number;
  pageviews: number;
}

export interface TrafficSource {
  source: string;
  visitors: number;
  percentage: number;
}

export interface TopPage {
  path: string;
  count: number;
  percentage: number;
}

export interface UserBehavior {
  avgScrollDepth: number;
  avgTimeOnPage: string;
  bounceRate: number;
  clickThroughRate: number;
}

export interface AnalyticsData {
  kpis: KPIMetrics;
  trafficSources: TrafficSource[];
  topPages: TopPage[];
  userBehavior: UserBehavior;
  timeSeriesData: {
    labels: string[];
    pageViews: number[];
    uniqueUsers: number[];
  };
}

const API_BASE = import.meta.env.VITE_API_URL || '';

export const useKPIs = (range: 'day' | 'week' | 'month' = 'day') => {
  return useQuery({
    queryKey: ['analytics-kpis', range],
    queryFn: async (): Promise<KPIMetrics> => {
      const response = await axios.get(`${API_BASE}/api/v1/analytics/kpis?range=${range}`);
      return response.data;
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

export const useTopPaths = (limit: number = 20) => {
  return useQuery({
    queryKey: ['analytics-top-paths', limit],
    queryFn: async (): Promise<TopPage[]> => {
      const response = await axios.get(`${API_BASE}/api/v1/analytics/top-paths?limit=${limit}`);
      return response.data.paths.map((path: any) => ({
        path: path.path,
        count: path.count,
        percentage: ((path.count / response.data.paths[0]?.count || 1) * 100).toFixed(1)
      }));
    },
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
};

export const useAnalyticsData = () => {
  const { data: kpis, isLoading: kpisLoading } = useKPIs('week');
  const { data: topPaths, isLoading: pathsLoading } = useTopPaths(10);

  // Mock additional data for now
  const analyticsData: AnalyticsData = {
    kpis: kpis || {
      total_events: 0,
      unique_users: 0,
      pageviews: 0
    },
    trafficSources: [
      { source: 'Direct', visitors: 1247, percentage: 43.8 },
      { source: 'Google', visitors: 892, percentage: 31.4 },
      { source: 'Social Media', visitors: 423, percentage: 14.9 },
      { source: 'Referral', visitors: 285, percentage: 10.0 }
    ],
    topPages: topPaths || [],
    userBehavior: {
      avgScrollDepth: 68,
      avgTimeOnPage: '3:24',
      bounceRate: 34.2,
      clickThroughRate: 12.8
    },
    timeSeriesData: {
      labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
      pageViews: [1200, 1350, 1180, 1420, 1680, 1520, 1380],
      uniqueUsers: [890, 920, 850, 980, 1100, 950, 920]
    }
  };

  return {
    data: analyticsData,
    isLoading: kpisLoading || pathsLoading
  };
};

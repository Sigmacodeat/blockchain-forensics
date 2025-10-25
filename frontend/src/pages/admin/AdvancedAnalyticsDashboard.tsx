import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import {
  BarChart3, TrendingUp, Users, Activity, Calendar,
  Download, Filter, RefreshCw, PieChart, LineChart
} from 'lucide-react';
import api from '@/lib/api';
import { useTranslation } from 'react-i18next';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  Title,
  Tooltip,
  Legend,
  ArcElement
} from 'chart.js';
import { Bar, Line, Pie } from 'react-chartjs-2';

// Register ChartJS components
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  Title,
  Tooltip,
  Legend,
  ArcElement
);

export default function AdvancedAnalyticsDashboard() {
  const { t } = useTranslation();
  const [dateRange, setDateRange] = useState(30);
  const [funnelSteps] = useState(['signup', 'first_login', 'first_trace', 'plan_upgrade']);

  // Fetch engagement metrics
  const { data: engagement, isLoading: engagementLoading } = useQuery({
    queryKey: ['analytics-engagement', dateRange],
    queryFn: async () => {
      const response = await api.get(`/api/v1/analytics/premium/engagement?days=${dateRange}`);
      return response.data;
    }
  });

  // Fetch retention metrics
  const { data: retention, isLoading: retentionLoading } = useQuery({
    queryKey: ['analytics-retention', dateRange],
    queryFn: async () => {
      const response = await api.get(`/api/v1/analytics/premium/retention?days=${dateRange}`);
      return response.data;
    }
  });

  // Fetch funnel analysis
  const { data: funnel, isLoading: funnelLoading } = useQuery({
    queryKey: ['analytics-funnel', funnelSteps],
    queryFn: async () => {
      const response = await api.post('/api/v1/analytics/premium/funnel', {
        funnel_steps: funnelSteps,
        start_date: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
        end_date: new Date().toISOString()
      });
      return response.data;
    }
  });

  // Fetch cohort analysis
  const { data: cohort, isLoading: cohortLoading } = useQuery({
    queryKey: ['analytics-cohort'],
    queryFn: async () => {
      const response = await api.get('/api/v1/analytics/premium/cohort?cohort_by=month&periods=6');
      return response.data;
    }
  });

  const isLoading = engagementLoading || retentionLoading || funnelLoading || cohortLoading;

  // Chart configurations
  const funnelChartData = {
    labels: funnel?.funnel_steps?.map((s: any) => s.step) || [],
    datasets: [
      {
        label: 'Users',
        data: funnel?.funnel_steps?.map((s: any) => s.count) || [],
        backgroundColor: 'rgba(139, 92, 246, 0.8)',
        borderColor: 'rgba(139, 92, 246, 1)',
        borderWidth: 2
      }
    ]
  };

  const retentionChartData = {
    labels: ['Day 1', 'Day 7', 'Day 30'],
    datasets: [
      {
        label: 'Retention Rate (%)',
        data: [
          retention?.retention?.day_1_retention?.retention_rate || 0,
          retention?.retention?.day_7_retention?.retention_rate || 0,
          retention?.retention?.day_30_retention?.retention_rate || 0
        ],
        backgroundColor: [
          'rgba(34, 197, 94, 0.8)',
          'rgba(234, 179, 8, 0.8)',
          'rgba(239, 68, 68, 0.8)'
        ],
        borderColor: [
          'rgba(34, 197, 94, 1)',
          'rgba(234, 179, 8, 1)',
          'rgba(239, 68, 68, 1)'
        ],
        borderWidth: 2
      }
    ]
  };

  const cohortChartData = cohort?.cohorts ? {
    labels: cohort.cohorts.map((c: any) => c.cohort),
    datasets: [
      {
        label: 'Cohort Size',
        data: cohort.cohorts.map((c: any) => c.cohort_size),
        backgroundColor: 'rgba(59, 130, 246, 0.8)',
        borderColor: 'rgba(59, 130, 246, 1)',
        borderWidth: 2
      }
    ]
  } : { labels: [], datasets: [] };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-purple-500 mx-auto mb-4"></div>
          <p className="text-slate-400">Loading analytics...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-3 rounded-xl bg-gradient-to-br from-purple-500 to-blue-500">
              <BarChart3 className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-white">Advanced Analytics</h1>
              <p className="text-slate-400 mt-1">
                Funnel, Cohort & Retention Analysis
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <select
              value={dateRange}
              onChange={(e) => setDateRange(parseInt(e.target.value))}
              className="px-4 py-2 bg-slate-800 text-slate-300 rounded-lg border border-slate-700"
            >
              <option value={7}>Last 7 days</option>
              <option value={30}>Last 30 days</option>
              <option value={90}>Last 90 days</option>
              <option value={365}>Last year</option>
            </select>
            <button className="flex items-center gap-2 px-4 py-2 bg-slate-800 text-slate-300 rounded-lg border border-slate-700 hover:bg-slate-700 transition-colors">
              <Download className="w-4 h-4" />
              Export
            </button>
          </div>
        </div>
      </motion.div>

      {/* Engagement Metrics Cards */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="p-6 rounded-xl bg-slate-800/50 backdrop-blur-sm border border-slate-700"
        >
          <div className="flex items-center justify-between mb-2">
            <p className="text-slate-400 text-sm font-medium">DAU</p>
            <Users className="w-5 h-5 text-blue-400" />
          </div>
          <p className="text-3xl font-bold text-white">
            {engagement?.dau?.toFixed(0) || '0'}
          </p>
          <p className="text-xs text-slate-500 mt-1">Daily Active Users</p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.1 }}
          className="p-6 rounded-xl bg-slate-800/50 backdrop-blur-sm border border-slate-700"
        >
          <div className="flex items-center justify-between mb-2">
            <p className="text-slate-400 text-sm font-medium">WAU</p>
            <Activity className="w-5 h-5 text-green-400" />
          </div>
          <p className="text-3xl font-bold text-white">
            {engagement?.wau?.toLocaleString() || '0'}
          </p>
          <p className="text-xs text-slate-500 mt-1">Weekly Active Users</p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.2 }}
          className="p-6 rounded-xl bg-slate-800/50 backdrop-blur-sm border border-slate-700"
        >
          <div className="flex items-center justify-between mb-2">
            <p className="text-slate-400 text-sm font-medium">MAU</p>
            <Calendar className="w-5 h-5 text-purple-400" />
          </div>
          <p className="text-3xl font-bold text-white">
            {engagement?.mau?.toLocaleString() || '0'}
          </p>
          <p className="text-xs text-slate-500 mt-1">Monthly Active Users</p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.3 }}
          className="p-6 rounded-xl bg-slate-800/50 backdrop-blur-sm border border-slate-700"
        >
          <div className="flex items-center justify-between mb-2">
            <p className="text-slate-400 text-sm font-medium">Stickiness</p>
            <TrendingUp className="w-5 h-5 text-yellow-400" />
          </div>
          <p className="text-3xl font-bold text-white">
            {engagement?.stickiness?.toFixed(1) || '0'}%
          </p>
          <p className="text-xs text-slate-500 mt-1">DAU/MAU Ratio</p>
          <div className="mt-2">
            {engagement?.stickiness >= 20 ? (
              <span className="text-xs text-green-400">Excellent</span>
            ) : engagement?.stickiness >= 10 ? (
              <span className="text-xs text-yellow-400">Good</span>
            ) : (
              <span className="text-xs text-red-400">Needs Work</span>
            )}
          </div>
        </motion.div>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-2 gap-6 mb-6">
        {/* Funnel Chart */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="p-6 rounded-xl bg-slate-800/50 backdrop-blur-sm border border-slate-700"
        >
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-white">Conversion Funnel</h3>
            <div className="text-sm text-slate-400">
              Overall: <span className="text-purple-400 font-bold">{funnel?.overall_conversion_rate}%</span>
            </div>
          </div>
          <div className="h-[300px]">
            <Bar
              data={funnelChartData}
              options={{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                  legend: { display: false },
                  tooltip: {
                    callbacks: {
                      label: (context: any) => {
                        const step = funnel?.funnel_steps?.[context.dataIndex];
                        return [
                          `Users: ${context.parsed.y}`,
                          `Conversion: ${step?.conversion_rate}%`,
                          `Drop-off: ${step?.drop_off}`
                        ];
                      }
                    }
                  }
                },
                scales: {
                  y: {
                    beginAtZero: true,
                    grid: { color: 'rgba(148, 163, 184, 0.1)' },
                    ticks: { color: '#94a3b8' }
                  },
                  x: {
                    grid: { display: false },
                    ticks: { color: '#94a3b8' }
                  }
                }
              }}
            />
          </div>
        </motion.div>

        {/* Retention Chart */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="p-6 rounded-xl bg-slate-800/50 backdrop-blur-sm border border-slate-700"
        >
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-white">Retention Curve</h3>
            <div className="text-sm text-slate-400">
              Churn: <span className="text-red-400 font-bold">{retention?.churn?.churn_rate}%</span>
            </div>
          </div>
          <div className="h-[300px]">
            <Bar
              data={retentionChartData}
              options={{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                  legend: { display: false },
                  tooltip: {
                    callbacks: {
                      label: (context: any) => `${context.parsed.y}% retention`
                    }
                  }
                },
                scales: {
                  y: {
                    beginAtZero: true,
                    max: 100,
                    grid: { color: 'rgba(148, 163, 184, 0.1)' },
                    ticks: { 
                      color: '#94a3b8',
                      callback: (value: any) => `${value}%`
                    }
                  },
                  x: {
                    grid: { display: false },
                    ticks: { color: '#94a3b8' }
                  }
                }
              }}
            />
          </div>
        </motion.div>
      </div>

      {/* Cohort Analysis */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="p-6 rounded-xl bg-slate-800/50 backdrop-blur-sm border border-slate-700"
      >
        <h3 className="text-lg font-semibold text-white mb-4">Cohort Analysis</h3>
        <div className="h-[300px]">
          <Line
            data={cohortChartData}
            options={{
              responsive: true,
              maintainAspectRatio: false,
              plugins: {
                legend: { display: false },
                tooltip: {
                  callbacks: {
                    label: (context: any) => `${context.parsed.y} users`
                  }
                }
              },
              scales: {
                y: {
                  beginAtZero: true,
                  grid: { color: 'rgba(148, 163, 184, 0.1)' },
                  ticks: { color: '#94a3b8' }
                },
                x: {
                  grid: { display: false },
                  ticks: { color: '#94a3b8' }
                }
              }
            }}
          />
        </div>
      </motion.div>

      {/* Retention Details */}
      <div className="grid grid-cols-3 gap-6 mt-6">
        {retention?.retention && Object.entries(retention.retention).map(([key, value]: [string, any], index) => (
          <motion.div
            key={key}
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.3 + index * 0.1 }}
            className="p-6 rounded-xl bg-slate-800/50 backdrop-blur-sm border border-slate-700"
          >
            <p className="text-slate-400 text-sm font-medium mb-2">
              {key.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
            </p>
            <p className="text-2xl font-bold text-white mb-1">
              {value.retention_rate}%
            </p>
            <p className="text-xs text-slate-500">
              {value.retained_users} users retained
            </p>
          </motion.div>
        ))}
      </div>
    </div>
  );
}

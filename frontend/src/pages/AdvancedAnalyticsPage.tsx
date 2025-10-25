import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Activity,
  TrendingUp,
  AlertTriangle,
  Users,
  Download,
  Calendar,
  Filter,
  RefreshCw,
} from 'lucide-react';
import { motion } from 'framer-motion';
import {
  useRealTimeMetrics,
  useThreatCategories,
  useRiskDistribution,
  useGeographicDistribution,
  useTopEntities,
  exportToCSV,
  exportToExcel,
} from '@/hooks/useAdvancedAnalytics';
import {
  RiskDistributionChart,
  ThreatCategoriesChart,
  TopEntitiesChart,
  MetricCard,
} from '@/components/analytics/RealTimeChart';
import { SkeletonDashboard } from '@/components/ui/SkeletonScreen';
import { EmptyState } from '@/components/ui/EmptyState';

/**
 * Advanced Analytics Dashboard
 * Premium analytics with real-time updates, exports, and drill-down
 */

const AdvancedAnalyticsPage: React.FC = () => {
  const { t } = useTranslation();
  
  // Date Range State
  const [dateRange, setDateRange] = useState<'today' | 'week' | 'month' | 'custom'>('week');
  const [startDate, setStartDate] = useState<string>('');
  const [endDate, setEndDate] = useState<string>('');
  
  // Export Loading State
  const [exporting, setExporting] = useState(false);
  
  // Real-Time Metrics (auto-refresh every 30s)
  const { data: metrics, isLoading: metricsLoading, refetch: refetchMetrics } = useRealTimeMetrics(30000);
  
  // Threat Categories
  const { data: threatCategories, isLoading: categoriesLoading } = useThreatCategories(
    startDate,
    endDate,
    10
  );
  
  // Risk Distribution
  const { data: riskDistribution, isLoading: riskLoading } = useRiskDistribution(
    startDate,
    endDate,
    'day'
  );
  
  // Geographic Distribution
  const { data: geographic, isLoading: geoLoading } = useGeographicDistribution(
    startDate,
    endDate
  );
  
  // Top Exchanges & Mixers
  const { data: topExchanges } = useTopEntities('exchange', startDate, endDate, 5);
  const { data: topMixers } = useTopEntities('mixer', startDate, endDate, 5);
  
  // Handle Export
  const handleExport = async (format: 'csv' | 'excel') => {
    setExporting(true);
    try {
      if (format === 'csv') {
        await exportToCSV('threat_categories', startDate, endDate);
      } else {
        await exportToExcel(startDate, endDate);
      }
    } catch (error) {
      console.error('Export failed:', error);
    } finally {
      setExporting(false);
    }
  };
  
  // Loading State
  if (metricsLoading && !metrics) {
    return <SkeletonDashboard />;
  }
  
  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900 p-6">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-2">
              {t('analytics.advanced.title', 'Advanced Analytics')}
            </h1>
            <p className="text-slate-600 dark:text-slate-400">
              {t('analytics.advanced.subtitle', 'Real-time insights and threat intelligence')}
            </p>
          </div>
          
          {/* Actions */}
          <div className="flex gap-3">
            <button
              onClick={() => refetchMetrics()}
              className="flex items-center gap-2 px-4 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors"
              aria-label={t('analytics.refresh', 'Refresh data')}
            >
              <RefreshCw className="w-4 h-4" />
              <span className="hidden sm:inline">{t('analytics.refresh', 'Refresh')}</span>
            </button>
            
            <button
              onClick={() => handleExport('excel')}
              disabled={exporting}
              className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-primary-600 to-primary-500 text-white rounded-lg hover:from-primary-700 hover:to-primary-600 transition-all shadow-lg hover:shadow-xl disabled:opacity-50"
              aria-label={t('analytics.export', 'Export data')}
            >
              <Download className="w-4 h-4" />
              <span className="hidden sm:inline">
                {exporting ? t('analytics.exporting', 'Exporting...') : t('analytics.export', 'Export')}
              </span>
            </button>
          </div>
        </div>
        
        {/* Date Range Filter */}
        <div className="flex flex-wrap gap-3">
          <div className="flex gap-2">
            {(['today', 'week', 'month'] as const).map((range) => (
              <button
                key={range}
                onClick={() => setDateRange(range)}
                className={`px-4 py-2 rounded-lg transition-colors ${
                  dateRange === range
                    ? 'bg-primary-600 text-white'
                    : 'bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700'
                }`}
                aria-pressed={dateRange === range}
              >
                {t(`analytics.dateRange.${range}`, range.charAt(0).toUpperCase() + range.slice(1))}
              </button>
            ))}
          </div>
        </div>
      </div>
      
      {/* Real-Time Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <MetricCard
          title={t('analytics.metrics.activeTraces', 'Active Traces')}
          value={metrics?.active_traces || 0}
          icon={<Activity className="w-5 h-5" />}
          color="primary"
        />
        <MetricCard
          title={t('analytics.metrics.activeCases', 'Active Cases')}
          value={metrics?.active_cases || 0}
          icon={<TrendingUp className="w-5 h-5" />}
          color="success"
        />
        <MetricCard
          title={t('analytics.metrics.criticalAlerts', 'Critical Alerts')}
          value={metrics?.critical_alerts || 0}
          icon={<AlertTriangle className="w-5 h-5" />}
          color="danger"
        />
        <MetricCard
          title={t('analytics.metrics.activeUsers', 'Active Users')}
          value={metrics?.active_users || 0}
          icon={<Users className="w-5 h-5" />}
          color="primary"
        />
      </div>
      
      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Risk Distribution Chart */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-6"
        >
          <h2 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">
            {t('analytics.charts.riskDistribution', 'Risk Distribution Over Time')}
          </h2>
          {riskLoading ? (
            <div className="h-80 flex items-center justify-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
            </div>
          ) : riskDistribution && riskDistribution.length > 0 ? (
            <RiskDistributionChart data={riskDistribution} height={320} />
          ) : (
            <EmptyState
              variant="no-data"
              title={t('analytics.noData', 'No data available')}
              description={t('analytics.noDataDesc', 'Try selecting a different date range')}
              size="sm"
            />
          )}
        </motion.div>
        
        {/* Threat Categories Chart */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-6"
        >
          <h2 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">
            {t('analytics.charts.threatCategories', 'Top Threat Categories')}
          </h2>
          {categoriesLoading ? (
            <div className="h-80 flex items-center justify-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
            </div>
          ) : threatCategories && threatCategories.length > 0 ? (
            <ThreatCategoriesChart data={threatCategories} height={320} />
          ) : (
            <EmptyState
              variant="no-data"
              title={t('analytics.noData', 'No data available')}
              description={t('analytics.noDataDesc', 'Try selecting a different date range')}
              size="sm"
            />
          )}
        </motion.div>
      </div>
      
      {/* Top Entities Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Exchanges */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-6"
        >
          <h2 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">
            {t('analytics.charts.topExchanges', 'Top Exchanges by Volume')}
          </h2>
          {topExchanges && topExchanges.length > 0 ? (
            <TopEntitiesChart
              data={topExchanges}
              height={300}
              dataKey="volume_usd"
              entityType="exchange"
            />
          ) : (
            <EmptyState variant="no-data" size="sm" />
          )}
        </motion.div>
        
        {/* Top Mixers */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-6"
        >
          <h2 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">
            {t('analytics.charts.topMixers', 'Top Mixers by Volume')}
          </h2>
          {topMixers && topMixers.length > 0 ? (
            <TopEntitiesChart
              data={topMixers}
              height={300}
              dataKey="volume_usd"
              entityType="mixer"
            />
          ) : (
            <EmptyState variant="no-data" size="sm" />
          )}
        </motion.div>
      </div>
    </div>
  );
};

export default AdvancedAnalyticsPage;

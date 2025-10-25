import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import { useQuery } from '@tanstack/react-query';
import api from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import {
  Activity, AlertTriangle, Shield, Database,
  TrendingUp, Zap, Clock, CheckCircle, XCircle,
  BarChart3, Target, Settings, RefreshCw,
  Cpu, HardDrive
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';

interface SystemHealth {
  status: string;
  uptime: number;
  version: string;
  timestamp: string;
  system: {
    platform: string;
    python_version: string;
    cpu_count: number;
    memory_total: number;
    memory_available: number;
    disk_usage: {
      total: number;
      free: number;
      used: number;
      percent: number;
    };
  };
  database: {
    connected: boolean;
    response_time: number;
    type: string;
  };
  services: {
    alert_engine: boolean;
    graph_db: boolean;
    ml_service: boolean;
  };
  environment: {
    mode: string;
    debug: boolean;
    log_level: string;
  };
}

const PerformanceDashboard: React.FC = () => {
  const { t } = useTranslation();
  const { user } = useAuth();
  const [refreshInterval, setRefreshInterval] = useState<number>(30000);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());

  const { data: systemHealth, isLoading: healthLoading } = useQuery({
    queryKey: ['systemHealth'],
    queryFn: async () => {
      const response = await api.get(`/api/v1/performance/system/health`);
      return response.data;
    },
    refetchInterval: refreshInterval
  });

  const { data: performanceMetrics, isLoading: metricsLoading } = useQuery({
    queryKey: ['performanceMetrics'],
    queryFn: async () => {
      const response = await api.get(`/api/v1/performance/monitoring/metrics`, { params: { time_window_minutes: 60 } });
      return response.data;
    },
    refetchInterval: refreshInterval
  });

  const { data: sloReport, isLoading: sloLoading } = useQuery({
    queryKey: ['sloReport'],
    queryFn: async () => {
      const response = await api.get(`/api/v1/performance/monitoring/slo`);
      return response.data;
    },
    refetchInterval: refreshInterval
  });

  const { data: performanceDashboard, isLoading: dashboardLoading } = useQuery({
    queryKey: ['performanceDashboard'],
    queryFn: async () => {
      const response = await api.get(`/api/v1/performance/monitoring/dashboard`);
      return response.data;
    },
    refetchInterval: refreshInterval
  });

  const formatUptime = (seconds: number) => {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    if (days > 0) return `${days}d ${hours}h`;
    if (hours > 0) return `${hours}h ${minutes}m`;
    return `${minutes}m`;
  };

  const formatBytes = (bytes: number) => {
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    if (bytes === 0) return '0 Bytes';
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'low': return 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400';
      case 'medium': return 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400';
      case 'high': return 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400';
      case 'critical': return 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400';
      default: return 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-400';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-slate-100 dark:from-slate-950 dark:via-slate-900 dark:to-slate-950">
      <div className="container mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <div className="flex flex-col lg:flex-row lg:justify-between lg:items-center gap-4">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-gradient-to-br from-primary-500 to-blue-500 rounded-xl shadow-lg">
                <Activity className="h-8 w-8 text-white" />
              </div>
              <div>
                <h1 className="text-3xl md:text-4xl font-bold text-gray-900 dark:text-white">
                  {t('perf.header.title', 'Performance & Observability')}
                </h1>
                <p className="text-gray-600 dark:text-gray-400 mt-1">
                  {t('perf.header.subtitle', 'Umfassende Überwachung von System-Performance, Metriken und SLOs')}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2 px-3 py-2 bg-card rounded-lg border border-border">
                <div className="flex h-2 w-2 rounded-full bg-green-500 animate-pulse" />
                <span className="text-sm text-gray-600 dark:text-gray-400">
                  {lastRefresh.toLocaleTimeString()}
                </span>
              </div>
              <Button onClick={() => setLastRefresh(new Date())} className="flex items-center gap-2 bg-gradient-to-r from-primary-500 to-blue-500 text-white">
                <RefreshCw className="h-4 w-4" />
                {t('perf.actions.refresh', 'Aktualisieren')}
              </Button>
            </div>
          </div>
        </motion.div>

        {/* System Health Overview */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8"
        >
          {[
            {
              title: t('perf.cards.system_status.title', 'System Status'),
              value: systemHealth?.status === 'healthy' 
                ? t('perf.cards.system_status.healthy', 'Gesund') 
                : t('perf.cards.system_status.issues', 'Probleme'),
              subtitle: `${t('perf.cards.system_status.uptime', 'Uptime')}: ${systemHealth ? formatUptime(systemHealth.uptime) : 'N/A'}`,
              icon: Activity,
              gradient: 'from-green-500 to-emerald-500',
              isHealthy: systemHealth?.status === 'healthy',
            },
            {
              title: t('perf.cards.cpu.title', 'CPU Usage'),
              value: `${performanceDashboard?.system_health?.cpu_usage?.toFixed(1) || 'N/A'}%`,
              subtitle: `${systemHealth?.system?.cpu_count || 'N/A'} ${t('perf.cards.cpu.cores', 'Cores')}`,
              icon: Cpu,
              gradient: 'from-primary-500 to-blue-500',
            },
            {
              title: t('perf.cards.memory.title', 'Memory Usage'),
              value: `${performanceDashboard?.system_health?.memory_usage?.toFixed(1) || 'N/A'}%`,
              subtitle: `${systemHealth?.system ? formatBytes(systemHealth.system.memory_available) : 'N/A'} ${t('perf.cards.memory.available', 'verfügbar')}`,
              icon: HardDrive,
              gradient: 'from-green-500 to-teal-500',
            },
            {
              title: t('perf.cards.db.title', 'Database'),
              value: systemHealth?.database?.connected 
                ? t('perf.cards.db.connected', 'Verbunden') 
                : t('perf.cards.db.disconnected', 'Getrennt'),
              subtitle: `${t('perf.cards.db.response', 'Response')}: ${systemHealth?.database?.response_time || 'N/A'}ms`,
              icon: Database,
              gradient: 'from-blue-500 to-cyan-500',
              isHealthy: systemHealth?.database?.connected,
            },
          ].map((card, index) => {
            const Icon = card.icon;
            return (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.05 * index }}
              >
                <Card className="border border-border shadow-lg bg-card hover:shadow-xl transition-all group">
                  <CardContent className="pt-6">
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex-1">
                        <p className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">
                          {card.title}
                        </p>
                        <p className={`text-2xl font-bold ${
                          card.isHealthy !== undefined
                            ? card.isHealthy
                              ? 'text-green-600 dark:text-green-400'
                              : 'text-red-600 dark:text-red-400'
                            : 'text-gray-900 dark:text-white'
                        }`}>
                          {card.value}
                        </p>
                      </div>
                      <div className={`p-3 bg-gradient-to-br ${card.gradient} rounded-xl shadow-md group-hover:scale-110 transition-transform`}>
                        <Icon className="h-6 w-6 text-white" />
                      </div>
                    </div>
                    <div className="text-sm text-gray-600 dark:text-gray-400">
                      {card.subtitle}
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            );
          })}
        </motion.div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Performance Metrics */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }}
          >
            <Card className="border border-border shadow-lg bg-card h-full">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-gray-900 dark:text-white">
                  <BarChart3 className="h-5 w-5 text-primary-600 dark:text-primary-400" />
                  {t('perf.metrics.title', 'Performance-Metriken (1 Stunde)')}
                </CardTitle>
              </CardHeader>
              <CardContent className="max-h-[500px] overflow-y-auto">
                {metricsLoading ? (
                  <div className="text-center py-8 text-gray-600 dark:text-gray-400">
                    {t('perf.metrics.loading', 'Lade Metriken...')}
                  </div>
                ) : performanceMetrics ? (
                  <div className="space-y-3">
                    {Object.entries(performanceMetrics.metrics).slice(0, 8).map(([metricName, metricData]: [string, any]) => (
                      <div key={metricName} className="p-3 bg-muted rounded-lg border border-border">
                        <div className="flex items-center justify-between">
                          <div className="flex-1">
                            <div className="font-medium text-gray-900 dark:text-white capitalize">
                              {metricName.replace(/_/g, ' ')}
                            </div>
                            <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                              {metricData.count} {t('perf.metrics.measurements', 'Messungen')} • {t('perf.metrics.trend', 'Trend')}: {metricData.trend}
                            </div>
                          </div>
                          <div className="text-right ml-4">
                            <div className="text-lg font-bold text-gray-900 dark:text-white">
                              {typeof metricData.avg === 'number' ? metricData.avg.toFixed(2) : 'N/A'}
                            </div>
                            <div className="text-xs text-gray-500 dark:text-gray-400">
                              {t('perf.metrics.min', 'Min')}: {typeof metricData.min === 'number' ? metricData.min.toFixed(2) : 'N/A'} •{' '}
                              {t('perf.metrics.max', 'Max')}: {typeof metricData.max === 'number' ? metricData.max.toFixed(2) : 'N/A'}
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                    {t('perf.metrics.empty', 'Keine Metrik-Daten verfügbar')}
                  </div>
                )}
              </CardContent>
            </Card>
          </motion.div>

          {/* SLO Compliance */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }}
          >
            <Card className="border border-border shadow-lg bg-card h-full">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-gray-900 dark:text-white">
                  <Target className="h-5 w-5 text-blue-600 dark:text-blue-400" />
                  {t('perf.slo.title', 'SLO-Compliance')}
                </CardTitle>
              </CardHeader>
              <CardContent className="max-h-[500px] overflow-y-auto">
                {sloLoading ? (
                  <div className="text-center py-8 text-gray-600 dark:text-gray-400">
                    {t('perf.slo.loading', 'Lade SLOs...')}
                  </div>
                ) : sloReport ? (
                  <div className="space-y-3">
                    {Object.entries(sloReport.compliance).map(([metricName, compliance]: [string, any]) => (
                      <div key={metricName} className="p-3 bg-muted rounded-lg border border-border">
                        <div className="flex justify-between items-center mb-2">
                          <span className="font-medium text-gray-900 dark:text-white capitalize">
                            {metricName.replace(/_/g, ' ')}
                          </span>
                          <Badge className={`${
                            compliance.compliance_rate >= 0.95 ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' :
                            compliance.compliance_rate >= 0.9 ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400' :
                            'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
                          }`}>
                            {(compliance.compliance_rate * 100).toFixed(1)}%
                          </Badge>
                        </div>
                        <div className="text-sm text-gray-600 dark:text-gray-400">
                          {t('perf.slo.threshold', 'Threshold')}: {compliance.threshold} {compliance.unit} •{' '}
                          {t('perf.slo.violations', 'Violations')}: {compliance.violations} / {compliance.total_samples}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                    {t('perf.slo.empty', 'Keine SLO-Daten verfügbar')}
                  </div>
                )}
              </CardContent>
            </Card>
          </motion.div>
        </div>

        {/* Service Status & Recent Alerts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Service Status */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
          >
            <Card className="border border-border shadow-lg bg-card">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-gray-900 dark:text-white">
                  <Shield className="h-5 w-5 text-green-600 dark:text-green-400" />
                  {t('perf.services.title', 'Service Status')}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {systemHealth?.services && Object.entries(systemHealth.services).map(([service, status]) => (
                    <div key={service} className="flex items-center justify-between p-3 bg-muted rounded-lg border border-border">
                      <span className="font-medium text-gray-900 dark:text-white capitalize">
                        {service.replace(/_/g, ' ')}
                      </span>
                      <div className="flex items-center gap-2">
                        {status ? (
                          <CheckCircle className="h-5 w-5 text-green-600 dark:text-green-400" />
                        ) : (
                          <XCircle className="h-5 w-5 text-red-600 dark:text-red-400" />
                        )}
                        <span className={`text-sm font-medium ${status ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                          {status ? t('perf.services.active', 'Aktiv') : t('perf.services.inactive', 'Inaktiv')}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </motion.div>

          {/* Recent Alerts */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
          >
            <Card className="border border-border shadow-lg bg-card">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-gray-900 dark:text-white">
                  <AlertTriangle className="h-5 w-5 text-orange-600 dark:text-orange-400" />
                  {t('perf.recent_alerts.title', 'Kürzliche Performance-Alerts')}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3 max-h-64 overflow-y-auto">
                  {performanceDashboard?.recent_alerts && performanceDashboard.recent_alerts.length > 0 ? (
                    performanceDashboard.recent_alerts.map((alert: any, index: number) => (
                      <div key={index} className="p-3 bg-muted rounded-lg border border-border">
                        <div className="flex justify-between items-start mb-2">
                          <span className="font-medium text-gray-900 dark:text-white text-sm">
                            {alert.metric || 'Unknown'}
                          </span>
                          <Badge className={getSeverityColor(alert.severity)}>
                            {alert.severity}
                          </Badge>
                        </div>
                        <div className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                          {alert.description}
                        </div>
                        <div className="text-xs text-gray-500 dark:text-gray-500">
                          {new Date(alert.timestamp).toLocaleString()}
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                      {t('perf.recent_alerts.empty', 'Keine aktuellen Alerts')}
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </motion.div>
        </div>

        {/* System Details */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
        >
          <Card className="border border-border shadow-lg bg-card">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-gray-900 dark:text-white">
                <Settings className="h-5 w-5 text-gray-600 dark:text-gray-400" />
                {t('perf.system_details.title', 'System-Details')}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div>
                  <h4 className="font-medium text-gray-900 dark:text-white mb-3">
                    {t('perf.system_details.system_info', 'System Information')}
                  </h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between py-2 border-b border-border">
                      <span className="text-gray-600 dark:text-gray-400">
                        {t('perf.system_details.platform', 'Platform')}:
                      </span>
                      <span className="font-medium text-gray-900 dark:text-white">
                        {systemHealth?.system?.platform || 'N/A'}
                      </span>
                    </div>
                    <div className="flex justify-between py-2 border-b border-border">
                      <span className="text-gray-600 dark:text-gray-400">
                        {t('perf.system_details.python_version', 'Python Version')}:
                      </span>
                      <span className="font-medium text-gray-900 dark:text-white">
                        {systemHealth?.system?.python_version || 'N/A'}
                      </span>
                    </div>
                    <div className="flex justify-between py-2">
                      <span className="text-gray-600 dark:text-gray-400">
                        {t('perf.system_details.version', 'Version')}:
                      </span>
                      <span className="font-medium text-gray-900 dark:text-white">
                        {systemHealth?.version || '1.0.0'}
                      </span>
                    </div>
                  </div>
                </div>

                <div>
                  <h4 className="font-medium text-gray-900 dark:text-white mb-3">
                    {t('perf.system_details.environment', 'Environment')}
                  </h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between py-2 border-b border-border">
                      <span className="text-gray-600 dark:text-gray-400">
                        {t('perf.system_details.mode', 'Mode')}:
                      </span>
                      <span className="font-medium text-gray-900 dark:text-white">
                        {systemHealth?.environment?.mode || 'N/A'}
                      </span>
                    </div>
                    <div className="flex justify-between py-2 border-b border-border">
                      <span className="text-gray-600 dark:text-gray-400">
                        {t('perf.system_details.debug', 'Debug')}:
                      </span>
                      <span className="font-medium text-gray-900 dark:text-white">
                        {systemHealth?.environment?.debug ? t('perf.common.yes', 'Ja') : t('perf.common.no', 'Nein')}
                      </span>
                    </div>
                    <div className="flex justify-between py-2">
                      <span className="text-gray-600 dark:text-gray-400">
                        {t('perf.system_details.log_level', 'Log Level')}:
                      </span>
                      <span className="font-medium text-gray-900 dark:text-white">
                        {systemHealth?.environment?.log_level || 'INFO'}
                      </span>
                    </div>
                  </div>
                </div>

                <div>
                  <h4 className="font-medium text-gray-900 dark:text-white mb-3">
                    {t('perf.system_details.database', 'Database')}
                  </h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between py-2 border-b border-border">
                      <span className="text-gray-600 dark:text-gray-400">
                        {t('perf.system_details.db_type', 'Type')}:
                      </span>
                      <span className="font-medium text-gray-900 dark:text-white">
                        {systemHealth?.database?.type || 'N/A'}
                      </span>
                    </div>
                    <div className="flex justify-between py-2 border-b border-border">
                      <span className="text-gray-600 dark:text-gray-400">
                        {t('perf.system_details.db_connected', 'Connected')}:
                      </span>
                      <span className={`font-medium ${systemHealth?.database?.connected ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                        {systemHealth?.database?.connected ? t('perf.common.yes', 'Ja') : t('perf.common.no', 'Nein')}
                      </span>
                    </div>
                    <div className="flex justify-between py-2">
                      <span className="text-gray-600 dark:text-gray-400">
                        {t('perf.system_details.response_time', 'Response Time')}:
                      </span>
                      <span className="font-medium text-gray-900 dark:text-white">
                        {systemHealth?.database?.response_time || 'N/A'}ms
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </div>
  );
};

export default PerformanceDashboard;

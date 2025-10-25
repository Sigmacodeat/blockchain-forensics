import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useQuery, useMutation } from '@tanstack/react-query';
import axios from 'axios';
import { motion } from 'framer-motion';
import {
  Brain, TrendingUp, AlertTriangle,
  Zap, Shield, Target, Activity, BarChart3,
  Users, DollarSign, Layers, GitBranch, Network,
  RefreshCw, Sparkles
} from 'lucide-react';
import { Button } from '@/components/ui/button';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const CorrelationAnalysisPage: React.FC = () => {
  const { t } = useTranslation();
  const [selectedTimeWindow, setSelectedTimeWindow] = useState<number>(3600);
  const [selectedMinSeverity, setSelectedMinSeverity] = useState<string>('medium');
  const [testRuleName, setTestRuleName] = useState<string>('');
  const [testAlerts, setTestAlerts] = useState<any[]>([]);

  // Fetch correlation rules
  const { data: correlationRules, isLoading: rulesLoading } = useQuery<any>({
    queryKey: ['correlationRules'],
    queryFn: async () => {
      const response = await axios.get(`${API_BASE_URL}/api/v1/alerts/correlation/rules`);
      return response.data;
    }
  });

  // Fetch correlation analysis
  const { data: correlationAnalysis, isLoading: analysisLoading, refetch: refetchAnalysis } = useQuery<any>({
    queryKey: ['correlationAnalysis', selectedTimeWindow, selectedMinSeverity],
    queryFn: async () => {
      const response = await axios.get(
        `${API_BASE_URL}/api/v1/alerts/correlation/analysis`,
        {
          params: {
            time_window: selectedTimeWindow,
            min_severity: selectedMinSeverity
          }
        }
      );
      return response.data;
    }
  });

  // Fetch suppression statistics
  const { data: suppressionStats } = useQuery<any>({
    queryKey: ['suppressionStats'],
    queryFn: async () => {
      const response = await axios.get(`${API_BASE_URL}/api/v1/alerts/suppressions/statistics`);
      return response.data;
    }
  });

  // Test correlation rule mutation
  const testCorrelationMutation = useMutation<any, unknown, { ruleName: string; alerts: any[] }>({
    mutationFn: async (data: { ruleName: string; alerts: any[] }) => {
      const response = await axios.post(`${API_BASE_URL}/api/v1/alerts/correlation/test`, {
        rule_name: data.ruleName,
        sample_alerts: data.alerts
      });
      return response.data;
    }
  });

  const handleTestRule = () => {
    if (testRuleName && testAlerts.length > 0) {
      testCorrelationMutation.mutate({
        ruleName: testRuleName,
        alerts: testAlerts
      });
    }
  };

  const addTestAlert = () => {
    const newAlert = {
      alert_type: 'high_risk_address',
      severity: 'medium',
      title: 'Test Alert',
      description: 'Test Description',
      address: `0x${Math.random().toString(16).substr(2, 40)}`,
      tx_hash: `0x${Math.random().toString(16).substr(2, 64)}`
    };
    setTestAlerts([...testAlerts, newAlert]);
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'low': return 'text-green-600 dark:text-green-400';
      case 'medium': return 'text-yellow-600 dark:text-yellow-400';
      case 'high': return 'text-orange-600 dark:text-orange-400';
      case 'critical': return 'text-red-600 dark:text-red-400';
      default: return 'text-slate-600 dark:text-slate-400';
    }
  };

  const getSeverityBgColor = (severity: string) => {
    switch (severity) {
      case 'low': return 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300';
      case 'medium': return 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300';
      case 'high': return 'bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-300';
      case 'critical': return 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300';
      default: return 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300';
    }
  };

  const iconColor = (c: string) => ({
    purple: 'text-purple-600 dark:text-purple-400',
    red: 'text-red-600 dark:text-red-400',
    yellow: 'text-yellow-600 dark:text-yellow-400',
    orange: 'text-orange-600 dark:text-orange-400',
    pink: 'text-pink-600 dark:text-pink-400',
    blue: 'text-blue-600 dark:text-blue-400',
    slate: 'text-slate-600 dark:text-slate-400',
    green: 'text-green-600 dark:text-green-400',
    indigo: 'text-indigo-600 dark:text-indigo-400',
  } as Record<string,string>)[c] || 'text-slate-600 dark:text-slate-400';

  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Premium Header mit Glassmorphism */}
        <motion.div 
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8 relative"
        >
          <div className="bg-gradient-to-r from-purple-600 via-blue-600 to-indigo-600 dark:from-purple-900 dark:via-blue-900 dark:to-indigo-900 rounded-2xl p-8 shadow-2xl">
            <div className="relative z-10">
              <div className="flex items-center gap-3 mb-3">
                <div className="p-3 bg-white/20 dark:bg-white/10 backdrop-blur-sm rounded-xl">
                  <Brain className="h-8 w-8 text-white" />
                </div>
                <h1 className="text-3xl md:text-4xl font-bold text-white">
                  {t('corr.header.title', 'Korrelations-Analyse & Erweiterte Alert-Regeln')}
                </h1>
              </div>
              <p className="text-white/90 text-lg max-w-3xl">
                {t('corr.header.subtitle', 'Intelligente Erkennung komplexer Bedrohungsmuster durch Korrelations-Analyse')}
              </p>
            </div>
            {/* Decorative Elements */}
            <div className="absolute top-0 right-0 w-64 h-64 bg-white/5 rounded-full blur-3xl"></div>
            <div className="absolute bottom-0 left-0 w-48 h-48 bg-blue-500/10 rounded-full blur-2xl"></div>
          </div>
        </motion.div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Controls Panel */}
          <motion.div 
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.1 }}
            className="lg:col-span-1 space-y-6"
          >
            {/* Analysis Settings */}
            <div className="bg-card p-6 rounded-xl shadow-lg border border-border">
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2 text-slate-900 dark:text-white">
                <div className="p-2 bg-primary-100 dark:bg-primary-900/30 rounded-lg">
                  <Activity className="h-5 w-5 text-primary-600 dark:text-primary-400" />
                </div>
                {t('corr.controls.title', 'Analyse-Einstellungen')}
              </h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                    {t('corr.controls.window', 'Zeitfenster')}
                  </label>
                  <select
                    value={selectedTimeWindow}
                    onChange={(e) => setSelectedTimeWindow(parseInt(e.target.value))}
                    className="w-full px-4 py-2.5 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-white focus:ring-2 focus:ring-primary-500 dark:focus:ring-primary-600 focus:border-transparent transition-all"
                  >
                    <option value={300}>{t('corr.controls.window_5m', '5 Minuten')}</option>
                    <option value={900}>{t('corr.controls.window_15m', '15 Minuten')}</option>
                    <option value={1800}>{t('corr.controls.window_30m', '30 Minuten')}</option>
                    <option value={3600}>{t('corr.controls.window_1h', '1 Stunde')}</option>
                    <option value={7200}>{t('corr.controls.window_2h', '2 Stunden')}</option>
                    <option value={86400}>{t('corr.controls.window_24h', '24 Stunden')}</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                    {t('corr.controls.min_severity', 'Minimum Severity')}
                  </label>
                  <select
                    value={selectedMinSeverity}
                    onChange={(e) => setSelectedMinSeverity(e.target.value)}
                    className="w-full px-4 py-2.5 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-white focus:ring-2 focus:ring-primary-500 dark:focus:ring-primary-600 focus:border-transparent transition-all"
                  >
                    <option value="low">{t('corr.sev.low', 'Low')}</option>
                    <option value="medium">{t('corr.sev.medium', 'Medium')}</option>
                    <option value="high">{t('corr.sev.high', 'High')}</option>
                    <option value="critical">{t('corr.sev.critical', 'Critical')}</option>
                  </select>
                </div>

                <Button onClick={() => refetchAnalysis()} className="w-full flex items-center justify-center gap-2">
                  <RefreshCw className="h-4 w-4" />
                  {t('corr.controls.refresh', 'Analyse aktualisieren')}
                </Button>
              </div>
            </div>

            {/* Correlation Rules Test */}
            <div className="bg-card p-6 rounded-xl shadow-lg border border-border">
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2 text-slate-900 dark:text-white">
                <div className="p-2 bg-purple-100 dark:bg-purple-900/30 rounded-lg">
                  <GitBranch className="h-5 w-5 text-purple-600 dark:text-purple-400" />
                </div>
                {t('corr.test.title', 'Korrelations-Regel testen')}
              </h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                    {t('corr.test.pick_rule', 'Regel auswählen')}
                  </label>
                  <select
                    value={testRuleName}
                    onChange={(e) => setTestRuleName(e.target.value)}
                    className="w-full px-4 py-2.5 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-white focus:ring-2 focus:ring-purple-500 dark:focus:ring-purple-600 focus:border-transparent transition-all"
                  >
                    <option value="">{t('corr.test.pick_rule_ph', 'Regel auswählen...')}</option>
                    {correlationRules?.rules && Object.keys(correlationRules.rules).map(ruleName => (
                      <option key={ruleName} value={ruleName}>{ruleName}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                    {t('corr.test.alerts_label', 'Test-Alerts')}
                  </label>
                  <div className="max-h-32 overflow-y-auto border border-border rounded-lg p-3 mb-2 bg-muted">
                    {testAlerts.map((alert, index) => (
                      <div key={index} className="text-xs text-slate-600 dark:text-slate-400 mb-1 font-mono">
                        {alert.alert_type} ({alert.severity})
                      </div>
                    ))}
                    {testAlerts.length === 0 && (
                      <div className="text-xs text-slate-400 dark:text-slate-500">
                        {t('corr.test.no_alerts', 'Keine Test-Alerts hinzugefügt')}
                      </div>
                    )}
                  </div>
                  <Button onClick={addTestAlert} variant="outline" className="w-full">
                    {t('corr.test.add_alert', 'Alert hinzufügen')}
                  </Button>
                </div>

                <Button
                  onClick={handleTestRule}
                  disabled={!testRuleName || testAlerts.length === 0 || testCorrelationMutation.isPending}
                  className="w-full flex items-center justify-center gap-2"
                >
                  <Sparkles className="h-4 w-4" />
                  {testCorrelationMutation.isPending ? t('corr.test.testing', 'Teste...') : t('corr.test.run', 'Regel testen')}
                </Button>

                {testCorrelationMutation.data && (
                  <motion.div 
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="mt-3 p-4 bg-muted rounded-lg border border-border"
                  >
                    <div className="text-sm flex items-center gap-2">
                      <span className="font-medium text-slate-700 dark:text-slate-300">
                        {t('corr.test.result', 'Ergebnis: ')}
                      </span>
                      <span className={(testCorrelationMutation.data as any).matches ? 'text-green-600 dark:text-green-400 font-semibold' : 'text-red-600 dark:text-red-400 font-semibold'}>
                        {(testCorrelationMutation.data as any).matches ? t('corr.test.match', 'Übereinstimmung gefunden') : t('corr.test.no_match', 'Keine Übereinstimmung')}
                      </span>
                    </div>
                  </motion.div>
                )}
              </div>
            </div>

            {/* Suppression Stats Summary */}
            {suppressionStats && (
              <div className="bg-card p-6 rounded-xl shadow-lg border border-border">
                <h3 className="text-lg font-semibold mb-4 flex items-center gap-2 text-slate-900 dark:text-white">
                  <div className="p-2 bg-emerald-100 dark:bg-emerald-900/30 rounded-lg">
                    <Shield className="h-5 w-5 text-emerald-600 dark:text-emerald-400" />
                  </div>
                  {t('corr.suppressions.title', 'Suppression Übersicht')}
                </h3>
                <div className="space-y-3">
                  <div className="flex justify-between items-center p-3 bg-muted rounded-lg">
                    <span className="text-sm font-medium text-slate-600 dark:text-slate-400">
                      {t('corr.suppressions.rate', 'Suppression Rate')}
                    </span>
                    <span className="font-bold text-emerald-600 dark:text-emerald-400">
                      {(suppressionStats.suppression_rate * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-muted rounded-lg">
                    <span className="text-sm font-medium text-slate-600 dark:text-slate-400">
                      {t('corr.suppressions.total', 'Total Suppressions')}
                    </span>
                    <span className="font-bold text-slate-900 dark:text-white">
                      {suppressionStats.total_suppressions}
                    </span>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-muted rounded-lg">
                    <span className="text-sm font-medium text-slate-600 dark:text-slate-400">
                      {t('corr.suppressions.top_entity', 'Top Entity')}
                    </span>
                    <span className="font-mono text-xs text-slate-700 dark:text-slate-300">
                      {suppressionStats.top_suppressed_entities[0]?.[0]?.slice(0, 10)}...
                    </span>
                  </div>
                </div>
              </div>
            )}
          </motion.div>

          {/* Main Content */}
          <motion.div 
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }}
            className="lg:col-span-2 space-y-6"
          >
            {/* Correlation Analysis Overview */}
            <div className="bg-card p-6 rounded-xl shadow-lg border border-border">
              <div className="flex flex-col md:flex-row md:justify-between md:items-center mb-6 gap-3">
                <h3 className="text-lg font-semibold flex items-center gap-2 text-slate-900 dark:text-white">
                  <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
                    <TrendingUp className="h-5 w-5 text-blue-600 dark:text-blue-400" />
                  </div>
                  {t('corr.overview.title', 'Korrelations-Analyse Übersicht')}
                </h3>
                <div className="text-sm text-slate-600 dark:text-slate-400 bg-muted px-4 py-2 rounded-lg">
                  {t('corr.overview.window', 'Zeitfenster')}: <span className="font-semibold">{Math.floor(selectedTimeWindow / 3600)}h</span> • {t('corr.overview.min_sev', 'Min Severity')}: <span className="font-semibold capitalize">{selectedMinSeverity}</span>
                </div>
              </div>

              {analysisLoading ? (
                <div className="text-center py-12">
                  <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-primary-600 border-t-transparent dark:border-primary-400"></div>
                  <p className="mt-4 text-slate-600 dark:text-slate-400">{t('corr.overview.loading', 'Lade Analyse...')}</p>
                </div>
              ) : correlationAnalysis ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
                  <motion.div 
                    whileHover={{ scale: 1.02 }}
                    className="bg-gradient-to-br from-primary-50 to-primary-100 dark:from-primary-900/20 dark:to-primary-800/20 p-5 rounded-xl border border-primary-200 dark:border-primary-800"
                  >
                    <div className="text-3xl font-bold text-primary-600 dark:text-primary-400">
                      {correlationAnalysis.total_alerts_analyzed}
                    </div>
                    <div className="text-sm font-medium text-primary-700 dark:text-primary-300 mt-1">
                      {t('corr.overview.analyzed', 'Analysierte Alerts')}
                    </div>
                  </motion.div>
                  <motion.div 
                    whileHover={{ scale: 1.02 }}
                    className="bg-gradient-to-br from-green-50 to-green-100 dark:from-green-900/20 dark:to-green-800/20 p-5 rounded-xl border border-green-200 dark:border-green-800"
                  >
                    <div className="text-3xl font-bold text-green-600 dark:text-green-400">
                      {correlationAnalysis.correlations_found}
                    </div>
                    <div className="text-sm font-medium text-green-700 dark:text-green-300 mt-1">
                      {t('corr.overview.found', 'Korrelationen gefunden')}
                    </div>
                  </motion.div>
                  <motion.div 
                    whileHover={{ scale: 1.02 }}
                    className="bg-gradient-to-br from-purple-50 to-purple-100 dark:from-purple-900/20 dark:to-purple-800/20 p-5 rounded-xl border border-purple-200 dark:border-purple-800"
                  >
                    <div className="text-3xl font-bold text-purple-600 dark:text-purple-400">
                      {(correlationAnalysis.correlation_rate * 100).toFixed(1)}%
                    </div>
                    <div className="text-sm font-medium text-purple-700 dark:text-purple-300 mt-1">
                      {t('corr.overview.rate', 'Korrelations-Rate')}
                    </div>
                  </motion.div>
                  <motion.div 
                    whileHover={{ scale: 1.02 }}
                    className="bg-gradient-to-br from-orange-50 to-orange-100 dark:from-orange-900/20 dark:to-orange-800/20 p-5 rounded-xl border border-orange-200 dark:border-orange-800"
                  >
                    <div className="text-3xl font-bold text-orange-600 dark:text-orange-400">
                      {correlationAnalysis.correlation_details?.length || 0}
                    </div>
                    <div className="text-sm font-medium text-orange-700 dark:text-orange-300 mt-1">
                      {t('corr.overview.active_rules', 'Aktive Regeln')}
                    </div>
                  </motion.div>
                </div>
              ) : (
                <div className="text-center py-12 text-slate-500 dark:text-slate-400">
                  {t('corr.overview.empty', 'Keine Analyse-Daten verfügbar')}
                </div>
              )}
            </div>

            {/* Correlation Rules */}
            <div className="bg-card p-6 rounded-xl shadow-lg border border-border">
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2 text-slate-900 dark:text-white">
                <div className="p-2 bg-indigo-100 dark:bg-indigo-900/30 rounded-lg">
                  <Network className="h-5 w-5 text-indigo-600 dark:text-indigo-400" />
                </div>
                {t('corr.rules.title', 'Korrelations-Regeln')}
              </h3>

              {rulesLoading ? (
                <div className="text-center py-12">
                  <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-indigo-600 border-t-transparent dark:border-indigo-400"></div>
                  <p className="mt-4 text-slate-600 dark:text-slate-400">{t('corr.rules.loading', 'Lade Regeln...')}</p>
                </div>
              ) : correlationRules?.rules ? (
                <div className="space-y-4">
                  {Object.entries(correlationRules.rules).map(([ruleName, ruleConfig]: [string, any], idx) => (
                    <motion.div 
                      key={ruleName}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: idx * 0.1 }}
                      className="border border-border rounded-xl p-5 bg-card hover:shadow-md transition-shadow"
                    >
                      <div className="flex justify-between items-start mb-3">
                        <div>
                          <h4 className="font-semibold text-slate-900 dark:text-white">{ruleName}</h4>
                          <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
                            {t('corr.rules.window', 'Zeitfenster')}: <span className="font-medium">{Math.floor(ruleConfig.time_window / 60)}</span> {t('corr.rules.minutes', 'Minuten')}
                          </p>
                        </div>
                        <span className={`px-3 py-1.5 rounded-lg text-xs font-semibold ${getSeverityBgColor(ruleConfig.min_severity)}`}>
                          {t('corr.rules.min', 'Min')} {ruleConfig.min_severity}
                        </span>
                      </div>

                      <div className="mb-3">
                        <div className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                          {t('corr.rules.required_patterns', 'Erforderliche Patterns:')}
                        </div>
                        <div className="flex flex-wrap gap-2">
                          {ruleConfig.patterns.map((pattern: string, index: number) => (
                            <span 
                              key={index} 
                              className="px-3 py-1 bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 rounded-lg text-xs font-medium"
                            >
                              {pattern}
                            </span>
                          ))}
                        </div>
                      </div>

                      <div className="text-xs text-slate-500 dark:text-slate-400 flex items-center gap-1">
                        <Sparkles className="h-3 w-3" />
                        {t('corr.rules.footer', 'Erkennt komplexe Bedrohungsmuster durch kombinierte Alert-Patterns')}
                      </div>
                    </motion.div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12 text-slate-500 dark:text-slate-400">
                  {t('corr.rules.empty', 'Keine Korrelations-Regeln verfügbar')}
                </div>
              )}
            </div>

            {/* Recent Correlations */}
            {correlationAnalysis?.correlation_details && correlationAnalysis.correlation_details.length > 0 && (
              <div className="bg-card p-6 rounded-xl shadow-lg border border-border">
                <h3 className="text-lg font-semibold mb-4 flex items-center gap-2 text-slate-900 dark:text-white">
                  <div className="p-2 bg-amber-100 dark:bg-amber-900/30 rounded-lg">
                    <Target className="h-5 w-5 text-amber-600 dark:text-amber-400" />
                  </div>
                  {t('corr.recent.title', 'Aktuelle Korrelationen')}
                </h3>

                <div className="space-y-3">
                  {correlationAnalysis.correlation_details.slice(0, 10).map((detail: any, index: number) => (
                    <motion.div 
                      key={index}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.05 }}
                      className="flex items-center justify-between p-4 bg-muted rounded-lg border border-border hover:shadow-md transition-all"
                    >
                      <div className="flex-1">
                        <div className="font-semibold text-slate-900 dark:text-white">{detail.rule_name}</div>
                        <div className="text-sm text-slate-600 dark:text-slate-400 mt-1">
                          <span className="font-medium">{t('corr.recent.triggered', 'Ausgelöst durch')}:</span> {detail.triggering_alert}
                        </div>
                      </div>
                      <div className="text-right ml-4">
                        <div className={`text-sm font-bold ${getSeverityColor(detail.severity)} uppercase`}>
                          {detail.severity}
                        </div>
                        <div className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                          {detail.matched_alerts} Patterns
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </div>
              </div>
            )}

            {/* Extended Alert Rules Overview */}
            <div className="bg-card p-6 rounded-xl shadow-lg border border-border">
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2 text-slate-900 dark:text-white">
                <div className="p-2 bg-yellow-100 dark:bg-yellow-900/30 rounded-lg">
                  <Zap className="h-5 w-5 text-yellow-600 dark:text-yellow-400" />
                </div>
                {t('corr.extended.title', 'Erweiterte Alert-Regeln Übersicht')}
              </h3>

              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
                {[
                  { name: 'Anomaly Detection', icon: Brain, count: suppressionStats?.suppressions_by_alert_type?.anomaly_detection || 0, color: 'purple' },
                  { name: 'Smart Contract Exploits', icon: Shield, count: suppressionStats?.suppressions_by_alert_type?.smart_contract_exploit || 0, color: 'red' },
                  { name: 'Flash Loan Attacks', icon: Zap, count: suppressionStats?.suppressions_by_alert_type?.flash_loan_attack || 0, color: 'yellow' },
                  { name: 'Money Laundering', icon: Layers, count: suppressionStats?.suppressions_by_alert_type?.money_laundering_pattern || 0, color: 'orange' },
                  { name: 'Ponzi Schemes', icon: TrendingUp, count: suppressionStats?.suppressions_by_alert_type?.ponzi_scheme || 0, color: 'pink' },
                  { name: 'Rug Pulls', icon: AlertTriangle, count: suppressionStats?.suppressions_by_alert_type?.rug_pull || 0, color: 'red' },
                  { name: 'Insider Trading', icon: Users, count: suppressionStats?.suppressions_by_alert_type?.insider_trading || 0, color: 'blue' },
                  { name: 'Dark Web', icon: Network, count: suppressionStats?.suppressions_by_alert_type?.dark_web_connection || 0, color: 'slate' },
                  { name: 'Whale Movements', icon: DollarSign, count: suppressionStats?.suppressions_by_alert_type?.whale_movement || 0, color: 'green' },
                  { name: 'Cross-Chain Arbitrage', icon: GitBranch, count: suppressionStats?.suppressions_by_alert_type?.cross_chain_arbitrage || 0, color: 'indigo' },
                ].map((rule, index) => {
                  const Icon = rule.icon;
                  return (
                    <motion.div 
                      key={index}
                      whileHover={{ scale: 1.05 }}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.05 }}
                      className="bg-card p-4 rounded-lg text-center border border-border hover:shadow-md transition-all"
                    >
                      <Icon className={`h-6 w-6 mx-auto mb-2 ${iconColor(rule.color)}`} />
                      <div className="text-xl font-bold text-slate-900 dark:text-white">{rule.count}</div>
                      <div className="text-xs text-slate-600 dark:text-slate-400 mt-1">{rule.name}</div>
                    </motion.div>
                  );
                })}
              </div>
            </div>

            {/* Suppression Breakdown */}
            {suppressionStats && (
              <div className="bg-card p-6 rounded-xl shadow-lg border border-border">
                <h3 className="text-lg font-semibold mb-4 flex items-center gap-2 text-slate-900 dark:text-white">
                  <div className="p-2 bg-cyan-100 dark:bg-cyan-900/30 rounded-lg">
                    <BarChart3 className="h-5 w-5 text-cyan-600 dark:text-cyan-400" />
                  </div>
                  {t('corr.suppressions.breakdown.title', 'Suppression-Aufschlüsselung')}
                </h3>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <h4 className="text-sm font-semibold mb-3 text-slate-700 dark:text-slate-300 flex items-center gap-2">
                      <div className="h-1 w-1 rounded-full bg-cyan-600 dark:bg-cyan-400"></div>
                      {t('corr.suppressions.breakdown.by_reason', 'Nach Grund')}
                    </h4>
                    <div className="space-y-2">
                      {Object.entries(suppressionStats.suppressions_by_reason as Record<string, number>).map(([reason, count], idx) => (
                        <motion.div 
                          key={reason}
                          initial={{ opacity: 0, x: -10 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: idx * 0.05 }}
                          className="flex justify-between items-center p-2 bg-muted rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                        >
                          <span className="text-sm text-slate-600 dark:text-slate-400 capitalize">{reason.replace(/_/g, ' ')}</span>
                          <span className="font-bold text-slate-900 dark:text-white">{count}</span>
                        </motion.div>
                      ))}
                    </div>
                  </div>

                  <div>
                    <h4 className="text-sm font-semibold mb-3 text-slate-700 dark:text-slate-300 flex items-center gap-2">
                      <div className="h-1 w-1 rounded-full bg-cyan-600 dark:bg-cyan-400"></div>
                      {t('corr.suppressions.breakdown.by_type', 'Nach Alert-Typ')}
                    </h4>
                    <div className="space-y-2">
                      {Object.entries(suppressionStats.suppressions_by_alert_type as Record<string, number>).slice(0, 8).map(([alertType, count], idx) => (
                        <motion.div 
                          key={alertType}
                          initial={{ opacity: 0, x: -10 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: idx * 0.05 }}
                          className="flex justify-between items-center p-2 bg-muted rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                        >
                          <span className="text-sm text-slate-600 dark:text-slate-400 capitalize">{alertType.replace(/_/g, ' ')}</span>
                          <span className="font-bold text-slate-900 dark:text-white">{count}</span>
                        </motion.div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </motion.div>
        </div>
      </div>
    </div>
  );
};

export default CorrelationAnalysisPage;

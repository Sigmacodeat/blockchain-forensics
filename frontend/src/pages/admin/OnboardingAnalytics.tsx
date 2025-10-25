/**
 * Onboarding Analytics Dashboard
 * ================================
 * 
 * Admin-Dashboard für Tour-Completion-Metriken:
 * - Completion Rate per Plan
 * - Total Starts/Completions/Skips
 * - Step-by-Step Funnel
 * - Temporal Trends
 */

import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { 
  BarChart3, 
  TrendingUp, 
  Users, 
  CheckCircle2, 
  XCircle, 
  Activity,
  Download,
  RefreshCw,
  Sparkles
} from 'lucide-react';
import { 
  getCompletionStats, 
  exportAnalyticsData, 
  clearAnalyticsData 
} from '@/lib/onboarding-analytics';
import type { TourCompletionStats } from '@/lib/onboarding-analytics';
import type { PlanId } from '@/lib/features';

export default function OnboardingAnalytics() {
  const [stats, setStats] = useState<TourCompletionStats | null>(null);
  const [loading, setLoading] = useState(true);

  const loadStats = () => {
    setLoading(true);
    try {
      const data = getCompletionStats();
      setStats(data);
    } catch (error) {
      console.error('Failed to load stats:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadStats();
  }, []);

  const handleExport = () => {
    const data = exportAnalyticsData();
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `onboarding-analytics-${new Date().toISOString()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleClear = () => {
    if (confirm('Möchtest du wirklich alle Analytics-Daten löschen? Dies kann nicht rückgängig gemacht werden.')) {
      clearAnalyticsData();
      loadStats();
    }
  };

  if (loading) {
    return (
      <div className="container mx-auto p-6">
        <div className="flex items-center justify-center h-64">
          <RefreshCw className="w-8 h-8 animate-spin text-primary" />
        </div>
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="container mx-auto p-6">
        <Card>
          <CardContent className="pt-6">
            <div className="text-center text-muted-foreground">
              Keine Analytics-Daten verfügbar
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  const planColors: Record<PlanId, string> = {
    starter: 'bg-gray-400',
    community: 'bg-gray-500',
    pro: 'bg-blue-500',
    plus: 'bg-purple-500',
    business: 'bg-orange-500',
    enterprise: 'bg-red-500',
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between"
      >
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Sparkles className="w-8 h-8 text-primary" />
            Onboarding Analytics
          </h1>
          <p className="text-muted-foreground mt-1">
            Tour-Completion-Metriken und User-Engagement
          </p>
        </div>
        <div className="flex gap-2">
          <Button onClick={loadStats} variant="outline" size="sm">
            <RefreshCw className="w-4 h-4 mr-2" />
            Aktualisieren
          </Button>
          <Button onClick={handleExport} variant="outline" size="sm">
            <Download className="w-4 h-4 mr-2" />
            Export
          </Button>
          <Button onClick={handleClear} variant="destructive" size="sm">
            <XCircle className="w-4 h-4 mr-2" />
            Löschen
          </Button>
        </div>
      </motion.div>

      {/* Overall Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Starts</CardTitle>
              <Users className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.total_starts}</div>
              <p className="text-xs text-muted-foreground">
                Gestartete Tours insgesamt
              </p>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Completions</CardTitle>
              <CheckCircle2 className="h-4 w-4 text-green-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-600">{stats.total_completions}</div>
              <p className="text-xs text-muted-foreground">
                Erfolgreich abgeschlossen
              </p>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Completion Rate</CardTitle>
              <TrendingUp className="h-4 w-4 text-blue-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-blue-600">
                {stats.completion_rate.toFixed(1)}%
              </div>
              <p className="text-xs text-muted-foreground">
                {stats.total_starts > 0 ? 'Durchschnittliche Rate' : 'Keine Daten'}
              </p>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
        >
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Skips</CardTitle>
              <XCircle className="h-4 w-4 text-red-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-red-600">{stats.total_skips}</div>
              <p className="text-xs text-muted-foreground">
                Abgebrochen
              </p>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Plan-Specific Stats */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
      >
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="w-5 h-5" />
              Completion Rate per Plan
            </CardTitle>
            <CardDescription>
              Vergleich der Tour-Performance nach Subscription-Plan
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {Object.entries(stats.by_plan).length === 0 ? (
                <div className="text-center text-muted-foreground py-8">
                  Keine Plan-spezifischen Daten verfügbar
                </div>
              ) : (
                Object.entries(stats.by_plan).map(([plan, planStats]) => (
                  <div key={plan} className="space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Badge className={planColors[plan as PlanId]}>
                          {plan.toUpperCase()}
                        </Badge>
                        <span className="text-sm text-muted-foreground">
                          {planStats.starts} starts
                        </span>
                      </div>
                      <div className="flex items-center gap-4">
                        <span className="text-sm">
                          <span className="text-green-600 font-medium">
                            {planStats.completions} ✓
                          </span>
                          {' / '}
                          <span className="text-red-600 font-medium">
                            {planStats.skips} ✗
                          </span>
                        </span>
                        <span className="text-sm font-bold">
                          {planStats.completion_rate.toFixed(1)}%
                        </span>
                      </div>
                    </div>
                    {/* Progress Bar */}
                    <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full ${planColors[plan as PlanId]}`}
                        style={{ width: `${planStats.completion_rate}%` }}
                      />
                    </div>
                  </div>
                ))
              )}
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Additional Metrics */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.6 }}
      >
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="w-5 h-5" />
              Zusätzliche Metriken
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <div className="text-sm text-muted-foreground">Durchschnittlich abgeschlossene Steps</div>
                <div className="text-2xl font-bold">
                  {stats.average_steps_completed.toFixed(1)}
                </div>
              </div>
              <div className="space-y-2">
                <div className="text-sm text-muted-foreground">Skip-Rate</div>
                <div className="text-2xl font-bold">
                  {stats.total_starts > 0 
                    ? ((stats.total_skips / stats.total_starts) * 100).toFixed(1)
                    : '0'}%
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Insights */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.7 }}
      >
        <Card>
          <CardHeader>
            <CardTitle>💡 Insights</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {stats.completion_rate >= 70 && (
              <div className="p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded">
                <p className="text-sm text-green-700 dark:text-green-300">
                  ✅ Ausgezeichnete Completion-Rate! Die Tour ist gut designed.
                </p>
              </div>
            )}
            {stats.completion_rate < 50 && stats.total_starts > 10 && (
              <div className="p-3 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded">
                <p className="text-sm text-yellow-700 dark:text-yellow-300">
                  ⚠️ Niedrige Completion-Rate. Erwäge Tour-Verbesserungen.
                </p>
              </div>
            )}
            {stats.average_steps_completed < 3 && (
              <div className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded">
                <p className="text-sm text-red-700 dark:text-red-300">
                  🚨 User brechen früh ab. Prüfe die ersten Steps auf Klarheit.
                </p>
              </div>
            )}
            {stats.total_starts === 0 && (
              <div className="p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded">
                <p className="text-sm text-blue-700 dark:text-blue-300">
                  ℹ️ Noch keine Tour-Daten vorhanden. Lade neue User ein!
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
}

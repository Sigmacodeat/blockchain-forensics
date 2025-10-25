'use client';

import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Activity, AlertCircle, CheckCircle2, Clock, TrendingUp } from 'lucide-react';
import { useKYTStream, type KYTResult } from '@/hooks/useKYTStream';
import { useNavigate } from 'react-router-dom';

export function KYTMonitor() {
  const { connected, results, error } = useKYTStream();
  const navigate = useNavigate();

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'critical':
        return 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300 border-red-300 dark:border-red-700';
      case 'high':
        return 'bg-orange-100 dark:bg-orange-900/30 text-orange-800 dark:text-orange-300 border-orange-300 dark:border-orange-700';
      case 'medium':
        return 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-300 border-yellow-300 dark:border-yellow-700';
      case 'low':
        return 'bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300 border-blue-300 dark:border-blue-700';
      default:
        return 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300 border-green-300 dark:border-green-700';
    }
  };

  const getRiskIcon = (level: string) => {
    switch (level) {
      case 'critical':
      case 'high':
        return <AlertCircle className="w-4 h-4" />;
      case 'medium':
      case 'low':
        return <TrendingUp className="w-4 h-4" />;
      default:
        return <CheckCircle2 className="w-4 h-4" />;
    }
  };

  return (
    <Card className="col-span-full lg:col-span-2">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Activity className="w-5 h-5" />
              KYT Monitor (Real-Time)
            </CardTitle>
            <CardDescription>
              Live Transaction Risk Analysis
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <div
              className={`w-2 h-2 rounded-full ${
                connected
                  ? 'bg-green-500 animate-pulse shadow-[0_0_8px_rgba(34,197,94,0.6)]'
                  : 'bg-gray-400'
              }`}
            />
            <span className="text-xs text-muted-foreground">
              {connected ? 'Live' : 'Offline'}
            </span>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {error && (
          <div className="mb-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
            <p className="text-sm text-red-700 dark:text-red-300">⚠️ {error}</p>
          </div>
        )}

        {results.length === 0 ? (
          <div className="text-center py-12 bg-gradient-to-br from-gray-50 to-gray-100 dark:from-slate-800/50 dark:to-slate-900/50 rounded-xl border border-gray-200 dark:border-slate-700">
            <Activity className="w-12 h-12 mx-auto text-gray-400 dark:text-gray-500 mb-4 opacity-50" />
            <p className="text-gray-700 dark:text-gray-300 font-medium mb-2">
              Warte auf Transaktionen...
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              Real-Time Analysen erscheinen automatisch
            </p>
          </div>
        ) : (
          <div className="space-y-3 max-h-[400px] overflow-y-auto">
            {results.map((result: KYTResult, idx: number) => (
              <div
                key={`${result.tx_hash}-${idx}`}
                className="p-4 rounded-lg border bg-gradient-to-r from-white to-gray-50 dark:from-slate-800 dark:to-slate-900 hover:border-primary-300 dark:hover:border-primary-600 transition-all"
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-2">
                    {getRiskIcon(result.risk_level)}
                    <Badge className={`${getRiskColor(result.risk_level)} border`}>
                      {result.risk_level.toUpperCase()}
                    </Badge>
                    <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                      Score: {(result.risk_score * 100).toFixed(0)}%
                    </span>
                  </div>
                  <div className="flex items-center gap-1 text-xs text-muted-foreground">
                    <Clock className="w-3 h-3" />
                    {result.analysis_time_ms.toFixed(0)}ms
                  </div>
                </div>

                <code className="text-xs font-mono block px-3 py-2 bg-gray-100 dark:bg-slate-900/50 border border-gray-200 dark:border-slate-700 rounded mb-3 text-gray-700 dark:text-gray-300">
                  {result.tx_hash}
                </code>

                {result.alerts.length > 0 && (
                  <div className="mb-3 space-y-2">
                    {result.alerts.slice(0, 2).map((alert, aidx) => (
                      <div
                        key={aidx}
                        className="text-xs p-2 bg-orange-50 dark:bg-orange-900/20 border border-orange-200 dark:border-orange-800 rounded"
                      >
                        <p className="font-medium text-orange-800 dark:text-orange-300">
                          {alert.title}
                        </p>
                        <p className="text-orange-700 dark:text-orange-400">
                          {alert.description}
                        </p>
                      </div>
                    ))}
                    {result.alerts.length > 2 && (
                      <p className="text-xs text-muted-foreground">
                        +{result.alerts.length - 2} weitere Alerts
                      </p>
                    )}
                  </div>
                )}

                <div className="flex items-center gap-2">
                  {(result.from_labels.length > 0 || result.to_labels.length > 0) && (
                    <div className="flex-1 text-xs text-muted-foreground">
                      Labels: {[...result.from_labels, ...result.to_labels].slice(0, 3).join(', ')}
                    </div>
                  )}
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => navigate(`/trace?tx=${result.tx_hash}`)}
                    className="text-xs"
                  >
                    Trace
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

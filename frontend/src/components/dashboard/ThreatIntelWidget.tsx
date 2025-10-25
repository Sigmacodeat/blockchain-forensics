'use client';

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Shield, AlertTriangle, TrendingUp, Activity, Database } from 'lucide-react';
import { api } from '@/lib/api';

interface ThreatIntelStats {
  total_intel_items: number;
  active_threats: number;
  critical_threats: number;
  feeds_updated: string;
  darkweb_hits: number;
  community_reports: number;
}

export function ThreatIntelWidget() {
  const { data: stats, isLoading, error } = useQuery<ThreatIntelStats>({
    queryKey: ['threatIntelStats'],
    queryFn: async () => {
      const response = await api.get('/api/v1/threat-intel/statistics');
      return response.data;
    },
    refetchInterval: 60000, // Refresh every minute
  });

  return (
    <Card className="lg:col-span-1">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Shield className="w-5 h-5 text-primary-600 dark:text-primary-400" />
          Threat Intelligence
        </CardTitle>
        <CardDescription>
          Live-Bedrohungsinformationen
        </CardDescription>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-16 bg-gray-100 dark:bg-slate-800 rounded-lg animate-pulse" />
            ))}
          </div>
        ) : error ? (
          <div className="text-center py-8 text-sm text-red-600 dark:text-red-400">
            ⚠️ Fehler beim Laden der Daten
          </div>
        ) : (
          <div className="space-y-3">
            {/* Critical Threats */}
            <div className="p-4 rounded-lg bg-gradient-to-r from-red-50 to-red-100 dark:from-red-900/20 dark:to-red-900/10 border border-red-200 dark:border-red-800">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-red-600 dark:text-red-400" />
                  <span className="text-sm font-medium text-red-900 dark:text-red-300">
                    Kritische Bedrohungen
                  </span>
                </div>
                <Badge variant="destructive" className="font-bold">
                  {stats?.critical_threats || 0}
                </Badge>
              </div>
              <p className="text-xs text-red-700 dark:text-red-400">
                Erfordern sofortige Aufmerksamkeit
              </p>
            </div>

            {/* Active Threats */}
            <div className="p-4 rounded-lg bg-gradient-to-r from-orange-50 to-orange-100 dark:from-orange-900/20 dark:to-orange-900/10 border border-orange-200 dark:border-orange-800">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 text-orange-600 dark:text-orange-400" />
                  <span className="text-sm font-medium text-orange-900 dark:text-orange-300">
                    Aktive Bedrohungen
                  </span>
                </div>
                <Badge className="bg-orange-200 dark:bg-orange-900/50 text-orange-900 dark:text-orange-300 border-orange-300 dark:border-orange-700">
                  {stats?.active_threats || 0}
                </Badge>
              </div>
              <p className="text-xs text-orange-700 dark:text-orange-400">
                Werden aktiv überwacht
              </p>
            </div>

            {/* Intel Database */}
            <div className="p-4 rounded-lg bg-gradient-to-r from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-900/10 border border-blue-200 dark:border-blue-800">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <Database className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                  <span className="text-sm font-medium text-blue-900 dark:text-blue-300">
                    Intel-Datenbank
                  </span>
                </div>
                <Badge className="bg-blue-200 dark:bg-blue-900/50 text-blue-900 dark:text-blue-300 border-blue-300 dark:border-blue-700">
                  {stats?.total_intel_items?.toLocaleString() || 0}
                </Badge>
              </div>
              <p className="text-xs text-blue-700 dark:text-blue-400">
                Threat Intelligence Items
              </p>
            </div>

            {/* Dark Web + Community */}
            <div className="grid grid-cols-2 gap-2">
              <div className="p-3 rounded-lg bg-gray-50 dark:bg-slate-800/50 border border-gray-200 dark:border-slate-700">
                <div className="text-xs text-muted-foreground mb-1">Dark Web</div>
                <div className="text-lg font-bold text-gray-900 dark:text-white">
                  {stats?.darkweb_hits || 0}
                </div>
              </div>
              <div className="p-3 rounded-lg bg-gray-50 dark:bg-slate-800/50 border border-gray-200 dark:border-slate-700">
                <div className="text-xs text-muted-foreground mb-1">Community</div>
                <div className="text-lg font-bold text-gray-900 dark:text-white">
                  {stats?.community_reports || 0}
                </div>
              </div>
            </div>

            {/* Last Update */}
            {stats?.feeds_updated && (
              <div className="pt-3 border-t border-gray-200 dark:border-slate-700">
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <Activity className="w-3 h-3" />
                  <span>
                    Aktualisiert:{' '}
                    {new Date(stats.feeds_updated).toLocaleTimeString('de-DE', {
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </span>
                </div>
              </div>
            )}

            {/* Action Button */}
            <Button
              variant="outline"
              className="w-full mt-3"
              onClick={() => window.location.href = '/threat-intel'}
            >
              Details anzeigen
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

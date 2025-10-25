'use client';

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { api } from '@/lib/api';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface RiskAddress {
  address: string;
  risk_score: number;
  risk_level: string;
  change_24h: number;
  tx_count: number;
  labels: string[];
}

export function RiskHeatmap() {
  const { data, isLoading } = useQuery<RiskAddress[]>({
    queryKey: ['riskHeatmap'],
    queryFn: async () => {
      const response = await api.get('/api/v1/analytics/top-risk-addresses?limit=20');
      return response.data;
    },
    refetchInterval: 60000, // Refresh every minute
  });

  const getRiskColor = (score: number) => {
    if (score >= 0.9) return 'bg-red-600';
    if (score >= 0.6) return 'bg-orange-500';
    if (score >= 0.3) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  const getTrendIcon = (change: number) => {
    if (change > 0.05) return <TrendingUp className="w-4 h-4 text-red-600" />;
    if (change < -0.05) return <TrendingDown className="w-4 h-4 text-green-600" />;
    return <Minus className="w-4 h-4 text-gray-400" />;
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Top Risk Addresses</CardTitle>
        <CardDescription>
          Adressen mit den höchsten Risk-Scores diese Woche
        </CardDescription>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="text-center py-8 text-muted-foreground">
            Lädt Heatmap...
          </div>
        ) : (
          <div className="space-y-4">
            {/* Heatmap Grid */}
            <div className="grid grid-cols-4 md:grid-cols-8 gap-2">
              {data?.slice(0, 32).map((addr, idx) => (
                <div
                  key={addr.address}
                  className={`aspect-square rounded ${getRiskColor(
                    addr.risk_score
                  )} cursor-pointer hover:scale-110 transition-transform relative group`}
                  title={`${addr.address}\nRisk: ${(addr.risk_score * 100).toFixed(1)}%`}
                >
                  <div className="absolute inset-0 flex items-center justify-center text-white text-xs font-bold opacity-0 group-hover:opacity-100 transition-opacity">
                    {(addr.risk_score * 100).toFixed(0)}
                  </div>
                </div>
              ))}
            </div>

            {/* Top 10 List */}
            <div className="mt-6 space-y-2">
              <h4 className="font-semibold text-sm mb-3">Top 10 Details:</h4>
              {data?.slice(0, 10).map((addr, idx) => (
                <div
                  key={addr.address}
                  className="flex items-center justify-between p-3 border rounded-lg hover:bg-accent transition-colors"
                >
                  <div className="flex items-center gap-3 flex-1">
                    <span className="text-sm font-semibold text-muted-foreground w-6">
                      #{idx + 1}
                    </span>
                    <code className="text-xs font-mono truncate max-w-[200px]">
                      {addr.address}
                    </code>
                    <Badge
                      className={
                        addr.risk_level === 'critical'
                          ? 'bg-red-100 text-red-800'
                          : addr.risk_level === 'high'
                          ? 'bg-orange-100 text-orange-800'
                          : 'bg-yellow-100 text-yellow-800'
                      }
                    >
                      {(addr.risk_score * 100).toFixed(1)}%
                    </Badge>
                  </div>

                  <div className="flex items-center gap-3">
                    {getTrendIcon(addr.change_24h)}
                    <span className="text-xs text-muted-foreground">
                      {addr.tx_count} TXs
                    </span>
                    <Button size="sm" variant="ghost">
                      Details
                    </Button>
                  </div>
                </div>
              ))}
            </div>

            {/* Legend */}
            <div className="flex items-center justify-center gap-6 pt-4 border-t text-xs">
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 bg-red-600 rounded" />
                <span>Critical (90%+)</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 bg-orange-500 rounded" />
                <span>High (60-90%)</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 bg-yellow-500 rounded" />
                <span>Medium (30-60%)</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 bg-green-500 rounded" />
                <span>Low (&lt;30%)</span>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

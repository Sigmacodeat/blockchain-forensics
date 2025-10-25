'use client';

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Area,
  AreaChart,
} from 'recharts';
import { api } from '@/lib/api';
import { TrendingUp, Activity, AlertCircle } from 'lucide-react';

interface TrendData {
  timestamp: string;
  traces: number;
  alerts: number;
  high_risk: number;
  avg_risk_score: number;
}

interface RiskDistribution {
  level: string;
  count: number;
  percentage: number;
}

export function TrendCharts() {
  // Trend-Daten (letzte 30 Tage)
  const { data: trendData, isLoading: trendLoading } = useQuery<TrendData[]>({
    queryKey: ['trends', '30d'],
    queryFn: async () => {
      const response = await api.get('/api/v1/analytics/trends?period=30d');
      return response.data;
    },
    refetchInterval: 300000, // 5 min
  });

  // Risk Distribution
  const { data: riskDist, isLoading: riskLoading } = useQuery<RiskDistribution[]>({
    queryKey: ['riskDistribution'],
    queryFn: async () => {
      const response = await api.get('/api/v1/analytics/risk-distribution');
      return response.data;
    },
    refetchInterval: 60000,
  });

  const COLORS = {
    critical: '#ef4444',
    high: '#f97316',
    medium: '#eab308',
    low: '#22c55e',
  };

  const PIE_COLORS = ['#ef4444', '#f97316', '#eab308', '#22c55e'];

  return (
    <div className="space-y-6">
      <Tabs defaultValue="traces">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="traces">
            <TrendingUp className="w-4 h-4 mr-2" />
            Traces Over Time
          </TabsTrigger>
          <TabsTrigger value="alerts">
            <AlertCircle className="w-4 h-4 mr-2" />
            Alerts Trend
          </TabsTrigger>
          <TabsTrigger value="risk">
            <Activity className="w-4 h-4 mr-2" />
            Risk Distribution
          </TabsTrigger>
        </TabsList>

        {/* Traces Trend */}
        <TabsContent value="traces">
          <Card>
            <CardHeader>
              <CardTitle>Transaction Traces - Last 30 Days</CardTitle>
              <CardDescription>
                Anzahl der durchgeführten Traces und durchschnittlicher Risk-Score
              </CardDescription>
            </CardHeader>
            <CardContent>
              {trendLoading ? (
                <div className="h-80 flex items-center justify-center">
                  <p className="text-muted-foreground">Lädt Chart-Daten...</p>
                </div>
              ) : (
                <ResponsiveContainer width="100%" height={400}>
                  <AreaChart data={trendData}>
                    <defs>
                      <linearGradient id="colorTraces" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8} />
                        <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis
                      dataKey="timestamp"
                      tickFormatter={(val) =>
                        new Date(val).toLocaleDateString('de-DE', {
                          month: 'short',
                          day: 'numeric',
                        })
                      }
                    />
                    <YAxis />
                    <Tooltip
                      labelFormatter={(val) => new Date(val).toLocaleDateString('de-DE')}
                      formatter={(value: number, name: string) => [
                        name === 'traces' ? value : `${(value * 100).toFixed(1)}%`,
                        name === 'traces' ? 'Traces' : 'Avg Risk Score',
                      ]}
                    />
                    <Legend />
                    <Area
                      type="monotone"
                      dataKey="traces"
                      stroke="#3b82f6"
                      fillOpacity={1}
                      fill="url(#colorTraces)"
                    />
                    <Line
                      type="monotone"
                      dataKey="avg_risk_score"
                      stroke="#f97316"
                      strokeWidth={2}
                      dot={{ r: 3 }}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Alerts Trend */}
        <TabsContent value="alerts">
          <Card>
            <CardHeader>
              <CardTitle>Security Alerts - Trend Analysis</CardTitle>
              <CardDescription>Entwicklung der Alerts und High-Risk-Detections</CardDescription>
            </CardHeader>
            <CardContent>
              {trendLoading ? (
                <div className="h-80 flex items-center justify-center">
                  <p className="text-muted-foreground">Lädt Chart-Daten...</p>
                </div>
              ) : (
                <ResponsiveContainer width="100%" height={400}>
                  <LineChart data={trendData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis
                      dataKey="timestamp"
                      tickFormatter={(val) =>
                        new Date(val).toLocaleDateString('de-DE', {
                          month: 'short',
                          day: 'numeric',
                        })
                      }
                    />
                    <YAxis />
                    <Tooltip
                      labelFormatter={(val) => new Date(val).toLocaleDateString('de-DE')}
                    />
                    <Legend />
                    <Line
                      type="monotone"
                      dataKey="alerts"
                      stroke="#eab308"
                      strokeWidth={2}
                      name="Total Alerts"
                    />
                    <Line
                      type="monotone"
                      dataKey="high_risk"
                      stroke="#ef4444"
                      strokeWidth={2}
                      name="High-Risk Detections"
                    />
                  </LineChart>
                </ResponsiveContainer>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Risk Distribution */}
        <TabsContent value="risk">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Risk Level Distribution</CardTitle>
                <CardDescription>Verteilung nach Risk-Level (Pie Chart)</CardDescription>
              </CardHeader>
              <CardContent>
                {riskLoading ? (
                  <div className="h-80 flex items-center justify-center">
                    <p className="text-muted-foreground">Lädt...</p>
                  </div>
                ) : (
                  <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                      <Pie
                        data={riskDist}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={({ level, percentage }) =>
                          `${level}: ${percentage.toFixed(1)}%`
                        }
                        outerRadius={100}
                        fill="#8884d8"
                        dataKey="count"
                      >
                        {riskDist?.map((entry, index) => (
                          <Cell
                            key={`cell-${index}`}
                            fill={PIE_COLORS[index % PIE_COLORS.length]}
                          />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Risk Level Counts</CardTitle>
                <CardDescription>Absolute Anzahl pro Risk-Level (Bar Chart)</CardDescription>
              </CardHeader>
              <CardContent>
                {riskLoading ? (
                  <div className="h-80 flex items-center justify-center">
                    <p className="text-muted-foreground">Lädt...</p>
                  </div>
                ) : (
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={riskDist}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="level" />
                      <YAxis />
                      <Tooltip />
                      <Legend />
                      <Bar dataKey="count" name="Addresses">
                        {riskDist?.map((entry, index) => (
                          <Cell
                            key={`cell-${index}`}
                            fill={
                              COLORS[entry.level.toLowerCase() as keyof typeof COLORS] ||
                              '#94a3b8'
                            }
                          />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}

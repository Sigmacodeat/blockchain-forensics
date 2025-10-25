import React, { useState, useMemo } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { AlertTriangle, TrendingUp, TrendingDown, Activity, Shield, Zap } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell } from 'recharts';

interface AnalyticsData {
  risk_assessment: {
    risk_score: number;
    risk_level: string;
    confidence: number;
    top_factors: string[];
  };
  anomalies: Array<{
    anomaly_score: number;
    anomaly_factors: string[];
    address: string;
    confidence: number;
  }>;
  patterns: Array<{
    pattern_type: string;
    confidence: number;
    sequence_length: number;
  }>;
  recommendations: string[];
}

interface AdvancedAnalyticsProps {
  data: AnalyticsData;
  address: string;
  onRefresh?: () => void;
  isLoading?: boolean;
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

function AdvancedAnalytics({ data, address, onRefresh, isLoading }: AdvancedAnalyticsProps) {
  const [selectedTimeRange, setSelectedTimeRange] = useState('7d');
  const [selectedMetric, setSelectedMetric] = useState('risk_score');

  // Mock time series data - in real app, this would come from API
  const timeSeriesData = useMemo(() => {
    const parsed = Number.parseInt(selectedTimeRange.replace(/[^0-9]/g, ''), 10);
    const days = Number.isFinite(parsed) && parsed > 0 ? Math.min(parsed, 365) : 7;
    return Array.from({ length: days }, (_, i) => ({
      date: new Date(Date.now() - (days - i) * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      risk_score: Math.random() * 100,
      anomaly_score: Math.random() * 50,
      tx_count: Math.floor(Math.random() * 100),
      volume: Math.random() * 10000
    }));
  }, [selectedTimeRange]);

  const patternDistribution = useMemo(() => {
    const patterns = Array.isArray(data.patterns) ? data.patterns : [];
    const grouped = patterns.reduce<Record<string, number>>((acc, pattern) => {
      const key = pattern.pattern_type;
      acc[key] = (acc[key] ?? 0) + 1;
      return acc;
    }, {});

    const total = patterns.length || 0;
    if (total === 0) return [] as Array<{ type: string; count: number; percentage: number }>;

    return Object.entries(grouped).map(([type, count]) => ({
      type,
      count,
      percentage: (count / total) * 100
    }));
  }, [data.patterns]);

  const anomalyTrend = useMemo(() => {
    return timeSeriesData.map(item => ({
      date: item.date,
      anomalies: Math.max(0, Math.floor(((Number.isFinite(item.anomaly_score) ? item.anomaly_score : 0) as number) / 10))
    }));
  }, [timeSeriesData]);

  // Helpers & local utils
  const safeFixed = (num: number, digits: number) => (Number.isFinite(num) ? num : 0).toFixed(digits)

  const riskScoreValue = data.risk_assessment?.risk_score ?? 0
  const riskLevelValue = (data.risk_assessment?.risk_level ?? 'low') as string
  const confidencePercentage = Math.round((data.risk_assessment?.confidence ?? 0) * 100)
  const anomaliesCountValue = data.anomalies?.length ?? 0
  const topRiskFactors: string[] = data.risk_assessment?.top_factors ?? []

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  // Defensive defaults/guards for UI rendering
  const recommendations = Array.isArray(data?.recommendations) ? data.recommendations : []

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Advanced Analytics</h2>
          <p className="text-gray-600">AI-powered insights for {address}</p>
        </div>
        <div className="flex items-center gap-3">
          <Select value={selectedTimeRange} onValueChange={setSelectedTimeRange}>
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="1d">1 Day</SelectItem>
              <SelectItem value="7d">7 Days</SelectItem>
              <SelectItem value="30d">30 Days</SelectItem>
              <SelectItem value="90d">90 Days</SelectItem>
            </SelectContent>
          </Select>
          <Button onClick={onRefresh} variant="outline" disabled={!onRefresh}>
            <Activity className="w-4 h-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Risk Assessment Summary */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="w-5 h-5" />
            Risk Assessment
          </CardTitle>
          <CardDescription>
            AI-powered risk analysis and recommendations
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className={`text-3xl font-bold ${getRiskColor(riskScoreValue)}`}>
                {safeFixed(riskScoreValue, 1)}
              </div>
              <div className="text-sm text-gray-600">Risk Score</div>
            </div>
            <div className="text-center">
              <Badge variant={getRiskVariant(riskLevelValue)}>
                {riskLevelValue.toUpperCase()}
              </Badge>
              <div className="text-sm text-gray-600 mt-1">Risk Level</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold">
                {confidencePercentage}%
              </div>
              <div className="text-sm text-gray-600">Confidence</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold">
                {anomaliesCountValue}
              </div>
              <div className="text-sm text-gray-600">Anomalies</div>
            </div>
          </div>

          {/* Top Risk Factors */}
          <div className="mt-6">
            <h4 className="font-semibold mb-3">Top Risk Factors</h4>
            <div className="flex flex-wrap gap-2">
              {topRiskFactors.map((factor: string, index: number) => (
                <Badge key={index} variant="outline">
                  {factor}
                </Badge>
              )) || []}
            </div>
          </div>

          {/* Recommendations */}
          {recommendations.length > 0 && (
            <div className="mt-6">
              <h4 className="font-semibold mb-3">AI Recommendations</h4>
              <div className="space-y-2">
                {recommendations.map((rec, index) => (
                  <div key={index} className="flex items-start gap-2 p-3 bg-primary-50 rounded-lg">
                    <AlertTriangle className="w-4 h-4 text-primary-600 mt-0.5 flex-shrink-0" />
                    <span className="text-sm text-primary-800">{rec}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Analytics Tabs */}
      <Tabs defaultValue="trends" className="space-y-4">
        <TabsList>
          <TabsTrigger value="trends">Risk Trends</TabsTrigger>
          <TabsTrigger value="patterns">Pattern Analysis</TabsTrigger>
          <TabsTrigger value="anomalies">Anomaly Detection</TabsTrigger>
        </TabsList>

        <TabsContent value="trends" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Risk Score Trends</CardTitle>
              <CardDescription>
                Historical risk assessment over time
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={timeSeriesData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Line
                    type="monotone"
                    dataKey="risk_score"
                    stroke="#0284c7"
                    strokeWidth={2}
                    dot={{ fill: '#0284c7' }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>Transaction Volume</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={200}>
                  <BarChart data={timeSeriesData.slice(-7)}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="tx_count" fill="#10b981" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Anomaly Trend</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={200}>
                  <LineChart data={anomalyTrend}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis />
                    <Tooltip />
                    <Line
                      type="monotone"
                      dataKey="anomalies"
                      stroke="#f59e0b"
                      strokeWidth={2}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="patterns" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Pattern Recognition</CardTitle>
              <CardDescription>
                AI-detected behavioral patterns
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h4 className="font-semibold mb-3">Detected Patterns</h4>
                  <div className="space-y-3">
                    {data.patterns?.map((pattern, index) => (
                      <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                        <div>
                          <div className="font-medium capitalize">
                            {pattern.pattern_type.replace('_', ' ')}
                          </div>
                          <div className="text-sm text-gray-600">
                            {pattern.sequence_length} transactions
                          </div>
                        </div>
                        <Badge variant="outline">
                          {(pattern.confidence * 100).toFixed(0)}%
                        </Badge>
                      </div>
                    )) || []}
                  </div>
                </div>

                <div>
                  <h4 className="font-semibold mb-3">Pattern Distribution</h4>
                  <ResponsiveContainer width="100%" height={200}>
                    <PieChart>
                      <Pie
                        data={patternDistribution}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={({ type, percentage }) => `${type}: ${safeFixed(Number(percentage), 1)}%`}
                        outerRadius={80}
                        fill="#8884d8"
                        dataKey="count"
                      >
                        {patternDistribution.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="anomalies" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Anomaly Detection</CardTitle>
              <CardDescription>
                Unusual behavior patterns detected by AI
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {(Array.isArray(data.anomalies) ? data.anomalies : []).map((anomaly, index) => (
                  <div key={index} className="p-4 border rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <Zap className="w-4 h-4 text-yellow-600" />
                        <span className="font-medium">Anomaly Detected</span>
                      </div>
                      <Badge variant="outline">
                        Score: {safeFixed(Number.isFinite(anomaly.anomaly_score) ? anomaly.anomaly_score : 0, 2)}
                      </Badge>
                    </div>

                    <div className="text-sm text-gray-600 mb-3">
                      Address: {anomaly.address || 'N/A'}
                    </div>

                    <div>
                      <h5 className="font-medium mb-2">Contributing Factors:</h5>
                      <div className="flex flex-wrap gap-1">
                        {(Array.isArray(anomaly.anomaly_factors) ? anomaly.anomaly_factors : []).map((factor, idx) => (
                          <Badge key={idx} variant="secondary" className="text-xs">
                            {factor}
                          </Badge>
                        ))}
                      </div>
                    </div>

                    <div className="mt-3 flex items-center justify-between text-sm">
                      <span>Confidence: {safeFixed((Number.isFinite(anomaly.confidence) ? anomaly.confidence : 0) * 100, 0)}%</span>
                      <Button size="sm" variant="outline">
                        Investigate
                      </Button>
                    </div>
                  </div>
                )) || []}

                {(!Array.isArray(data.anomalies) || data.anomalies.length === 0) && (
                  <div className="text-center py-8 text-gray-500">
                    No anomalies detected in the current analysis
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

export default React.memo(AdvancedAnalytics);

function getRiskColor(score: number): string {
  if (score >= 80) return 'text-red-600';
  if (score >= 60) return 'text-orange-600';
  if (score >= 40) return 'text-yellow-600';
  return 'text-green-600';
}

function getRiskVariant(level: string) {
  switch (level?.toLowerCase()) {
    case 'critical':
    case 'high':
      return 'destructive';
    case 'medium':
      return 'secondary';
    default:
      return 'outline';
  }
}

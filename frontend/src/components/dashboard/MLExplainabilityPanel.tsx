'use client';

import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { api } from '@/lib/api';
import { Brain, Search } from 'lucide-react';

interface MLFactors {
  address: string;
  risk_score: number;
  risk_level: string;
  factors: string[];
  confidence: number;
  model: string;
  feature_importance?: Record<string, number>;
}

export function MLExplainabilityPanel() {
  const [address, setAddress] = useState('');
  const [searchAddress, setSearchAddress] = useState('');

  const { data, isLoading } = useQuery<MLFactors>({
    queryKey: ['mlExplainability', searchAddress],
    queryFn: async () => {
      const response = await api.get(`/api/v1/ml/explain/${searchAddress}`);
      return response.data;
    },
    enabled: !!searchAddress && searchAddress.length > 10,
  });

  const handleSearch = () => {
    if (address.trim().length > 10) {
      setSearchAddress(address.trim());
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Brain className="w-5 h-5" />
          ML Explainability
        </CardTitle>
        <CardDescription>
          Verstehen Sie, warum das ML-Modell eine bestimmte Risk-Score vergeben hat
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Search */}
        <div className="flex gap-2">
          <Input
            placeholder="Adresse eingeben..."
            value={address}
            onChange={(e) => setAddress(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
            className="font-mono"
          />
          <Button onClick={handleSearch} disabled={!address.trim() || isLoading}>
            <Search className="w-4 h-4" />
          </Button>
        </div>

        {isLoading && (
          <div className="text-center py-8 text-sm text-muted-foreground">
            Analysiere Adresse...
          </div>
        )}

        {data && (
          <div className="space-y-6">
            {/* Risk Score */}
            <div className="p-4 border rounded-lg bg-muted">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium">Risk Score</span>
                <Badge
                  className={
                    data.risk_level === 'critical'
                      ? 'bg-red-100 text-red-800'
                      : data.risk_level === 'high'
                      ? 'bg-orange-100 text-orange-800'
                      : data.risk_level === 'medium'
                      ? 'bg-yellow-100 text-yellow-800'
                      : 'bg-green-100 text-green-800'
                  }
                >
                  {data.risk_level.toUpperCase()}
                </Badge>
              </div>
              <div className="text-3xl font-bold">
                {(data.risk_score * 100).toFixed(1)}%
              </div>
              <div className="text-xs text-muted-foreground mt-1">
                Confidence: {(data.confidence * 100).toFixed(1)}% | Model: {data.model}
              </div>
            </div>

            {/* Top Factors (SHAP-based) */}
            <div>
              <h4 className="text-sm font-semibold mb-3">Top Contributing Factors:</h4>
              <div className="space-y-3">
                {data.factors.map((factor, idx) => (
                  <div key={idx} className="flex items-start gap-3 p-3 border rounded-lg">
                    <span className="text-sm font-semibold text-muted-foreground">
                      #{idx + 1}
                    </span>
                    <div className="flex-1">
                      <p className="text-sm">{factor}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Feature Importance (if available) */}
            {data.feature_importance && Object.keys(data.feature_importance).length > 0 && (
              <div>
                <h4 className="text-sm font-semibold mb-3">Feature Importance:</h4>
                <div className="space-y-2">
                  {Object.entries(data.feature_importance)
                    .sort(([, a], [, b]) => b - a)
                    .slice(0, 10)
                    .map(([feature, importance]) => (
                      <div key={feature} className="space-y-1">
                        <div className="flex items-center justify-between text-xs">
                          <span className="font-mono">{feature}</span>
                          <span className="font-semibold">{(importance * 100).toFixed(1)}%</span>
                        </div>
                        <div className="w-full bg-muted rounded-full h-2">
                          <div
                            className="bg-primary h-2 rounded-full transition-all"
                            style={{ width: `${importance * 100}%` }}
                          />
                        </div>
                      </div>
                    ))}
                </div>
              </div>
            )}

            {/* Explanation */}
            <div className="p-4 border rounded-lg bg-blue-50 dark:bg-blue-950/20">
              <h4 className="text-sm font-semibold mb-2">Interpretation:</h4>
              <p className="text-sm text-muted-foreground">
                Das ML-Modell hat diese Adresse als <strong>{data.risk_level}</strong> eingestuft
                basierend auf {data.factors.length} Haupt-Faktoren. Die Confidence von{' '}
                {(data.confidence * 100).toFixed(1)}% zeigt, wie sicher das Modell ist.
                {data.model === 'xgboost' && (
                  <> Das XGBoost-Modell wurde mit über 10M+ gelabelten Adressen trainiert.</>
                )}
              </p>
            </div>
          </div>
        )}

        {!data && !isLoading && (
          <div className="text-center py-12 text-sm text-muted-foreground">
            <Brain className="w-12 h-12 mx-auto mb-3 opacity-50" />
            <p>Geben Sie eine Adresse ein, um die ML-Analyse zu starten</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

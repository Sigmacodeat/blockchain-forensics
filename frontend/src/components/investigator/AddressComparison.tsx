'use client';

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { api } from '@/lib/api';
import { TrendingUp, Users, AlertTriangle } from 'lucide-react';

interface AddressData {
  address: string;
  risk_score: number;
  risk_level: string;
  labels: string[];
  tx_count?: number;
  cluster_id?: string;
  cluster_size?: number;
}

interface AddressComparisonProps {
  addresses: string[];
}

export function AddressComparison({ addresses }: AddressComparisonProps) {
  const { data, isLoading } = useQuery<AddressData[]>({
    queryKey: ['addressComparison', addresses],
    queryFn: async () => {
      const results = await Promise.all(
        addresses.map((addr) => api.get(`/api/v1/enrich/${addr}`))
      );
      return results.map((r) => r.data);
    },
    enabled: addresses.length > 0,
  });

  // Find shared counterparties
  const findSharedConnections = () => {
    if (!data || data.length < 2) return [];
    // Simplified: would need actual graph query
    return ['0xABC...shared', '0xDEF...shared'];
  };

  const sharedConnections = findSharedConnections();

  if (addresses.length === 0) {
    return (
      <Card>
        <CardContent className="pt-6 text-center text-sm text-muted-foreground">
          Fügen Sie mindestens 2 Adressen hinzu, um einen Vergleich zu starten
        </CardContent>
      </Card>
    );
  }

  if (isLoading) {
    return (
      <div className="space-y-4">
        {addresses.map((addr) => (
          <Card key={addr}>
            <CardContent className="pt-6 space-y-3">
              <Skeleton className="h-6 w-48" />
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-3/4" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Comparison Matrix */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="w-5 h-5" />
            Risk Score Comparison
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {data?.map((addr) => (
              <div key={addr.address} className="flex items-center justify-between p-3 border rounded-lg">
                <div className="flex-1">
                  <code className="text-xs font-mono">{addr.address}</code>
                </div>
                <div className="flex items-center gap-4">
                  <div className="text-right">
                    <p className="text-xs text-muted-foreground">Risk Score</p>
                    <p className="text-lg font-bold">{(addr.risk_score * 100).toFixed(1)}%</p>
                  </div>
                  <Badge
                    className={
                      addr.risk_level === 'critical'
                        ? 'bg-red-100 text-red-800'
                        : addr.risk_level === 'high'
                        ? 'bg-orange-100 text-orange-800'
                        : addr.risk_level === 'medium'
                        ? 'bg-yellow-100 text-yellow-800'
                        : 'bg-green-100 text-green-800'
                    }
                  >
                    {addr.risk_level}
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Shared Connections */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="w-5 h-5" />
            Shared Connections
          </CardTitle>
        </CardHeader>
        <CardContent>
          {sharedConnections.length > 0 ? (
            <div className="space-y-2">
              {sharedConnections.map((conn) => (
                <div key={conn} className="p-3 border rounded-lg">
                  <code className="text-xs font-mono">{conn}</code>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-sm text-muted-foreground">
              Keine gemeinsamen Verbindungen gefunden
            </div>
          )}
        </CardContent>
      </Card>

      {/* Cluster Analysis */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertTriangle className="w-5 h-5" />
            Cluster Analysis
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {data?.filter((addr) => addr.cluster_id).map((addr) => (
              <div key={addr.address} className="p-3 border rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <code className="text-xs font-mono">{addr.address}</code>
                  <Badge variant="secondary">
                    Cluster: {addr.cluster_id?.substring(0, 8)}...
                  </Badge>
                </div>
                <p className="text-xs text-muted-foreground">
                  Cluster Size: {addr.cluster_size || 'N/A'} Adressen
                </p>
              </div>
            ))}
            {!data?.some((addr) => addr.cluster_id) && (
              <div className="text-center py-8 text-sm text-muted-foreground">
                Keine Cluster-Informationen verfügbar
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Labels Comparison */}
      <Card>
        <CardHeader>
          <CardTitle>Label Distribution</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {data?.map((addr) => (
              <div key={addr.address} className="space-y-2">
                <code className="text-xs font-mono block">{addr.address}</code>
                <div className="flex flex-wrap gap-2">
                  {addr.labels && addr.labels.length > 0 ? (
                    addr.labels.map((label, idx) => (
                      <Badge key={idx} variant="outline">
                        {label}
                      </Badge>
                    ))
                  ) : (
                    <span className="text-xs text-muted-foreground">No labels</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

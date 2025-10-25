/**
 * Contract Analysis Hook
 * ======================
 * React hook for fetching and caching contract analysis
 */

import { useState, useEffect, useCallback } from 'react';

interface ContractAnalysisOptions {
  address: string;
  chain?: string;
  autoFetch?: boolean;
  resolveProxy?: boolean;
}

interface AnalysisResult {
  address: string;
  chain: string;
  score: number;
  risk_level: string;
  summary: string;
  vulnerabilities: {
    total: number;
    critical: number;
    high: number;
    medium: number;
    low: number;
  };
  interface: {
    standards: string[];
    functions_count: number;
    events: string[];
  };
  proxy?: {
    is_proxy: boolean;
    implementation?: string;
    type?: string;
  };
  findings: any[];
  statistics: any;
}

export const useContractAnalysis = ({
  address,
  chain = 'ethereum',
  autoFetch = true,
  resolveProxy = true,
}: ContractAnalysisOptions) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null);

  const fetchAnalysis = useCallback(async () => {
    if (!address) return;

    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/v1/contracts/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          address,
          chain,
          resolve_proxy: resolveProxy,
        }),
      });

      if (!response.ok) {
        throw new Error(`Analysis failed: ${response.statusText}`);
      }

      const data = await response.json();
      setAnalysis(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      setAnalysis(null);
    } finally {
      setLoading(false);
    }
  }, [address, chain, resolveProxy]);

  useEffect(() => {
    if (autoFetch && address) {
      fetchAnalysis();
    }
  }, [autoFetch, address, fetchAnalysis]);

  const refetch = () => {
    return fetchAnalysis();
  };

  return {
    loading,
    error,
    analysis,
    refetch,
  };
};

export default useContractAnalysis;

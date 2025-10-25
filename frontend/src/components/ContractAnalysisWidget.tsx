/**
 * Contract Analysis Widget
 * =========================
 * Displays smart contract analysis results in compact or full mode
 */

import React, { useState, useEffect } from 'react';
import { AlertTriangle, CheckCircle, XCircle, TrendingUp, TrendingDown, Shield, FileText, Download } from 'lucide-react';

interface ContractAnalysisWidgetProps {
  address: string;
  chain?: string;
  variant?: 'compact' | 'full';
  onAnalysisComplete?: (analysis: any) => void;
}

interface Analysis {
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
}

export const ContractAnalysisWidget: React.FC<ContractAnalysisWidgetProps> = ({
  address,
  chain = 'ethereum',
  variant = 'compact',
  onAnalysisComplete,
}) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    analyzeContract();
  }, [address, chain]);

  const analyzeContract = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`/api/v1/contracts/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ address, chain }),
      });

      if (!response.ok) {
        throw new Error(`Analysis failed: ${response.statusText}`);
      }

      const data = await response.json();
      setAnalysis(data);
      onAnalysisComplete?.(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Analysis failed');
    } finally {
      setLoading(false);
    }
  };

  const getRiskColor = (score: number) => {
    if (score < 0.3) return 'text-green-600 bg-green-100';
    if (score < 0.5) return 'text-yellow-600 bg-yellow-100';
    if (score < 0.7) return 'text-orange-600 bg-orange-100';
    return 'text-red-600 bg-red-100';
  };

  const getRiskIcon = (score: number) => {
    if (score < 0.3) return <CheckCircle className="w-5 h-5" />;
    if (score < 0.7) return <AlertTriangle className="w-5 h-5" />;
    return <XCircle className="w-5 h-5" />;
  };

  const downloadReport = async (format: 'json' | 'markdown' | 'pdf') => {
    try {
      const response = await fetch(`/api/v1/contracts/export/${chain}/${address}/${format}`);
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `contract-analysis-${address.slice(0, 10)}.${format}`;
      a.click();
    } catch (err) {
      console.error('Download failed:', err);
    }
  };

  if (loading) {
    return (
      <div className={`rounded-lg border border-gray-200 p-4 ${variant === 'full' ? 'min-h-[400px]' : 'h-24'} animate-pulse bg-gray-50`}>
        <div className="flex items-center justify-between">
          <div className="h-4 bg-gray-200 rounded w-1/3"></div>
          <div className="h-8 w-16 bg-gray-200 rounded"></div>
        </div>
        <div className="mt-4 space-y-3">
          <div className="h-3 bg-gray-200 rounded"></div>
          <div className="h-3 bg-gray-200 rounded w-5/6"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-4">
        <div className="flex items-center gap-2 text-red-800">
          <XCircle className="w-5 h-5" />
          <span className="font-medium">Analysis Error</span>
        </div>
        <p className="mt-2 text-sm text-red-700">{error}</p>
        <button
          onClick={analyzeContract}
          className="mt-3 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 text-sm"
        >
          Retry Analysis
        </button>
      </div>
    );
  }

  if (!analysis) return null;

  // Compact Variant
  if (variant === 'compact') {
    return (
      <div className="rounded-lg border border-gray-200 bg-white p-3 hover:shadow-md transition-shadow">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className={`p-2 rounded-lg ${getRiskColor(analysis.score)}`}>
              {getRiskIcon(analysis.score)}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-sm font-semibold text-gray-900">Contract Risk</span>
                {analysis.proxy?.is_proxy && (
                  <span className="px-2 py-0.5 text-xs bg-purple-100 text-purple-700 rounded">
                    Proxy
                  </span>
                )}
              </div>
              <div className="flex items-center gap-2 text-xs text-gray-600">
                <span>{analysis.risk_level.toUpperCase()}</span>
                <span>•</span>
                <span>{analysis.vulnerabilities.total} issues</span>
                {analysis.interface.standards.length > 0 && (
                  <>
                    <span>•</span>
                    <span>{analysis.interface.standards.join(', ')}</span>
                  </>
                )}
              </div>
            </div>
          </div>
          <div className="text-2xl font-bold text-gray-900">
            {(analysis.score * 100).toFixed(0)}
          </div>
        </div>
      </div>
    );
  }

  // Full Variant
  return (
    <div className="rounded-lg border border-gray-200 bg-white overflow-hidden">
      {/* Header */}
      <div className={`p-4 ${getRiskColor(analysis.score)} border-b`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {getRiskIcon(analysis.score)}
            <div>
              <h3 className="font-semibold">Contract Analysis</h3>
              <p className="text-sm opacity-80">
                Risk Score: {(analysis.score * 100).toFixed(0)}/100 - {analysis.risk_level.toUpperCase()}
              </p>
            </div>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => downloadReport('json')}
              className="p-2 hover:bg-white/20 rounded transition-colors"
              title="Download JSON"
            >
              <Download className="w-4 h-4" />
            </button>
            <button
              onClick={() => downloadReport('markdown')}
              className="p-2 hover:bg-white/20 rounded transition-colors"
              title="Download Markdown"
            >
              <FileText className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="p-4 space-y-4">
        {/* Summary */}
        <div>
          <h4 className="text-sm font-semibold text-gray-700 mb-2">Summary</h4>
          <p className="text-sm text-gray-600 whitespace-pre-wrap">{analysis.summary}</p>
        </div>

        {/* Vulnerabilities */}
        {analysis.vulnerabilities.total > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-gray-700 mb-2">Vulnerabilities</h4>
            <div className="grid grid-cols-4 gap-2">
              {analysis.vulnerabilities.critical > 0 && (
                <div className="p-2 rounded bg-red-50 border border-red-200">
                  <div className="text-xs text-red-600">Critical</div>
                  <div className="text-lg font-bold text-red-700">{analysis.vulnerabilities.critical}</div>
                </div>
              )}
              {analysis.vulnerabilities.high > 0 && (
                <div className="p-2 rounded bg-orange-50 border border-orange-200">
                  <div className="text-xs text-orange-600">High</div>
                  <div className="text-lg font-bold text-orange-700">{analysis.vulnerabilities.high}</div>
                </div>
              )}
              {analysis.vulnerabilities.medium > 0 && (
                <div className="p-2 rounded bg-yellow-50 border border-yellow-200">
                  <div className="text-xs text-yellow-600">Medium</div>
                  <div className="text-lg font-bold text-yellow-700">{analysis.vulnerabilities.medium}</div>
                </div>
              )}
              {analysis.vulnerabilities.low > 0 && (
                <div className="p-2 rounded bg-blue-50 border border-blue-200">
                  <div className="text-xs text-blue-600">Low</div>
                  <div className="text-lg font-bold text-blue-700">{analysis.vulnerabilities.low}</div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Interface Info */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <h4 className="text-sm font-semibold text-gray-700 mb-2">Standards</h4>
            <div className="flex flex-wrap gap-1">
              {analysis.interface.standards.map((std) => (
                <span key={std} className="px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded">
                  {std}
                </span>
              ))}
              {analysis.interface.standards.length === 0 && (
                <span className="text-sm text-gray-500">None detected</span>
              )}
            </div>
          </div>
          <div>
            <h4 className="text-sm font-semibold text-gray-700 mb-2">Functions</h4>
            <div className="text-2xl font-bold text-gray-900">{analysis.interface.functions_count}</div>
          </div>
        </div>

        {/* Proxy Info */}
        {analysis.proxy?.is_proxy && (
          <div className="p-3 rounded bg-purple-50 border border-purple-200">
            <div className="flex items-center gap-2 mb-2">
              <Shield className="w-4 h-4 text-purple-600" />
              <span className="text-sm font-semibold text-purple-900">Proxy Contract</span>
            </div>
            <div className="text-xs text-purple-700 space-y-1">
              <div>Type: {analysis.proxy.type || 'Unknown'}</div>
              {analysis.proxy.implementation && (
                <div className="font-mono">Impl: {analysis.proxy.implementation.slice(0, 20)}...</div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

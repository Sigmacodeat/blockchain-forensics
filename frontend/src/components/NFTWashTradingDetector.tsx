/**
 * NFT Wash-Trading Detector UI
 * =============================
 * 
 * State-of-the-art interface for detecting NFT wash trading patterns.
 * Features:
 * - Upload trades via CSV/JSON
 * - Real-time detection with 5 heuristics
 * - Visual pattern breakdown
 * - Confidence scoring with color-coded badges
 * - Export findings for evidence
 */

import React, { useState, useCallback } from 'react';
import { Upload, AlertTriangle, CheckCircle, TrendingDown, RefreshCw, Download, Info } from 'lucide-react';
import axios from 'axios';

interface NFTTrade {
  tx_hash: string;
  timestamp: string;
  token_address: string;
  token_id: string;
  from_address: string;
  to_address: string;
  price: number;
  marketplace?: string;
}

interface WashTradingFinding {
  pattern_type: 'self_trading' | 'round_trip' | 'repeated_wallets' | 'price_anomaly' | 'coordinated_bidding';
  confidence: number;
  description: string;
  involved_addresses: string[];
  involved_trades: string[];
  metadata?: {
    time_gap_hours?: number;
    price_difference?: number;
    repetition_count?: number;
  };
}

interface DetectionResult {
  success: boolean;
  findings: WashTradingFinding[];
  summary: {
    total_trades: number;
    suspicious_trades: number;
    unique_patterns: number;
    confidence_avg: number;
  };
}

const PATTERN_INFO: Record<string, { icon: string; description: string; color: string }> = {
  self_trading: {
    icon: '🔄',
    description: 'Same wallet buying and selling',
    color: 'text-red-600 dark:text-red-400'
  },
  round_trip: {
    icon: '🔁',
    description: 'Asset returns to original owner',
    color: 'text-orange-600 dark:text-orange-400'
  },
  repeated_wallets: {
    icon: '♻️',
    description: 'High trading frequency between wallets',
    color: 'text-yellow-600 dark:text-yellow-400'
  },
  price_anomaly: {
    icon: '📈',
    description: 'Unusual price spikes/drops',
    color: 'text-purple-600 dark:text-purple-400'
  },
  coordinated_bidding: {
    icon: '🤝',
    description: 'Synchronized bidding patterns',
    color: 'text-blue-600 dark:text-blue-400'
  }
};

export const NFTWashTradingDetector: React.FC = () => {
  const [trades, setTrades] = useState<NFTTrade[]>([]);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<DetectionResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFileUpload = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const content = e.target?.result as string;
        let parsedTrades: NFTTrade[];

        if (file.name.endsWith('.json')) {
          parsedTrades = JSON.parse(content);
        } else if (file.name.endsWith('.csv')) {
          // Simple CSV parsing (header row expected)
          const lines = content.split('\n').filter(l => l.trim());
          const headers = lines[0].split(',').map(h => h.trim());
          parsedTrades = lines.slice(1).map(line => {
            const values = line.split(',').map(v => v.trim());
            const trade: any = {};
            headers.forEach((h, i) => {
              if (h === 'price') trade[h] = parseFloat(values[i]);
              else trade[h] = values[i];
            });
            return trade as NFTTrade;
          });
        } else {
          throw new Error('Unsupported file format. Use JSON or CSV.');
        }

        setTrades(parsedTrades);
        setError(null);
      } catch (err) {
        setError(`Failed to parse file: ${err}`);
      }
    };
    reader.readAsText(file);
  }, []);

  const handleDetect = useCallback(async () => {
    if (trades.length === 0) {
      setError('Please upload trades first');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await axios.post<DetectionResult>(
        '/api/v1/forensics/nft/wash-detect',
        { trades },
        { headers: { 'Content-Type': 'application/json' } }
      );

      setResult(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Detection failed');
    } finally {
      setLoading(false);
    }
  }, [trades]);

  const handleExport = useCallback(() => {
    if (!result) return;

    const exportData = {
      timestamp: new Date().toISOString(),
      summary: result.summary,
      findings: result.findings
    };

    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `nft-wash-trading-report-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }, [result]);

  const getConfidenceBadge = (confidence: number) => {
    if (confidence >= 0.9) return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
    if (confidence >= 0.75) return 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200';
    if (confidence >= 0.6) return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200';
    return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white dark:bg-slate-800 rounded-lg shadow-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-2xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <TrendingDown className="w-7 h-7 text-purple-600" />
              NFT Wash-Trading Detector
            </h2>
            <p className="text-slate-600 dark:text-slate-400 mt-1">
              Detect suspicious trading patterns with 5 advanced heuristics
            </p>
          </div>
        </div>

        {/* Upload Section */}
        <div className="border-2 border-dashed border-slate-300 dark:border-slate-600 rounded-lg p-8 text-center">
          <Upload className="w-12 h-12 text-slate-400 mx-auto mb-4" />
          <label className="cursor-pointer">
            <span className="text-primary-600 hover:text-primary-700 font-medium">
              Upload trades (JSON or CSV)
            </span>
            <input
              type="file"
              accept=".json,.csv"
              onChange={handleFileUpload}
              className="hidden"
            />
          </label>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-2">
            Max 1000 trades per analysis
          </p>
        </div>

        {/* Trades Loaded */}
        {trades.length > 0 && (
          <div className="mt-4 p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <CheckCircle className="w-5 h-5 text-green-600" />
                <span className="text-green-800 dark:text-green-200 font-medium">
                  {trades.length} trades loaded
                </span>
              </div>
              <button
                onClick={handleDetect}
                disabled={loading}
                className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                {loading ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    Analyzing...
                  </>
                ) : (
                  <>
                    <AlertTriangle className="w-4 h-4" />
                    Detect Wash Trading
                  </>
                )}
              </button>
            </div>
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="mt-4 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
            <p className="text-red-800 dark:text-red-200">{error}</p>
          </div>
        )}
      </div>

      {/* Results */}
      {result && (
        <>
          {/* Summary */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-white dark:bg-slate-800 rounded-lg shadow p-6">
              <div className="text-sm text-slate-600 dark:text-slate-400">Total Trades</div>
              <div className="text-3xl font-bold text-slate-900 dark:text-white mt-2">
                {result.summary.total_trades}
              </div>
            </div>
            <div className="bg-white dark:bg-slate-800 rounded-lg shadow p-6">
              <div className="text-sm text-slate-600 dark:text-slate-400">Suspicious</div>
              <div className="text-3xl font-bold text-red-600 dark:text-red-400 mt-2">
                {result.summary.suspicious_trades}
              </div>
            </div>
            <div className="bg-white dark:bg-slate-800 rounded-lg shadow p-6">
              <div className="text-sm text-slate-600 dark:text-slate-400">Patterns Found</div>
              <div className="text-3xl font-bold text-orange-600 dark:text-orange-400 mt-2">
                {result.summary.unique_patterns}
              </div>
            </div>
            <div className="bg-white dark:bg-slate-800 rounded-lg shadow p-6">
              <div className="text-sm text-slate-600 dark:text-slate-400">Avg Confidence</div>
              <div className="text-3xl font-bold text-purple-600 dark:text-purple-400 mt-2">
                {(result.summary.confidence_avg * 100).toFixed(0)}%
              </div>
            </div>
          </div>

          {/* Findings */}
          <div className="bg-white dark:bg-slate-800 rounded-lg shadow-lg p-6">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-xl font-bold text-slate-900 dark:text-white">
                Detected Patterns ({result.findings.length})
              </h3>
              <button
                onClick={handleExport}
                className="flex items-center gap-2 px-4 py-2 bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-600"
              >
                <Download className="w-4 h-4" />
                Export Report
              </button>
            </div>

            <div className="space-y-4">
              {result.findings.map((finding, idx) => {
                const patternInfo = PATTERN_INFO[finding.pattern_type];
                return (
                  <div
                    key={idx}
                    className="border border-slate-200 dark:border-slate-700 rounded-lg p-4 hover:border-primary-500 transition-colors"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <span className="text-2xl">{patternInfo.icon}</span>
                          <div>
                            <h4 className={`font-semibold ${patternInfo.color}`}>
                              {finding.pattern_type.replace('_', ' ').toUpperCase()}
                            </h4>
                            <p className="text-sm text-slate-600 dark:text-slate-400">
                              {patternInfo.description}
                            </p>
                          </div>
                        </div>
                        <p className="text-slate-700 dark:text-slate-300 mb-3">
                          {finding.description}
                        </p>
                        <div className="flex flex-wrap gap-2 text-sm">
                          <span className="text-slate-600 dark:text-slate-400">
                            Addresses: {finding.involved_addresses.length}
                          </span>
                          <span className="text-slate-400">•</span>
                          <span className="text-slate-600 dark:text-slate-400">
                            Trades: {finding.involved_trades.length}
                          </span>
                          {finding.metadata?.time_gap_hours && (
                            <>
                              <span className="text-slate-400">•</span>
                              <span className="text-slate-600 dark:text-slate-400">
                                Time Gap: {finding.metadata.time_gap_hours.toFixed(1)}h
                              </span>
                            </>
                          )}
                        </div>
                      </div>
                      <div className="ml-4">
                        <span className={`px-3 py-1 rounded-full text-xs font-semibold ${getConfidenceBadge(finding.confidence)}`}>
                          {(finding.confidence * 100).toFixed(0)}% Confidence
                        </span>
                      </div>
                    </div>
                  </div>
                );
              })}

              {result.findings.length === 0 && (
                <div className="text-center py-8">
                  <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-3" />
                  <p className="text-slate-600 dark:text-slate-400">
                    No suspicious patterns detected. Trades appear legitimate.
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Pattern Info */}
          <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
            <div className="flex items-start gap-2">
              <Info className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
              <div className="text-sm text-blue-800 dark:text-blue-200">
                <strong>Detection Methods:</strong> Self-Trading (same wallet), Round-Trip (returns to owner), 
                Repeated Wallets (high frequency), Price Anomaly (spikes), Coordinated Bidding (synchronized).
                Confidence based on temporal analysis, price patterns, and transaction graph structure.
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

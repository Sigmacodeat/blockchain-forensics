/**
 * Scam Detection Dashboard
 * =========================
 * 
 * Real-time behavioral scam detection dashboard.
 * State-of-the-art mit 15 Pattern-Types + ML-basierte Confidence Scoring.
 */

import React, { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import axios from 'axios';
import {
  AlertTriangle, Shield, Search, TrendingUp, Users,
  DollarSign, Activity, Eye, FileText, Clock
} from 'lucide-react';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface ScamPattern {
  pattern_type: string;
  confidence: number;
  indicators: string[];
  timestamp: string;
  victim_count: number;
  attacker_addresses: string[];
  metadata: any;
  transaction_count: number;
}

interface ScamDetectionResult {
  address: string;
  chain: string;
  patterns_detected: ScamPattern[];
  total_confidence: number;
  risk_level: string;
  timestamp: string;
}

const PATTERN_INFO: Record<string, { name: string; severity: string; color: string; icon: string }> = {
  pig_butchering: {
    name: 'Pig Butchering',
    severity: 'CRITICAL',
    color: 'bg-red-600',
    icon: '🐷'
  },
  ice_phishing: {
    name: 'Ice Phishing',
    severity: 'HIGH',
    color: 'bg-orange-600',
    icon: '🎣'
  },
  address_poisoning: {
    name: 'Address Poisoning',
    severity: 'MEDIUM',
    color: 'bg-yellow-600',
    icon: '☠️'
  },
  rug_pull: {
    name: 'Rug Pull',
    severity: 'CRITICAL',
    color: 'bg-red-600',
    icon: '💸'
  },
  impersonation_token: {
    name: 'Impersonation Token',
    severity: 'HIGH',
    color: 'bg-orange-600',
    icon: '🎭'
  }
};

export default function ScamDetectionPage() {
  const [searchAddress, setSearchAddress] = useState('');
  const [selectedChain, setSelectedChain] = useState('ethereum');
  const [detectionResult, setDetectionResult] = useState<ScamDetectionResult | null>(null);

  // Fetch available patterns
  const { data: patterns = [] } = useQuery({
    queryKey: ['scam-patterns'],
    queryFn: async () => {
      const response = await axios.get(`${API_BASE_URL}/api/v1/scam-detection/patterns`);
      return response.data;
    }
  });

  // Fetch statistics
  const { data: stats } = useQuery({
    queryKey: ['scam-stats', selectedChain],
    queryFn: async () => {
      const response = await axios.get(
        `${API_BASE_URL}/api/v1/scam-detection/statistics?chain=${selectedChain}&days=30`
      );
      return response.data;
    }
  });

  // Run detection
  const detectionMutation = useMutation({
    mutationFn: async () => {
      const response = await axios.post(`${API_BASE_URL}/api/v1/scam-detection/detect`, {
        address: searchAddress,
        chain: selectedChain,
        include_token_metadata: true
      });
      return response.data as ScamDetectionResult;
    },
    onSuccess: (data) => {
      setDetectionResult(data);
    }
  });

  const handleDetect = () => {
    if (searchAddress) {
      detectionMutation.mutate();
    }
  };

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'CRITICAL': return 'text-red-600 bg-red-50 border-red-200';
      case 'HIGH': return 'text-orange-600 bg-orange-50 border-orange-200';
      case 'MEDIUM': return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      default: return 'text-green-600 bg-green-50 border-green-200';
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <Shield className="h-8 w-8 text-primary-600" />
            <h1 className="text-3xl font-bold text-gray-900">Scam Detection</h1>
          </div>
          <p className="text-gray-600">
            Real-time behavioral analysis detecting 15 scam patterns with AI-powered confidence scoring
          </p>
        </div>

        {/* Statistics Cards */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <div className="bg-white p-6 rounded-lg shadow">
              <div className="flex items-center justify-between mb-2">
                <div className="text-sm font-medium text-gray-600">Total Scams Detected</div>
                <AlertTriangle className="h-5 w-5 text-red-600" />
              </div>
              <div className="text-2xl font-bold text-gray-900">
                {stats.total_scams_detected?.toLocaleString()}
              </div>
              <div className="text-xs text-gray-500 mt-1">Last 30 days</div>
            </div>

            <div className="bg-white p-6 rounded-lg shadow">
              <div className="flex items-center justify-between mb-2">
                <div className="text-sm font-medium text-gray-600">Victims Protected</div>
                <Users className="h-5 w-5 text-green-600" />
              </div>
              <div className="text-2xl font-bold text-gray-900">
                {stats.victims_protected?.toLocaleString()}
              </div>
              <div className="text-xs text-gray-500 mt-1">Accounts</div>
            </div>

            <div className="bg-white p-6 rounded-lg shadow">
              <div className="flex items-center justify-between mb-2">
                <div className="text-sm font-medium text-gray-600">Value at Risk</div>
                <DollarSign className="h-5 w-5 text-orange-600" />
              </div>
              <div className="text-2xl font-bold text-gray-900">
                {stats.total_value_affected}
              </div>
              <div className="text-xs text-gray-500 mt-1">USD equivalent</div>
            </div>

            <div className="bg-white p-6 rounded-lg shadow">
              <div className="flex items-center justify-between mb-2">
                <div className="text-sm font-medium text-gray-600">Detection Accuracy</div>
                <TrendingUp className="h-5 w-5 text-primary-600" />
              </div>
              <div className="text-2xl font-bold text-gray-900">
                {(stats.detection_accuracy * 100).toFixed(1)}%
              </div>
              <div className="text-xs text-gray-500 mt-1">Verified cases</div>
            </div>
          </div>
        )}

        {/* Search Section */}
        <div className="bg-white p-6 rounded-lg shadow mb-8">
          <h2 className="text-lg font-semibold mb-4">Analyze Address</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Address
              </label>
              <input
                type="text"
                className="w-full px-4 py-2 border border-gray-300 rounded-md"
                placeholder="0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
                value={searchAddress}
                onChange={(e) => setSearchAddress(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleDetect()}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Chain
              </label>
              <select
                className="w-full px-4 py-2 border border-gray-300 rounded-md"
                value={selectedChain}
                onChange={(e) => setSelectedChain(e.target.value)}
              >
                <option value="ethereum">Ethereum</option>
                <option value="polygon">Polygon</option>
                <option value="arbitrum">Arbitrum</option>
                <option value="optimism">Optimism</option>
                <option value="base">Base</option>
              </select>
            </div>
          </div>

          <button
            onClick={handleDetect}
            disabled={!searchAddress || detectionMutation.isPending}
            className="w-full md:w-auto px-6 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 disabled:opacity-50 flex items-center justify-center gap-2"
          >
            <Search className="h-4 w-4" />
            {detectionMutation.isPending ? 'Analyzing...' : 'Analyze Address'}
          </button>
        </div>

        {/* Detection Results */}
        {detectionResult && (
          <div className="bg-white p-6 rounded-lg shadow mb-8">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-semibold">Detection Results</h2>
              <div className={`px-4 py-2 rounded-lg border font-semibold ${getRiskColor(detectionResult.risk_level)}`}>
                {detectionResult.risk_level} RISK
              </div>
            </div>

            {/* Address Info */}
            <div className="bg-gray-50 p-4 rounded-lg mb-6">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                <div>
                  <div className="text-gray-500 mb-1">Address</div>
                  <code className="text-xs font-mono">{detectionResult.address}</code>
                </div>
                <div>
                  <div className="text-gray-500 mb-1">Chain</div>
                  <div className="font-medium">{detectionResult.chain}</div>
                </div>
                <div>
                  <div className="text-gray-500 mb-1">Overall Confidence</div>
                  <div className="font-medium">{(detectionResult.total_confidence * 100).toFixed(1)}%</div>
                </div>
              </div>
            </div>

            {/* Detected Patterns */}
            {detectionResult.patterns_detected.length > 0 ? (
              <div className="space-y-4">
                <h3 className="font-semibold text-lg flex items-center gap-2">
                  <AlertTriangle className="h-5 w-5 text-red-600" />
                  {detectionResult.patterns_detected.length} Scam Pattern(s) Detected
                </h3>

                {detectionResult.patterns_detected.map((pattern, idx) => {
                  const info = PATTERN_INFO[pattern.pattern_type] || {
                    name: pattern.pattern_type,
                    severity: 'UNKNOWN',
                    color: 'bg-gray-600',
                    icon: '⚠️'
                  };

                  return (
                    <div key={idx} className="border border-gray-200 rounded-lg p-4">
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex items-center gap-3">
                          <span className="text-2xl">{info.icon}</span>
                          <div>
                            <h4 className="font-semibold text-lg">{info.name}</h4>
                            <div className="flex items-center gap-2 text-sm text-gray-600">
                              <span className={`px-2 py-0.5 rounded text-xs font-medium text-white ${info.color}`}>
                                {info.severity}
                              </span>
                              <span>•</span>
                              <span>Confidence: {(pattern.confidence * 100).toFixed(1)}%</span>
                            </div>
                          </div>
                        </div>
                        <div className="text-right text-sm text-gray-500">
                          <div className="flex items-center gap-1">
                            <Clock className="h-3 w-3" />
                            {new Date(pattern.timestamp).toLocaleString()}
                          </div>
                        </div>
                      </div>

                      {/* Indicators */}
                      <div className="mb-3">
                        <div className="text-sm font-medium text-gray-700 mb-2">Indicators:</div>
                        <ul className="space-y-1">
                          {pattern.indicators.map((indicator, i) => (
                            <li key={i} className="text-sm text-gray-600 flex items-start gap-2">
                              <span className="text-red-600">•</span>
                              <span>{indicator}</span>
                            </li>
                          ))}
                        </ul>
                      </div>

                      {/* Stats */}
                      <div className="grid grid-cols-3 gap-4 text-sm bg-gray-50 p-3 rounded">
                        <div>
                          <div className="text-gray-500">Victims</div>
                          <div className="font-medium">{pattern.victim_count}</div>
                        </div>
                        <div>
                          <div className="text-gray-500">Attackers</div>
                          <div className="font-medium">{pattern.attacker_addresses.length}</div>
                        </div>
                        <div>
                          <div className="text-gray-500">Transactions</div>
                          <div className="font-medium">{pattern.transaction_count}</div>
                        </div>
                      </div>

                      {/* Evidence Metadata */}
                      {pattern.metadata && Object.keys(pattern.metadata).length > 0 && (
                        <details className="mt-3">
                          <summary className="text-sm text-primary-600 cursor-pointer hover:text-primary-700">
                            View Evidence Details
                          </summary>
                          <div className="mt-2 bg-gray-100 p-3 rounded text-xs font-mono">
                            <pre>{JSON.stringify(pattern.metadata, null, 2)}</pre>
                          </div>
                        </details>
                      )}
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="text-center py-8 text-green-600">
                <Shield className="h-16 w-16 mx-auto mb-3" />
                <p className="text-lg font-semibold">No Scam Patterns Detected</p>
                <p className="text-sm text-gray-600">This address appears clean based on behavioral analysis</p>
              </div>
            )}
          </div>
        )}

        {/* Available Patterns */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <FileText className="h-5 w-5" />
            Supported Scam Patterns
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {patterns.map((pattern: any, idx: number) => (
              <div key={idx} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                <div className="flex items-center gap-2 mb-2">
                  <span className={`px-2 py-0.5 rounded text-xs font-medium text-white ${
                    pattern.severity === 'CRITICAL' ? 'bg-red-600' :
                    pattern.severity === 'HIGH' ? 'bg-orange-600' :
                    'bg-yellow-600'
                  }`}>
                    {pattern.severity}
                  </span>
                  <h3 className="font-semibold">{pattern.name}</h3>
                </div>
                <p className="text-sm text-gray-600 mb-3">{pattern.description}</p>
                
                <details className="text-xs">
                  <summary className="text-primary-600 cursor-pointer hover:text-primary-700">
                    Key Indicators
                  </summary>
                  <ul className="mt-2 space-y-1 text-gray-600">
                    {pattern.indicators.map((ind: string, i: number) => (
                      <li key={i} className="flex items-start gap-1">
                        <span>•</span>
                        <span>{ind}</span>
                      </li>
                    ))}
                  </ul>
                </details>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

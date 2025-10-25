/**
 * Contract Risk Dashboard Widget
 * ===============================
 * Shows recent contract analyses and risk overview
 */

import React, { useState, useEffect } from 'react';
import { Shield, AlertTriangle, TrendingUp, FileText } from 'lucide-react';

interface ContractSummary {
  address: string;
  chain: string;
  score: number;
  risk_level: string;
  analyzed_at: string;
}

export const ContractRiskWidget: React.FC = () => {
  const [recentAnalyses, setRecentAnalyses] = useState<ContractSummary[]>([]);
  const [stats, setStats] = useState({
    total: 0,
    high_risk: 0,
    medium_risk: 0,
    low_risk: 0,
  });

  useEffect(() => {
    // In production, fetch from API
    // For now, mock data
    setStats({
      total: 42,
      high_risk: 5,
      medium_risk: 12,
      low_risk: 25,
    });

    setRecentAnalyses([
      {
        address: '0x1234...5678',
        chain: 'ethereum',
        score: 0.75,
        risk_level: 'high',
        analyzed_at: '2 hours ago',
      },
      {
        address: '0xabcd...ef12',
        chain: 'polygon',
        score: 0.35,
        risk_level: 'medium',
        analyzed_at: '5 hours ago',
      },
      {
        address: '0x9876...5432',
        chain: 'ethereum',
        score: 0.15,
        risk_level: 'low',
        analyzed_at: '1 day ago',
      },
    ]);
  }, []);

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'critical':
      case 'high':
        return 'text-red-600 bg-red-100';
      case 'medium':
        return 'text-yellow-600 bg-yellow-100';
      case 'low':
        return 'text-green-600 bg-green-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
      {/* Header */}
      <div className="p-4 border-b border-gray-200 bg-gradient-to-r from-purple-50 to-blue-50">
        <div className="flex items-center gap-2">
          <Shield className="w-5 h-5 text-purple-600" />
          <h3 className="font-semibold text-gray-900">Contract Risk Overview</h3>
        </div>
        <p className="text-sm text-gray-600 mt-1">Smart contract security analysis</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-3 gap-4 p-4 border-b border-gray-100">
        <div className="text-center">
          <div className="text-2xl font-bold text-gray-900">{stats.total}</div>
          <div className="text-xs text-gray-600">Total Analyzed</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-red-600">{stats.high_risk}</div>
          <div className="text-xs text-gray-600">High Risk</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-green-600">{stats.low_risk}</div>
          <div className="text-xs text-gray-600">Low Risk</div>
        </div>
      </div>

      {/* Recent Analyses */}
      <div className="p-4">
        <h4 className="text-sm font-semibold text-gray-700 mb-3">Recent Analyses</h4>
        <div className="space-y-2">
          {recentAnalyses.map((analysis, idx) => (
            <div
              key={idx}
              className="flex items-center justify-between p-2 rounded hover:bg-gray-50 transition-colors cursor-pointer"
            >
              <div className="flex items-center gap-3 flex-1">
                <div className={`p-1.5 rounded ${getRiskColor(analysis.risk_level)}`}>
                  {analysis.risk_level === 'high' ? (
                    <AlertTriangle className="w-3.5 h-3.5" />
                  ) : (
                    <Shield className="w-3.5 h-3.5" />
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-mono font-medium text-gray-900 truncate">
                      {analysis.address}
                    </span>
                    <span className="px-1.5 py-0.5 text-xs bg-gray-100 text-gray-600 rounded">
                      {analysis.chain}
                    </span>
                  </div>
                  <div className="text-xs text-gray-500">{analysis.analyzed_at}</div>
                </div>
              </div>
              <div className="text-right">
                <div className={`text-sm font-bold ${getRiskColor(analysis.risk_level).split(' ')[0]}`}>
                  {(analysis.score * 100).toFixed(0)}
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* View All Button */}
        <button className="w-full mt-4 px-4 py-2 text-sm font-medium text-purple-600 bg-purple-50 hover:bg-purple-100 rounded transition-colors">
          View All Analyses
        </button>
      </div>
    </div>
  );
};

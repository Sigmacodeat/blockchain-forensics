/**
 * Mixer Detection Component
 * ==========================
 * 
 * Schnelle Prüfung, ob eine Adresse Mixer verwendet hat
 */

import React, { useState } from 'react';
import { 
  Search, 
  AlertTriangle, 
  Shield, 
  TrendingUp,
  CheckCircle,
  XCircle
} from 'lucide-react';

interface MixerDetectionResult {
  has_mixer_activity: boolean;
  mixers_used: string[];
  total_deposits: number;
  total_withdrawals: number;
  risk_score: number;
}

export const MixerDetection: React.FC = () => {
  const [address, setAddress] = useState('');
  const [chain, setChain] = useState('ethereum');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<MixerDetectionResult | null>(null);
  const [error, setError] = useState('');

  const handleCheck = async () => {
    if (!address) return;

    setLoading(true);
    setError('');
    setResult(null);

    try {
      const response = await fetch('/api/v1/demixing/detect-mixer', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          address,
          chain
        })
      });

      if (!response.ok) {
        throw new Error(`Error: ${response.statusText}`);
      }

      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const getRiskLevel = (score: number): { label: string; color: string } => {
    if (score === 0) return { label: 'Clean', color: 'green' };
    if (score < 0.3) return { label: 'Low Risk', color: 'yellow' };
    if (score < 0.7) return { label: 'Medium Risk', color: 'orange' };
    return { label: 'High Risk', color: 'red' };
  };

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-cyan-600 rounded-lg p-6 text-white">
        <h1 className="text-3xl font-bold mb-2">
          🔍 Mixer Detection
        </h1>
        <p className="text-blue-100">
          Schnelle Prüfung: Hat diese Adresse Privacy Mixer verwendet?
        </p>
      </div>

      {/* Input Form */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2">
              Wallet Address
            </label>
            <input
              type="text"
              value={address}
              onChange={(e) => setAddress(e.target.value)}
              placeholder="0x..."
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Chain</label>
            <select
              value={chain}
              onChange={(e) => setChain(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg"
            >
              <option value="ethereum">Ethereum</option>
              <option value="bsc">BSC</option>
              <option value="polygon">Polygon</option>
              <option value="bitcoin">Bitcoin</option>
            </select>
          </div>

          <button
            onClick={handleCheck}
            disabled={!address || loading}
            className="w-full bg-gradient-to-r from-blue-600 to-cyan-600 text-white py-3 rounded-lg font-semibold hover:from-blue-700 hover:to-cyan-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent" />
                Checking...
              </>
            ) : (
              <>
                <Search className="w-5 h-5" />
                Check for Mixers
              </>
            )}
          </button>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
          <div>
            <h3 className="font-semibold text-red-900 dark:text-red-100">Error</h3>
            <p className="text-red-700 dark:text-red-300">{error}</p>
          </div>
        </div>
      )}

      {/* Results */}
      {result && (
        <div className="space-y-6">
          {/* Status Card */}
          <div className={`rounded-lg p-6 ${
            result.has_mixer_activity 
              ? 'bg-red-50 dark:bg-red-900/20 border-2 border-red-500' 
              : 'bg-green-50 dark:bg-green-900/20 border-2 border-green-500'
          }`}>
            <div className="flex items-center gap-4">
              {result.has_mixer_activity ? (
                <AlertTriangle className="w-12 h-12 text-red-600" />
              ) : (
                <CheckCircle className="w-12 h-12 text-green-600" />
              )}
              <div className="flex-1">
                <h2 className={`text-2xl font-bold mb-1 ${
                  result.has_mixer_activity 
                    ? 'text-red-900 dark:text-red-100' 
                    : 'text-green-900 dark:text-green-100'
                }`}>
                  {result.has_mixer_activity ? 'Mixer Usage Detected!' : 'No Mixer Activity'}
                </h2>
                <p className={
                  result.has_mixer_activity 
                    ? 'text-red-700 dark:text-red-300' 
                    : 'text-green-700 dark:text-green-300'
                }>
                  {result.has_mixer_activity 
                    ? 'This address has interacted with privacy mixers' 
                    : 'No privacy mixer interactions found'}
                </p>
              </div>
            </div>
          </div>

          {/* Details */}
          {result.has_mixer_activity && (
            <>
              {/* Stats Grid */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                  <div className="flex items-center gap-3 mb-2">
                    <TrendingUp className="w-6 h-6 text-blue-600" />
                    <span className="text-sm text-gray-600 dark:text-gray-400">Deposits</span>
                  </div>
                  <div className="text-3xl font-bold text-gray-900 dark:text-gray-100">
                    {result.total_deposits}
                  </div>
                </div>

                <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                  <div className="flex items-center gap-3 mb-2">
                    <TrendingUp className="w-6 h-6 text-purple-600 transform rotate-180" />
                    <span className="text-sm text-gray-600 dark:text-gray-400">Withdrawals</span>
                  </div>
                  <div className="text-3xl font-bold text-gray-900 dark:text-gray-100">
                    {result.total_withdrawals}
                  </div>
                </div>

                <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                  <div className="flex items-center gap-3 mb-2">
                    <Shield className="w-6 h-6 text-red-600" />
                    <span className="text-sm text-gray-600 dark:text-gray-400">Risk Score</span>
                  </div>
                  <div className="text-3xl font-bold text-gray-900 dark:text-gray-100">
                    {(result.risk_score * 100).toFixed(0)}
                  </div>
                  <div className={`text-sm font-semibold mt-1 ${
                    getRiskLevel(result.risk_score).color === 'green' ? 'text-green-600' :
                    getRiskLevel(result.risk_score).color === 'yellow' ? 'text-yellow-600' :
                    getRiskLevel(result.risk_score).color === 'orange' ? 'text-orange-600' :
                    'text-red-600'
                  }`}>
                    {getRiskLevel(result.risk_score).label}
                  </div>
                </div>
              </div>

              {/* Mixers Used */}
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                <h3 className="text-xl font-bold mb-4">Mixers Used</h3>
                <div className="space-y-2">
                  {result.mixers_used.map((mixer, idx) => (
                    <div key={idx} className="flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                      <AlertTriangle className="w-5 h-5 text-red-600" />
                      <span className="font-mono text-sm text-gray-900 dark:text-gray-100">
                        {mixer}
                      </span>
                      {mixer.toLowerCase().includes('tornado') && (
                        <span className="ml-auto px-3 py-1 bg-red-100 dark:bg-red-900/30 text-red-900 dark:text-red-100 rounded-full text-xs font-semibold">
                          SANCTIONED
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* Risk Assessment */}
              <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
                <h3 className="font-semibold text-yellow-900 dark:text-yellow-100 mb-2">
                  ⚠️ Risk Assessment
                </h3>
                <ul className="space-y-1 text-sm text-yellow-800 dark:text-yellow-200">
                  <li>• Enhanced Due Diligence (EDD) empfohlen</li>
                  <li>• Mögliche Geldwäsche-Aktivität</li>
                  <li>• Compliance-Prüfung notwendig</li>
                  {result.mixers_used.some(m => m.toLowerCase().includes('tornado')) && (
                    <li className="font-semibold">• OFAC Sanctions Check erforderlich!</li>
                  )}
                </ul>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
};

/**
 * KYT Live Monitor - Real-Time Transaction Monitoring
 * ====================================================
 * 
 * WebSocket-based live transaction monitoring with instant risk scoring.
 * Chainalysis Killer Feature: Sub-100ms screening.
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Activity, AlertTriangle, CheckCircle, XCircle, Shield, Zap } from 'lucide-react';

interface KYTAlert {
  id: string;
  timestamp: string;
  chain: string;
  from_address: string;
  to_address: string;
  amount: number;
  risk_level: 'critical' | 'high' | 'medium' | 'low' | 'safe';
  decision: 'allow' | 'review' | 'hold';
  alerts: Array<{
    type: string;
    severity: string;
    message: string;
  }>;
  latency_ms: number;
}

const RISK_COLORS = {
  critical: 'bg-red-500 text-white',
  high: 'bg-orange-500 text-white',
  medium: 'bg-yellow-500 text-slate-900',
  low: 'bg-blue-500 text-white',
  safe: 'bg-green-500 text-white'
};

const DECISION_ICONS = {
  allow: <CheckCircle className="w-5 h-5 text-green-600" />,
  review: <AlertTriangle className="w-5 h-5 text-yellow-600" />,
  hold: <XCircle className="w-5 h-5 text-red-600" />
};

export const KYTLiveMonitor: React.FC = () => {
  const [connected, setConnected] = useState(false);
  const [alerts, setAlerts] = useState<KYTAlert[]>([]);
  const [stats, setStats] = useState({
    total: 0,
    allowed: 0,
    review: 0,
    hold: 0,
    avgLatency: 0
  });
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    // Connect to KYT WebSocket
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/api/v1/ws/kyt`;
    
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('KYT WebSocket connected');
      setConnected(true);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        if (data.type === 'kyt_alert') {
          const alert: KYTAlert = data.data;
          
          setAlerts(prev => [alert, ...prev].slice(0, 100)); // Keep last 100
          
          setStats(prev => ({
            total: prev.total + 1,
            allowed: prev.allowed + (alert.decision === 'allow' ? 1 : 0),
            review: prev.review + (alert.decision === 'review' ? 1 : 0),
            hold: prev.hold + (alert.decision === 'hold' ? 1 : 0),
            avgLatency: (prev.avgLatency * prev.total + alert.latency_ms) / (prev.total + 1)
          }));
        }
      } catch (err) {
        console.error('Failed to parse WebSocket message:', err);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setConnected(false);
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
      setConnected(false);
    };

    return () => {
      ws.close();
    };
  }, []);

  const clearAlerts = useCallback(() => {
    setAlerts([]);
    setStats({ total: 0, allowed: 0, review: 0, hold: 0, avgLatency: 0 });
  }, []);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white dark:bg-slate-800 rounded-lg shadow-lg p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className={`p-3 rounded-lg ${connected ? 'bg-green-100 dark:bg-green-900/30' : 'bg-red-100 dark:bg-red-900/30'}`}>
              <Activity className={`w-6 h-6 ${connected ? 'text-green-600' : 'text-red-600'}`} />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-slate-900 dark:text-white">
                KYT Live Monitor
              </h2>
              <p className="text-sm text-slate-600 dark:text-slate-400 flex items-center gap-2">
                <span className={`w-2 h-2 rounded-full ${connected ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`}></span>
                {connected ? 'Connected - Real-Time Monitoring' : 'Disconnected'}
              </p>
            </div>
          </div>
          <button
            onClick={clearAlerts}
            className="px-4 py-2 bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-600"
          >
            Clear
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <div className="bg-white dark:bg-slate-800 rounded-lg shadow p-4">
          <div className="text-sm text-slate-600 dark:text-slate-400">Total</div>
          <div className="text-2xl font-bold text-slate-900 dark:text-white mt-1">
            {stats.total}
          </div>
        </div>
        <div className="bg-white dark:bg-slate-800 rounded-lg shadow p-4">
          <div className="text-sm text-slate-600 dark:text-slate-400">Allowed</div>
          <div className="text-2xl font-bold text-green-600 dark:text-green-400 mt-1">
            {stats.allowed}
          </div>
        </div>
        <div className="bg-white dark:bg-slate-800 rounded-lg shadow p-4">
          <div className="text-sm text-slate-600 dark:text-slate-400">Review</div>
          <div className="text-2xl font-bold text-yellow-600 dark:text-yellow-400 mt-1">
            {stats.review}
          </div>
        </div>
        <div className="bg-white dark:bg-slate-800 rounded-lg shadow p-4">
          <div className="text-sm text-slate-600 dark:text-slate-400">Hold</div>
          <div className="text-2xl font-bold text-red-600 dark:text-red-400 mt-1">
            {stats.hold}
          </div>
        </div>
        <div className="bg-white dark:bg-slate-800 rounded-lg shadow p-4">
          <div className="text-sm text-slate-600 dark:text-slate-400 flex items-center gap-1">
            <Zap className="w-3 h-3" />
            Avg Latency
          </div>
          <div className="text-2xl font-bold text-purple-600 dark:text-purple-400 mt-1">
            {stats.avgLatency.toFixed(0)}ms
          </div>
        </div>
      </div>

      {/* Alerts Stream */}
      <div className="bg-white dark:bg-slate-800 rounded-lg shadow-lg">
        <div className="p-4 border-b border-slate-200 dark:border-slate-700">
          <h3 className="font-semibold text-slate-900 dark:text-white">
            Live Transaction Stream
          </h3>
        </div>
        <div className="divide-y divide-slate-200 dark:divide-slate-700 max-h-[600px] overflow-y-auto">
          {alerts.map((alert) => (
            <div
              key={alert.id}
              className="p-4 hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors animate-fadeIn"
            >
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center gap-3">
                  <span className={`px-2 py-1 rounded text-xs font-bold ${RISK_COLORS[alert.risk_level]}`}>
                    {alert.risk_level.toUpperCase()}
                  </span>
                  {DECISION_ICONS[alert.decision]}
                  <span className="text-sm text-slate-600 dark:text-slate-400">
                    {new Date(alert.timestamp).toLocaleTimeString()}
                  </span>
                  <span className="text-xs text-slate-500 dark:text-slate-500">
                    {alert.latency_ms}ms
                  </span>
                </div>
                <span className="text-xs font-mono text-slate-500 dark:text-slate-400">
                  {alert.chain}
                </span>
              </div>

              <div className="grid grid-cols-2 gap-3 text-sm mb-2">
                <div>
                  <span className="text-slate-600 dark:text-slate-400">From:</span>
                  <span className="ml-2 font-mono text-slate-900 dark:text-white text-xs">
                    {alert.from_address.slice(0, 10)}...{alert.from_address.slice(-8)}
                  </span>
                </div>
                <div>
                  <span className="text-slate-600 dark:text-slate-400">To:</span>
                  <span className="ml-2 font-mono text-slate-900 dark:text-white text-xs">
                    {alert.to_address.slice(0, 10)}...{alert.to_address.slice(-8)}
                  </span>
                </div>
              </div>

              <div className="flex items-center gap-2 text-sm mb-2">
                <span className="text-slate-600 dark:text-slate-400">Amount:</span>
                <span className="font-semibold text-slate-900 dark:text-white">
                  {alert.amount.toFixed(4)}
                </span>
              </div>

              {alert.alerts.length > 0 && (
                <div className="mt-3 space-y-1">
                  {alert.alerts.map((a, idx) => (
                    <div
                      key={idx}
                      className="flex items-start gap-2 text-xs p-2 bg-slate-100 dark:bg-slate-700 rounded"
                    >
                      <Shield className="w-3 h-3 text-red-500 flex-shrink-0 mt-0.5" />
                      <div>
                        <span className="font-semibold text-slate-900 dark:text-white">
                          {a.type}:
                        </span>
                        <span className="ml-1 text-slate-700 dark:text-slate-300">
                          {a.message}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}

          {alerts.length === 0 && (
            <div className="p-12 text-center">
              <Activity className="w-12 h-12 text-slate-300 dark:text-slate-600 mx-auto mb-3" />
              <p className="text-slate-500 dark:text-slate-400">
                {connected ? 'Waiting for transactions...' : 'Not connected to KYT stream'}
              </p>
            </div>
          )}
        </div>
      </div>

      <style>{`
        @keyframes fadeIn {
          from {
            opacity: 0;
            transform: translateY(-10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        .animate-fadeIn {
          animation: fadeIn 0.3s ease-out;
        }
      `}</style>
    </div>
  );
};

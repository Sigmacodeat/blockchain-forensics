'use client';

import React, { useEffect, useRef, useState } from 'react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { AlertTriangle, X, Check, ExternalLink } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { api } from '@/lib/api';
import { ToastProvider, useToast } from '@/components/ui/toast';

interface Alert {
  id: string;
  rule_type: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  address: string;
  details: string;
  timestamp: string;
  acknowledged: boolean;
}

export function LiveAlertsFeed() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [ws, setWs] = useState<WebSocket | null>(null);
  const navigate = useNavigate();
  const liveRef = useRef<HTMLDivElement>(null);
  const [pendingAck, setPendingAck] = useState<Set<string>>(new Set());
  const [pendingDismiss, setPendingDismiss] = useState<Set<string>>(new Set());
  const { showToast } = useToast();

  useEffect(() => {
    // WebSocket connection
    // Prefer explicit VITE_WS_URL (full ws(s)://... URL). Otherwise derive from API URL.
    const configured = (import.meta as any).env?.VITE_WS_URL as string | undefined
    const apiBase = (import.meta as any).env?.VITE_API_URL as string | undefined
    // Build default ws base: from API base (http://localhost:8000) -> ws://localhost:8000
    const defaultWsBase = (() => {
      const base = apiBase || 'http://localhost:8000'
      return base.replace(/^http/, 'ws')
    })()
    // Our backend mounts ws under /api/v1/ws/alerts
    const wsUrl = configured || `${defaultWsBase}/api/v1`;
    let socket: WebSocket | null = null;
    let reconnectTimer: number | undefined;

    const connect = () => {
      socket = new WebSocket(`${wsUrl}/ws/alerts`);

      socket.onopen = () => {
        console.log('WebSocket connected');
        setWs(socket);
      };

      socket.onmessage = (event) => {
        try {
          const alert = JSON.parse(event.data);
          setAlerts((prev) => [alert, ...prev].slice(0, 50)); // Keep last 50
          // Announce new alert to screen readers
          if (liveRef.current) {
            liveRef.current.textContent = `Neuer Alert: ${alert.rule_type} für Adresse ${alert.address} mit Schweregrad ${String(alert.severity)}`;
          }
        } catch (error) {
          console.error('Error parsing alert:', error);
        }
      };

      socket.onerror = (error) => {
        console.error('WebSocket error:', error);
      };

      socket.onclose = () => {
        console.log('WebSocket disconnected, retrying in 3s...');
        reconnectTimer = window.setTimeout(connect, 3000);
      };
    };
    connect();

    return () => {
      if (reconnectTimer) window.clearTimeout(reconnectTimer);
      socket?.close();
    };
  }, []);

  const handleAcknowledge = async (alertId: string) => {
    const prev = alerts;
    setPendingAck((s) => new Set(s).add(alertId));
    setAlerts((p) => p.map((a) => (a.id === alertId ? { ...a, acknowledged: true } : a)));
    try {
      await api.post(`/api/v1/alerts/${alertId}/acknowledge`);
      if (liveRef.current) liveRef.current.textContent = 'Alert bestätigt.';
      // Toast with undo
      showToast({
        type: 'success',
        title: 'Alert bestätigt',
        message: 'Die Bestätigung kann rückgängig gemacht werden.',
        action: {
          label: 'Rückgängig',
          onClick: () => {
            setAlerts((p) => p.map((a) => (a.id === alertId ? { ...a, acknowledged: false } : a)));
          },
        },
      });
    } catch (e) {
      console.error('Acknowledge failed', e);
      setAlerts(prev);
    } finally {
      setPendingAck((s) => {
        const n = new Set(s);
        n.delete(alertId);
        return n;
      });
    }
  };

  const handleDismiss = async (alertId: string) => {
    const prev = alerts;
    const removed = alerts.find((a) => a.id === alertId);
    setPendingDismiss((s) => new Set(s).add(alertId));
    setAlerts((p) => p.filter((a) => a.id !== alertId));
    try {
      await api.post(`/api/v1/alerts/${alertId}/dismiss`);
      if (liveRef.current) liveRef.current.textContent = 'Alert entfernt.';
      // Toast with undo
      if (removed) {
        showToast({
          type: 'info',
          title: 'Alert entfernt',
          message: 'Entfernen rückgängig machen?',
          action: {
            label: 'Rückgängig',
            onClick: () => {
              setAlerts((p) => [removed, ...p].slice(0, 50));
            },
          },
        });
      }
    } catch (e) {
      console.error('Dismiss failed', e);
      setAlerts(prev);
    } finally {
      setPendingDismiss((s) => {
        const n = new Set(s);
        n.delete(alertId);
        return n;
      });
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300 border-red-300 dark:border-red-700';
      case 'high':
        return 'bg-orange-100 dark:bg-orange-900/30 text-orange-800 dark:text-orange-300 border-orange-300 dark:border-orange-700';
      case 'medium':
        return 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-300 border-yellow-300 dark:border-yellow-700';
      default:
        return 'bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300 border-blue-300 dark:border-blue-700';
    }
  };

  const getSeverityLabel = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'Kritisch';
      case 'high':
        return 'Hoch';
      case 'medium':
        return 'Mittel';
      case 'low':
        return 'Niedrig';
      default:
        return severity.toUpperCase();
    }
  };

  return (
    <div className="space-y-3 max-h-[600px] overflow-y-auto">
      {/* Live region for announcements */}
      <div ref={liveRef} className="sr-only" aria-live="polite" />
      {/* Connection Status */}
      <div className="flex items-center gap-2 text-xs text-gray-600 dark:text-gray-400 mb-4 px-3 py-2 bg-gradient-to-r from-gray-50 to-transparent dark:from-slate-800/50 dark:to-transparent rounded-lg border border-gray-200 dark:border-slate-700" aria-live="polite">
        <div className={`w-2 h-2 rounded-full ${
          ws?.readyState === WebSocket.OPEN 
            ? 'bg-green-500 dark:bg-green-400 animate-pulse shadow-[0_0_8px_rgba(34,197,94,0.6)]' 
            : 'bg-gray-400 dark:bg-gray-500'
        }`} />
        <span className="font-medium">
          {ws?.readyState === WebSocket.OPEN ? '🔴 Live verbunden' : '⚠️ Verbindung wird hergestellt...'}
        </span>
      </div>

      {alerts.length === 0 && (
        <div className="text-center py-12 px-4 bg-gradient-to-br from-gray-50 to-gray-100 dark:from-slate-800/50 dark:to-slate-900/50 rounded-xl border border-gray-200 dark:border-slate-700">
          <div className="relative inline-block mb-4">
            <div className="absolute inset-0 bg-primary-500 dark:bg-primary-400 rounded-full blur-xl opacity-20 animate-pulse" />
            <AlertTriangle className="relative w-12 h-12 mx-auto text-gray-400 dark:text-gray-500" />
          </div>
          <p className="text-gray-700 dark:text-gray-300 font-medium mb-2">✨ Keine aktiven Alerts</p>
          <p className="text-xs text-gray-500 dark:text-gray-400">Neue Sicherheitshinweise erscheinen hier automatisch in Echtzeit</p>
        </div>
      )}

      <div role="list" aria-label="Live Alerts Liste" className="space-y-3">
      {alerts.map((alert, idx) => (
        <div
          key={alert.id}
          className={`relative overflow-hidden p-4 rounded-xl transition-all duration-300 ${
            alert.acknowledged 
              ? 'opacity-60 bg-gradient-to-r from-gray-100 to-gray-50 dark:from-slate-800/30 dark:to-slate-900/30 border border-gray-300 dark:border-slate-700' 
              : 'bg-gradient-to-r from-white to-gray-50 dark:from-slate-800 dark:to-slate-900 border hover:border-primary-300 dark:hover:border-primary-600 hover:shadow-lg'
          } ${
            alert.severity === 'critical' 
              ? 'border-red-300 dark:border-red-700 shadow-[0_0_20px_rgba(239,68,68,0.2)] dark:shadow-[0_0_20px_rgba(239,68,68,0.3)]' 
              : 'border-gray-200 dark:border-slate-700'
          }`}
          role="listitem"
          aria-label={`Alert ${idx + 1}: ${alert.rule_type}, Schweregrad ${alert.severity}, Adresse ${alert.address}`}
        >
          {/* Severity Gradient Accent */}
          <div className={`absolute left-0 top-0 bottom-0 w-1 ${
            alert.severity === 'critical' ? 'bg-gradient-to-b from-red-500 to-red-700' :
            alert.severity === 'high' ? 'bg-gradient-to-b from-orange-500 to-orange-700' :
            alert.severity === 'medium' ? 'bg-gradient-to-b from-yellow-500 to-yellow-700' :
            'bg-gradient-to-b from-blue-500 to-blue-700'
          }`} />
          <div className="flex items-start justify-between mb-3 pl-3">
            <div className="flex items-center gap-3">
              <div className={`relative p-2 rounded-lg ${
                alert.severity === 'critical' ? 'bg-red-100 dark:bg-red-900/30' :
                alert.severity === 'high' ? 'bg-orange-100 dark:bg-orange-900/30' :
                alert.severity === 'medium' ? 'bg-yellow-100 dark:bg-yellow-900/30' :
                'bg-blue-100 dark:bg-blue-900/30'
              }`}>
                <AlertTriangle
                  className={`w-4 h-4 ${
                    alert.severity === 'critical'
                      ? 'text-red-600 dark:text-red-400'
                      : alert.severity === 'high'
                      ? 'text-orange-600 dark:text-orange-400'
                      : alert.severity === 'medium'
                      ? 'text-yellow-600 dark:text-yellow-400'
                      : 'text-blue-600 dark:text-blue-400'
                  }`}
                />
              </div>
              <div>
                <span className="font-bold text-sm text-gray-900 dark:text-white">{alert.rule_type}</span>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Badge className={`${getSeverityColor(alert.severity)} font-bold border`}>
                {getSeverityLabel(alert.severity)}
              </Badge>
              {!alert.acknowledged && (
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => handleAcknowledge(alert.id)}
                  aria-label={`Alert bestätigen: ${alert.rule_type}`}
                  title="Als bestätigt markieren"
                  disabled={pendingAck.has(alert.id)}
                >
                  <Check className="w-3 h-3" />
                </Button>
              )}
              <Button
                size="sm"
                variant="ghost"
                onClick={() => handleDismiss(alert.id)}
                aria-label={`Alert verwerfen: ${alert.rule_type}`}
                title="Alert aus Liste entfernen"
                disabled={pendingDismiss.has(alert.id)}
              >
                <X className="w-3 h-3" />
              </Button>
            </div>
          </div>

          <div className="pl-3 mb-3">
            <code className="text-xs font-mono block px-3 py-2 bg-gray-100 dark:bg-slate-900/50 border border-gray-200 dark:border-slate-700 rounded-lg text-gray-700 dark:text-gray-300">
              {alert.address}
            </code>
          </div>

          <p className="text-sm text-gray-700 dark:text-gray-300 mb-3 pl-3 leading-relaxed">{alert.details}</p>

          <div className="flex items-center justify-between pl-3 pt-3 border-t border-gray-200 dark:border-slate-700">
            <div className="flex items-center gap-2">
              <div className="w-1.5 h-1.5 bg-gray-400 dark:bg-gray-500 rounded-full" />
              <span className="text-xs font-medium text-gray-600 dark:text-gray-400">
                {new Date(alert.timestamp).toLocaleTimeString('de-DE', { 
                  hour: '2-digit', 
                  minute: '2-digit',
                  second: '2-digit'
                })}
              </span>
            </div>
            <div className="flex gap-2">
              <Button
                size="sm"
                variant="outline"
                onClick={() => navigate(`/trace?source=${alert.address}`)}
                aria-label={`Adresse im Trace öffnen: ${alert.address}`}
                title="Trace öffnen"
                className="bg-primary-50 dark:bg-primary-900/20 hover:bg-primary-100 dark:hover:bg-primary-900/40 text-primary-700 dark:text-primary-300 border-primary-200 dark:border-primary-800"
              >
                <ExternalLink className="w-3 h-3 mr-1" />
                Trace
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => navigate(`/investigator?address=${alert.address}`)}
                aria-label={`Investigation öffnen für Adresse: ${alert.address}`}
                title="Investigation öffnen"
                className="bg-blue-50 dark:bg-blue-900/20 hover:bg-blue-100 dark:hover:bg-blue-900/40 text-blue-700 dark:text-blue-300 border-blue-200 dark:border-blue-800"
              >
                Investigate
              </Button>
            </div>
          </div>
        </div>
      ))}
      </div>
    </div>
  );
}

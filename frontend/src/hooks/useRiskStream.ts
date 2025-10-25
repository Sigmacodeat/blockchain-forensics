import { useEffect, useRef, useState } from 'react';

export type RiskEvent =
  | { type: 'risk.ready'; ok: boolean }
  | { type: 'risk.typing'; ok: boolean }
  | { type: 'risk.error'; detail: string }
  | { type: 'risk.result'; payload: {
      chain: string;
      address: string;
      score: number;
      factors?: Record<string, number> | null;
      categories?: string[] | null;
      reasons?: string[] | null;
    }};

export interface UseRiskStreamOptions {
  apiBase?: string; // e.g. "/api/v1"
  autoStart?: boolean;
}

export function useRiskStream(chain: string, address: string, opts: UseRiskStreamOptions = {}) {
  const apiBase = opts.apiBase ?? '/api/v1';
  const [connected, setConnected] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [score, setScore] = useState<number | null>(null);
  const [categories, setCategories] = useState<string[] | null>(null);
  const [reasons, setReasons] = useState<string[] | null>(null);
  const [factors, setFactors] = useState<Record<string, number> | null>(null);
  const esRef = useRef<EventSource | null>(null);

  const start = () => {
    if (esRef.current) return; // already started
    if (!chain || !address) return;
    setLoading(true);
    setError(null);

    const url = `${apiBase}/risk/stream?chain=${encodeURIComponent(chain)}&address=${encodeURIComponent(address)}`;
    const es = new EventSource(url);
    esRef.current = es;

    es.addEventListener('risk.ready', () => {
      setConnected(true);
    });

    es.addEventListener('risk.typing', () => {
      setLoading(true);
    });

    es.addEventListener('risk.error', (e: MessageEvent) => {
      try {
        const data = JSON.parse((e as MessageEvent).data);
        setError(data.detail || 'error');
      } catch {
        setError('error');
      }
      setLoading(false);
    });

    es.addEventListener('risk.result', (e: MessageEvent) => {
      try {
        const data = JSON.parse((e as MessageEvent).data);
        const p = data as RiskEvent & { payload: any };
        setScore(p.payload?.score ?? null);
        setCategories(p.payload?.categories ?? null);
        setReasons(p.payload?.reasons ?? null);
        setFactors(p.payload?.factors ?? null);
        setLoading(false);
      } catch (err) {
        setError('parse_error');
        setLoading(false);
      }
    });

    es.onerror = () => {
      setError('connection_error');
      setLoading(false);
      setConnected(false);
    };
  };

  const stop = () => {
    if (esRef.current) {
      esRef.current.close();
      esRef.current = null;
      setConnected(false);
    }
  };

  useEffect(() => {
    if (opts.autoStart !== false) {
      start();
    }
    return () => stop();
  }, [chain, address, apiBase]);

  return {
    connected,
    loading,
    error,
    score,
    categories,
    reasons,
    factors,
    start,
    stop,
  };
}

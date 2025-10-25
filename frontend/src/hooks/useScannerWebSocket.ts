import { useEffect, useRef, useState } from 'react';

export interface ScanProgress {
  scan_id: string;
  progress: number;
  current: number;
  total: number;
  message: string;
}

export function useScannerWebSocket(userId: string | null) {
  const [progress, setProgress] = useState<ScanProgress | null>(null);
  const [result, setResult] = useState<any>(null);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!userId) return;

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.hostname;
    const port = import.meta.env.VITE_BACKEND_PORT || '8000';
    const wsUrl = `${protocol}//${host}:${port}/api/v1/ws/scanner/${userId}`;

    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      setConnected(true);
      console.log('Scanner WebSocket connected');
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'scan.progress') {
          setProgress({
            scan_id: data.scan_id,
            progress: data.progress,
            current: data.current,
            total: data.total,
            message: data.message || '',
          });
        } else if (data.type === 'scan.complete') {
          setResult(data.result);
          setProgress(null);
        }
      } catch (e) {
        console.error('Scanner WS parse error:', e);
      }
    };

    ws.onerror = (err) => {
      console.error('Scanner WS error:', err);
      setConnected(false);
    };

    ws.onclose = () => {
      setConnected(false);
      console.log('Scanner WebSocket closed');
    };

    return () => {
      ws.close();
    };
  }, [userId]);

  const subscribe = (scanId: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ action: 'subscribe', scan_id: scanId }));
    }
  };

  return { progress, result, connected, subscribe };
}

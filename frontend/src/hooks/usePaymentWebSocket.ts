/**
 * WebSocket Hook for Real-Time Payment Updates
 * Provides instant notifications when payment status changes
 */
import { useState, useEffect, useCallback, useRef } from 'react';

interface PaymentUpdate {
  type: 'connected' | 'status_update' | 'final_status' | 'error';
  payment_id: number;
  payment_status?: string;
  pay_in_hash?: string;
  order_id?: string;
  updated_at?: string;
  timestamp?: string;
  message?: string;
}

interface UsePaymentWebSocketReturn {
  status: string;
  connected: boolean;
  error: string | null;
  txHash: string | null;
  lastUpdate: Date | null;
}

const WS_URL = import.meta.env.VITE_WS_URL || (() => {
  try {
    const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    return `${proto}//${host}`;
  } catch {
    return 'ws://localhost:8000';
  }
})();

export const usePaymentWebSocket = (paymentId: number | null): UsePaymentWebSocketReturn => {
  const [status, setStatus] = useState<string>('pending');
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [txHash, setTxHash] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttempts = useRef(0);

  const connect = useCallback(() => {
    if (!paymentId || wsRef.current) return;

    try {
      const ws = new WebSocket(`${WS_URL}/api/v1/ws/payment/${paymentId}`);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('Payment WebSocket connected');
        setConnected(true);
        setError(null);
        reconnectAttempts.current = 0;
      };

      ws.onmessage = (event) => {
        try {
          const data: PaymentUpdate = JSON.parse(event.data);
          
          switch (data.type) {
            case 'connected':
              console.log('WebSocket connection confirmed');
              break;
              
            case 'status_update':
              if (data.payment_status) {
                setStatus(data.payment_status);
                setLastUpdate(new Date());
                
                if (data.pay_in_hash) {
                  setTxHash(data.pay_in_hash);
                }
                
                console.log(`Payment ${paymentId} status: ${data.payment_status}`);
              }
              break;
              
            case 'final_status':
              if (data.payment_status) {
                setStatus(data.payment_status);
                setLastUpdate(new Date());
                console.log(`Payment ${paymentId} finalized: ${data.payment_status}`);
              }
              // Don't reconnect on final status
              reconnectAttempts.current = 999;
              break;
              
            case 'error':
              setError(data.message || 'WebSocket error');
              console.error('Payment WebSocket error:', data.message);
              break;
          }
        } catch (err) {
          console.error('Error parsing WebSocket message:', err);
        }
      };

      ws.onerror = (event) => {
        console.error('WebSocket error:', event);
        setError('Connection error');
        setConnected(false);
      };

      ws.onclose = (event) => {
        console.log('WebSocket closed:', event.code, event.reason);
        setConnected(false);
        wsRef.current = null;

        // Auto-reconnect with exponential backoff (max 3 attempts)
        if (reconnectAttempts.current < 3 && !['finished', 'failed', 'expired'].includes(status)) {
          const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 10000);
          console.log(`Reconnecting in ${delay}ms (attempt ${reconnectAttempts.current + 1}/3)`);
          
          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectAttempts.current++;
            connect();
          }, delay);
        }
      };
    } catch (err) {
      console.error('Error creating WebSocket:', err);
      setError('Failed to connect');
    }
  }, [paymentId, status]);

  useEffect(() => {
    connect();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [connect]);

  return {
    status,
    connected,
    error,
    txHash,
    lastUpdate
  };
};

export default usePaymentWebSocket;

/**
 * WebSocket Hook for Intelligence Network live updates
 * 
 * Events:
 * - flag.created: New flag submitted
 * - flag.confirmed: Flag confirmed
 * - check.performed: Address checked
 * - member.joined: New member joined
 * - stats.updated: Network stats updated
 */

import { useEffect, useState, useCallback, useRef } from 'react';

export interface IntelligenceEvent {
  type: 'flag.created' | 'flag.confirmed' | 'check.performed' | 'member.joined' | 'stats.updated';
  data: any;
  timestamp: string;
}

export interface UseIntelligenceWSOptions {
  onEvent?: (event: IntelligenceEvent) => void;
  onFlagCreated?: (data: any) => void;
  onFlagConfirmed?: (data: any) => void;
  onCheckPerformed?: (data: any) => void;
  onMemberJoined?: (data: any) => void;
  onStatsUpdated?: (data: any) => void;
}

export function useIntelligenceWS(options?: UseIntelligenceWSOptions) {
  const [connected, setConnected] = useState(false);
  const [lastEvent, setLastEvent] = useState<IntelligenceEvent | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  const reconnectAttemptsRef = useRef(0);

  const connect = useCallback(() => {
    try {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = window.location.host;
      const wsUrl = `${protocol}//${host}/api/v1/ws/intelligence`;

      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        console.log('[Intelligence WS] Connected');
        setConnected(true);
        reconnectAttemptsRef.current = 0;

        // Start keepalive ping
        const pingInterval = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send('ping');
          }
        }, 30000); // 30s ping

        ws.addEventListener('close', () => {
          clearInterval(pingInterval);
        });
      };

      ws.onmessage = (event) => {
        try {
          if (event.data === 'pong') return; // Keepalive

          const message: IntelligenceEvent = JSON.parse(event.data);
          setLastEvent(message);

          // Trigger callbacks
          if (options?.onEvent) {
            options.onEvent(message);
          }

          switch (message.type) {
            case 'flag.created':
              options?.onFlagCreated?.(message.data);
              break;
            case 'flag.confirmed':
              options?.onFlagConfirmed?.(message.data);
              break;
            case 'check.performed':
              options?.onCheckPerformed?.(message.data);
              break;
            case 'member.joined':
              options?.onMemberJoined?.(message.data);
              break;
            case 'stats.updated':
              options?.onStatsUpdated?.(message.data);
              break;
          }
        } catch (err) {
          console.error('[Intelligence WS] Parse error:', err);
        }
      };

      ws.onerror = (error) => {
        console.error('[Intelligence WS] Error:', error);
      };

      ws.onclose = () => {
        console.log('[Intelligence WS] Disconnected');
        setConnected(false);
        wsRef.current = null;

        // Reconnect with exponential backoff
        const delay = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current), 30000);
        reconnectAttemptsRef.current++;

        reconnectTimeoutRef.current = setTimeout(() => {
          if (reconnectAttemptsRef.current <= 5) {
            console.log(`[Intelligence WS] Reconnecting (attempt ${reconnectAttemptsRef.current})...`);
            connect();
          }
        }, delay);
      };

      wsRef.current = ws;
    } catch (err) {
      console.error('[Intelligence WS] Connection error:', err);
    }
  }, [options]);

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
    connected,
    lastEvent,
  };
}

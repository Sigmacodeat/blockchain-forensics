import React, { useState, useEffect, useRef } from 'react';
import { QRCodeSVG } from 'qrcode.react';
import { CheckCircle, Clock, XCircle, Copy, ExternalLink } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';

interface PaymentStatus {
  order_id: string;
  status: 'pending' | 'paid' | 'expired' | 'not_found';
  received_amount_btc?: string;
  expected_amount_btc?: string;
  address?: string;
  txid?: string;
  paid_at?: string;
  expires_at?: string; // Add expires_at field
}

interface BTCInvoiceCheckoutProps {
  orderId: string;
  onSuccess?: (payment: PaymentStatus) => void;
  onExpire?: () => void;
  onError?: (error: string) => void;
}

export const BTCInvoiceCheckout: React.FC<BTCInvoiceCheckoutProps> = ({
  orderId,
  onSuccess,
  onExpire,
  onError
}) => {
  const [status, setStatus] = useState<PaymentStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [timeLeft, setTimeLeft] = useState<number>(0);
  const [copied, setCopied] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Fetch initial invoice status
  useEffect(() => {
    fetchInvoiceStatus();
  }, [orderId]);

  // Setup real-time updates via WebSocket or polling
  useEffect(() => {
    if (!status || status.status !== 'pending') return;

    connectWebSocket();

    return () => {
      disconnectWebSocket();
    };
  }, [status?.status]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnectWebSocket();
    };
  }, []);

  // Countdown timer for expiration
  useEffect(() => {
    if (!status?.expires_at) return;

    const expiresAt = new Date(status.expires_at);
    const updateTimer = () => {
      const now = new Date();
      const diff = expiresAt.getTime() - now.getTime();
      if (diff <= 0) {
        setTimeLeft(0);
        onExpire?.();
      } else {
        setTimeLeft(Math.floor(diff / 1000));
      }
    };

    updateTimer();
    const timer = setInterval(updateTimer, 1000);
    return () => clearInterval(timer);
  }, [status?.expires_at]);

  const fetchInvoiceStatus = async () => {
    try {
      const response = await fetch(`/api/v1/crypto-payments/invoice/${orderId}`);
      if (!response.ok) throw new Error('Failed to fetch invoice status');

      const data = await response.json();
      setStatus(data);
      setError(null);

      if (data.status === 'paid') {
        onSuccess?.(data);
      } else if (data.status === 'expired') {
        onExpire?.();
      }
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMsg);
      onError?.(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const connectWebSocket = () => {
    if (wsRef.current) return; // Already connected

    // Get JWT token from localStorage (assuming it's stored there)
    const token = localStorage.getItem('auth_token') || localStorage.getItem('token');
    if (!token) {
      console.warn('No auth token found, falling back to polling');
      startPolling();
      return;
    }

    try {
      const wsUrl = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/api/v1/ws/invoice/${orderId}?token=${encodeURIComponent(token)}`;
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        console.log('WebSocket connected for invoice updates');
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'invoice_status_update') {
            handleStatusUpdate(data);
          } else if (data.type === 'pong') {
            // Keepalive response
          }
        } catch (e) {
          console.error('Failed to parse WebSocket message:', e);
        }
      };

      ws.onclose = (event) => {
        console.log('WebSocket disconnected:', event.code, event.reason);
        wsRef.current = null;

        // If not intentionally closed and status is still pending, try reconnect or fallback to polling
        if (event.code !== 1000 && status?.status === 'pending') {
          reconnectTimeoutRef.current = setTimeout(() => {
            console.log('Attempting WebSocket reconnect...');
            connectWebSocket();
          }, 5000); // Reconnect after 5 seconds
        } else if (status?.status === 'pending') {
          console.log('WebSocket failed, falling back to polling');
          startPolling();
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };

      wsRef.current = ws;

      // Send ping every 30 seconds to keep connection alive
      const pingInterval = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: 'ping' }));
        } else {
          clearInterval(pingInterval);
        }
      }, 30000);

    } catch (error) {
      console.error('Failed to create WebSocket:', error);
      startPolling();
    }
  };

  const disconnectWebSocket = () => {
    if (wsRef.current) {
      wsRef.current.close(1000, 'Component unmounting');
      wsRef.current = null;
    }
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    stopPolling();
  };

  const startPolling = () => {
    if (reconnectTimeoutRef.current) return; // Already polling
    reconnectTimeoutRef.current = setInterval(fetchInvoiceStatus, 10000); // Poll every 10s
  };

  const stopPolling = () => {
    if (reconnectTimeoutRef.current) {
      clearInterval(reconnectTimeoutRef.current as NodeJS.Timeout);
      reconnectTimeoutRef.current = null;
    }
  };

  const handleStatusUpdate = (data: any) => {
    setStatus(data);
    setError(null);

    if (data.status === 'paid') {
      onSuccess?.(data);
    } else if (data.status === 'expired') {
      onExpire?.();
    }
  };

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getStatusIcon = () => {
    switch (status?.status) {
      case 'paid':
        return <CheckCircle className="h-6 w-6 text-green-600" />;
      case 'expired':
        return <XCircle className="h-6 w-6 text-red-600" />;
      default:
        return <Clock className="h-6 w-6 text-blue-600" />;
    }
  };

  const getStatusBadge = () => {
    switch (status?.status) {
      case 'paid':
        return <Badge variant="default" className="bg-green-100 text-green-800">Bezahlt</Badge>;
      case 'expired':
        return <Badge variant="destructive">Abgelaufen</Badge>;
      default:
        return <Badge variant="secondary">Ausstehend</Badge>;
    }
  };

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    );
  }

  if (!status || status.status === 'not_found') {
    return (
      <Alert variant="destructive">
        <AlertDescription>Invoice nicht gefunden</AlertDescription>
      </Alert>
    );
  }

  return (
    <Card className="w-full max-w-md mx-auto">
      <CardHeader className="text-center">
        <CardTitle className="flex items-center justify-center gap-2">
          {getStatusIcon()}
          BTC Zahlung
        </CardTitle>
        <div className="flex justify-center">
          {getStatusBadge()}
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {status.status === 'pending' && (
          <>
            {/* QR Code */}
            <div className="flex justify-center">
              <QRCodeSVG
                value={`bitcoin:${status.address}?amount=${status.expected_amount_btc}`}
                size={200}
                level="M"
                includeMargin={true}
              />
            </div>

            {/* Amount */}
            <div className="text-center">
              <p className="text-sm text-gray-600">Betrag</p>
              <p className="text-2xl font-bold">{status.expected_amount_btc} BTC</p>
            </div>

            {/* Address */}
            <div className="space-y-2">
              <p className="text-sm text-gray-600">BTC Adresse</p>
              <div className="flex items-center gap-2 p-2 bg-gray-50 rounded">
                <code className="text-xs flex-1 break-all">{status.address}</code>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => copyToClipboard(status.address!)}
                >
                  <Copy className="h-4 w-4" />
                  {copied && <span className="ml-1 text-xs">Kopiert!</span>}
                </Button>
              </div>
            </div>

            {/* Timer */}
            <div className="text-center">
              <p className="text-sm text-gray-600">Verbleibende Zeit</p>
              <p className={`text-xl font-bold ${timeLeft < 300 ? 'text-red-600' : 'text-blue-600'}`}>
                {formatTime(timeLeft)}
              </p>
            </div>

            {/* Progress */}
            {status.received_amount_btc && (
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>Erhalten</span>
                  <span>{status.received_amount_btc} / {status.expected_amount_btc} BTC</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                    style={{
                      width: `${Math.min(100, (parseFloat(status.received_amount_btc || '0') / parseFloat(status.expected_amount_btc || '1')) * 100)}%`
                    }}
                  />
                </div>
              </div>
            )}

            {/* Instructions */}
            <Alert>
              <AlertDescription>
                Scannen Sie den QR-Code mit Ihrer BTC-Wallet oder kopieren Sie die Adresse.
                Die Zahlung wird automatisch erkannt.
              </AlertDescription>
            </Alert>
          </>
        )}

        {status.status === 'paid' && (
          <div className="text-center space-y-4">
            <div className="text-green-600">
              <CheckCircle className="h-12 w-12 mx-auto mb-2" />
              <p className="font-bold">Zahlung erfolgreich!</p>
            </div>
            {status.txid && (
              <div className="text-sm">
                <p className="text-gray-600">Transaktion:</p>
                <a
                  href={`https://blockstream.info/tx/${status.txid}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:underline flex items-center justify-center gap-1"
                >
                  {status.txid.slice(0, 8)}...{status.txid.slice(-8)}
                  <ExternalLink className="h-3 w-3" />
                </a>
              </div>
            )}
          </div>
        )}

        {status.status === 'expired' && (
          <div className="text-center space-y-4">
            <div className="text-red-600">
              <XCircle className="h-12 w-12 mx-auto mb-2" />
              <p className="font-bold">Zahlung abgelaufen</p>
            </div>
            <Button onClick={() => window.location.reload()}>
              Neue Zahlung erstellen
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

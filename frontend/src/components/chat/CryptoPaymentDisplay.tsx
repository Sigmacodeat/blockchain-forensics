/**
 * CryptoPaymentDisplay Component
 * Displays crypto payment details in chat with QR code
 */
import React, { useState, useEffect, useMemo } from 'react';
import { motion, useReducedMotion } from 'framer-motion';
import { Copy, Check, QrCode, ExternalLink, RefreshCw, Wifi, WifiOff, Clock } from 'lucide-react';
import api from '@/lib/api';
import { usePaymentWebSocket } from '@/hooks/usePaymentWebSocket';
import { toast } from 'react-hot-toast';
import Web3PaymentButton from './Web3PaymentButton';
import { useAuth } from '@/contexts/AuthContext';

interface CryptoPaymentDisplayProps {
  paymentId: number;
  address: string;
  amount: number;
  currency: string;
  invoiceUrl: string;
  createdAt?: string; // ISO timestamp
}

interface TimeLeft {
  total: number;
  minutes: number;
  seconds: number;
}

export const CryptoPaymentDisplay: React.FC<CryptoPaymentDisplayProps> = ({
  paymentId,
  address,
  amount,
  currency,
  invoiceUrl,
  createdAt
}) => {
  const [copied, setCopied] = useState(false);
  const [showQR, setShowQR] = useState(false);
  const [qrCode, setQRCode] = useState<string>('');
  const [timeLeft, setTimeLeft] = useState<TimeLeft>({ total: 900000, minutes: 15, seconds: 0 }); // 15 min
  const [extendedExpiry, setExtendedExpiry] = useState<Date | null>(null);
  const [a11yMessage, setA11yMessage] = useState<string>('');
  const [checking, setChecking] = useState(false);
  const [lastManualCheck, setLastManualCheck] = useState<number>(0);
  const prefersReducedMotion = useReducedMotion();
  const { refreshUser } = useAuth();
  // lazy analytics if available
  const safeTrack = (name: string, data?: Record<string, any>) => {
    try {
      if (window?.analytics?.track) window.analytics.track(name, data);
      // optional app tracker (dynamic import bewusst vermieden)
    } catch {}
  };
  
  // Use WebSocket for real-time updates instead of polling
  const { status, connected, error: wsError, txHash: wsTxHash, lastUpdate } = usePaymentWebSocket(paymentId);
  
  // Simple ETA by currency (can be refined by tool output)
  const etaLabel = useMemo(() => {
    const map: Record<string, string> = {
      eth: '5–15 Min',
      usdt: '10–20 Min',
      usdc: '10–20 Min',
      matic: '2–5 Min',
      sol: '1–2 Min',
      bnb: '3–5 Min',
      trx: '1–3 Min'
    };
    return map[(currency || '').toLowerCase()] || '~10 Min';
  }, [currency]);

  // Countdown timer (15 minutes from creation or extended expiry)
  useEffect(() => {
    if (status !== 'pending') return;
    const calculateTimeLeft = (): TimeLeft => {
      let expires: number;
      if (extendedExpiry) {
        expires = extendedExpiry.getTime();
      } else {
        const base = createdAt ? new Date(createdAt).getTime() : Date.now();
        expires = base + (15 * 60 * 1000);
      }
      const now = Date.now();
      const total = expires - now;
      if (total <= 0) return { total: 0, minutes: 0, seconds: 0 };
      const minutes = Math.floor((total / 1000 / 60) % 60);
      const seconds = Math.floor((total / 1000) % 60);
      return { total, minutes, seconds };
    };
    setTimeLeft(calculateTimeLeft());
    setA11yMessage('Zahlungsfenster aktiv. Timer läuft.');
    const interval = setInterval(() => {
      const left = calculateTimeLeft();
      setTimeLeft(left);
      if (left.total <= 0) {
        clearInterval(interval);
        toast.error('⏱️ Payment expired! Create a new one.');
        setA11yMessage('Zahlungsfenster abgelaufen. Bitte neue Zahlung erstellen.');
      } else if (left.total <= 60000 && left.total > 59000) {
        toast('⚠️ Only 1 minute left!', { duration: 5000, icon: '⚠️' });
        setA11yMessage('Nur noch eine Minute verbleibend.');
      } else if (left.total <= 300000 && left.total > 299000) {
        toast('⏰ 5 minutes remaining', { duration: 3000 });
        setA11yMessage('Fünf Minuten verbleibend.');
      }
    }, 1000);
    return () => clearInterval(interval);
  }, [createdAt, status, extendedExpiry]);

  // If WebSocket pushes final finished state, refresh user to update plan immediately
  useEffect(() => {
    if (status === 'finished') {
      (async () => { try { await refreshUser(); } catch {} })();
    }
  }, [status, refreshUser]);

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const loadQRCode = async () => {
    try {
      setShowQR(true);
      if (!qrCode) {
        const response = await api.get(`/api/v1/crypto-payments/qr-code/${paymentId}`);
        setQRCode(response.data.qr_code);
      }
    } catch (error) {
      console.error('Error loading QR code:', error);
    }
  };

  const getStatusBadge = () => {
    const badges: Record<string, { color: string; text: string }> = {
      pending: { color: 'bg-yellow-100 text-yellow-800', text: '⏳ Warte auf Zahlung' },
      waiting: { color: 'bg-blue-100 text-blue-800', text: '⏳ Warte auf Bestätigung' },
      confirming: { color: 'bg-blue-100 text-blue-800', text: '🔄 Wird bestätigt' },
      finished: { color: 'bg-green-100 text-green-800', text: '✅ Erfolgreich' },
      failed: { color: 'bg-red-100 text-red-800', text: '❌ Fehlgeschlagen' },
      expired: { color: 'bg-gray-100 text-gray-800', text: '⏱️ Abgelaufen' }
    };
    
    const badge = badges[status] || badges.pending;
    return (
      <span className={`inline-block px-2 py-1 rounded-full text-xs font-medium ${badge.color}`}>
        {badge.text}
      </span>
    );
  };

  async function checkStatus(): Promise<void> {
    // Debounce: mind. 1,5s zwischen manuellen Checks
    const now = Date.now();
    if (now - lastManualCheck < 1500) return;
    setLastManualCheck(now);
    if (checking) return;
    setChecking(true);
    try {
      const res = await api.get(`/api/v1/crypto-payments/status/${paymentId}`);
      const data = res?.data || {};
      const s = (data.payment_status || status || 'pending') as string;

      // Nutzerfeedback
      if (s === 'finished') {
        toast.success('✅ Zahlung bestätigt!');
        setA11yMessage('Zahlung bestätigt.');
        safeTrack('payment_status_finished', { paymentId });
        try { await refreshUser(); } catch {}
      } else if (s === 'confirming' || s === 'waiting') {
        toast('🔄 Zahlung wird bestätigt...', { icon: '⏳' });
        setA11yMessage('Zahlung wird bestätigt.');
      } else if (s === 'expired') {
        toast.error('⏱️ Zahlung abgelaufen. Bitte neu erstellen.');
        setA11yMessage('Zahlung abgelaufen.');
        safeTrack('payment_status_expired', { paymentId });
      } else if (s === 'failed') {
        toast.error('❌ Zahlung fehlgeschlagen.');
        setA11yMessage('Zahlung fehlgeschlagen.');
        safeTrack('payment_status_failed', { paymentId });
      } else {
        toast('⏳ Warte auf Zahlung...', { icon: '⌛' });
        setA11yMessage('Warte auf Zahlung.');
      }
    } catch (err: any) {
      console.error('Status-Check fehlgeschlagen:', err);
      toast.error('Fehler beim Status-Check');
    } finally {
      setChecking(false);
    }
  }

  // Keyboard shortcuts: Enter = primary action, Esc = close QR
  const onKeyDown = (e: React.KeyboardEvent<HTMLDivElement>) => {
    if (e.key === 'Enter') {
      if (status === 'pending' && !showQR) {
        // prioritize Web3 primary button focus flow
        const web3Primary = document.getElementById('web3-primary') as HTMLButtonElement | null;
        if (web3Primary) {
          web3Primary.click();
          return;
        }
        // else open QR as fallback
        loadQRCode();
      } else if (status !== 'pending') {
        checkStatus();
      }
    }
    if (e.key === 'Escape' && showQR) {
      setShowQR(false);
      setA11yMessage('QR-Code geschlossen.');
    }
  };

  // Auto-Fallback-Polling: wenn WebSocket disconnected & Payment noch offen
  useEffect(() => {
    if (connected || status !== 'pending') return;
    const iv = setInterval(() => {
      // nur pollen, wenn weiterhin disconnected und pending
      if (!connected && status === 'pending') {
        checkStatus();
      }
    }, 10000);
    return () => clearInterval(iv);
  }, [connected, status]);

  return (
    <motion.div
      initial={prefersReducedMotion ? false : { opacity: 0, y: 10 }}
      animate={prefersReducedMotion ? {} : { opacity: 1, y: 0 }}
      className="bg-gradient-to-br from-primary-50 to-primary-50 dark:from-primary-900/20 dark:to-primary-900/20 rounded-lg p-4 my-3 border border-primary-200 dark:border-primary-800"
      tabIndex={0}
      onKeyDown={onKeyDown}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <h4 className="text-sm font-semibold text-gray-900 dark:text-white flex items-center gap-2">
          💎 Crypto Payment
          <span title={connected ? "Live-Updates aktiv" : "Reconnecting..."}>
            {connected ? (
              <Wifi className="w-3 h-3 text-green-500" />
            ) : (
              <WifiOff className="w-3 h-3 text-gray-400" />
            )}
          </span>
        </h4>
        <div className="flex items-center gap-2">
          {getStatusBadge()}
          <button
            onClick={checkStatus}
            disabled={checking || status !== 'pending'}
            className={`p-1 rounded hover:bg-gray-100 dark:hover:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed`}
            title="Status aktualisieren"
            aria-label="Status aktualisieren"
          >
            <RefreshCw className={`w-4 h-4 ${checking ? 'animate-spin text-primary-600' : 'text-gray-600 dark:text-gray-300'}`} />
          </button>
        </div>
      </div>

      {/* Trust microcopy */}
      <div className="mb-3 text-[11px] text-gray-600 dark:text-gray-400">
        Sichere Wallet-Verbindung • Keine privaten Schlüssel • Gebühren transparent
      </div>

      {/* A11y live region (screenreader) */}
      <div className="sr-only" role="status" aria-live="polite">{a11yMessage}</div>

      {/* Amount */}
      <div className="bg-white dark:bg-slate-800 rounded-lg p-3 mb-3">
        <div className="flex items-center justify-between mb-1">
          <div className="text-xs text-gray-600 dark:text-gray-400">Zu zahlender Betrag:</div>
          {status === 'pending' && createdAt && timeLeft.total > 0 && (
            <div className={`flex items-center gap-1 text-xs font-medium ${
              timeLeft.total < 60000 ? 'text-red-600' : timeLeft.total < 300000 ? 'text-yellow-600' : 'text-gray-600'
            }`}>
              <Clock className="w-3 h-3" />
              {timeLeft.minutes}:{timeLeft.seconds.toString().padStart(2, '0')}
            </div>
          )}
        </div>
        <div className="text-2xl font-bold text-primary-600 dark:text-primary-400">
          {amount.toLocaleString(undefined, { maximumFractionDigits: 8 })} {currency.toUpperCase()}
        </div>
        <div className="mt-1 text-[11px] text-gray-600 dark:text-gray-400">
          Erwartete Bestätigungszeit: ~{etaLabel}
        </div>
        {status === 'pending' && (createdAt || extendedExpiry) && timeLeft.total > 0 && (
          <div className="mt-2">
            <button
              onClick={async () => {
                try {
                  const res = await api.post(`/api/v1/crypto-payments/extend/${paymentId}`, { minutes: 10 });
                  const next = res?.data?.client_expiry;
                  if (next) {
                    setExtendedExpiry(new Date(next));
                    toast('⏱️ Zahlungsfenster um 10 Minuten verlängert', { icon: '➕' });
                    setA11yMessage('Zahlungsfenster verlängert um zehn Minuten.');
                  }
                } catch (e) {
                  toast.error('Konnte Zeitfenster nicht verlängern');
                }
              }}
              className="text-xs px-2 py-1 rounded border border-gray-300 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-slate-700"
              aria-label="Zahlungsfenster um zehn Minuten verlängern"
            >
              +10 Min verlängern
            </button>
            <span className="ml-2 text-[11px] text-gray-500">Warum Zeitfenster?</span>
          </div>
        )}
      </div>

      {/* Web3 One-Click Payment */}
      {status === 'pending' && ['eth', 'trx', 'bnb', 'matic'].includes(currency.toLowerCase()) && (
        <div className="mb-3">
          <div className="text-xs text-gray-600 dark:text-gray-400 mb-2 text-center">
            🚀 One-Click Payment (MetaMask/TronLink):
          </div>
          <Web3PaymentButton
            amount={amount}
            currency={currency.toLowerCase() as 'eth' | 'trx' | 'bnb' | 'matic'}
            paymentAddress={address}
            plan="pro"
            onSuccess={(txHash) => {
              toast.success(`✅ Payment sent! TX: ${txHash.slice(0, 10)}...`);
            }}
          />
        </div>
      )}

      {/* Divider */}
      {status === 'pending' && ['eth', 'trx', 'bnb', 'matic'].includes(currency.toLowerCase()) && (
        <div className="relative mb-3">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-gray-300 dark:border-gray-700"></div>
          </div>
          <div className="relative flex justify-center text-xs">
            <span className="bg-gradient-to-br from-primary-50 to-primary-50 dark:from-primary-900/20 dark:to-primary-900/20 px-2 text-gray-500">
              oder manuell bezahlen
            </span>
          </div>
        </div>
      )}

      {/* Address */}
      <div className="bg-white dark:bg-slate-800 rounded-lg p-3 mb-3">
        <div className="text-xs text-gray-600 dark:text-gray-400 mb-2">Zahlungsadresse:</div>
        <div className="flex items-center gap-2">
          <code className="flex-1 text-xs font-mono bg-gray-100 dark:bg-slate-700 px-2 py-1 rounded overflow-x-auto">
            {address}
          </code>
          <button
            onClick={() => copyToClipboard(address)}
            className="p-2 hover:bg-gray-100 dark:hover:bg-slate-700 rounded transition"
            title="Adresse kopieren"
            aria-label="Zahlungsadresse in die Zwischenablage kopieren"
          >
            {copied ? (
              <Check className="w-4 h-4 text-green-600" />
            ) : (
              <Copy className="w-4 h-4 text-gray-600 dark:text-gray-400" />
            )}
          </button>
        </div>
      </div>

      {/* Actions */}
      <div className="flex gap-2">
        <button
          onClick={loadQRCode}
          className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg text-sm font-medium transition"
          aria-label="QR-Code für Wallet-Zahlung anzeigen"
          aria-expanded={showQR}
        >
          <QrCode className="w-4 h-4" />
          QR-Code anzeigen
        </button>
        <a
          href={invoiceUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center justify-center gap-2 px-3 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg text-sm font-medium transition"
          aria-label="Externe Payment-Seite öffnen"
        >
          <ExternalLink className="w-4 h-4" />
          Payment-Page
        </a>
      </div>
      
      {lastUpdate && (
        <div className="mt-2 text-xs text-gray-500 dark:text-gray-400 text-center">
          ⚡ Last update: {new Date(lastUpdate).toLocaleTimeString()}
        </div>
      )}

      {/* QR Code */}
      {showQR && (
        <motion.div
          initial={prefersReducedMotion ? false : { opacity: 0, height: 0 }}
          animate={prefersReducedMotion ? {} : { opacity: 1, height: 'auto' }}
          className="mt-3 bg-white dark:bg-slate-800 rounded-lg p-4 text-center"
        >
          {qrCode ? (
            <>
              <div className="text-xs text-gray-600 dark:text-gray-400 mb-2">
                Scanne mit deiner Wallet:
              </div>
              <img
                src={qrCode}
                alt={`Wallet-QR für Zahlung in ${currency.toUpperCase()}`}
                className="mx-auto w-48 h-48 rounded-lg"
              />
            </>
          ) : (
            <div className="text-sm text-gray-500">Lade QR-Code...</div>
          )}
        </motion.div>
      )}

      {/* Warning */}
      <div className="mt-3 p-2 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
        <p className="text-xs text-yellow-800 dark:text-yellow-200">
          ⚠️ Sende nur <strong>{currency.toUpperCase()}</strong> an diese Adresse!
        </p>
      </div>
    </motion.div>
  );
};

export default CryptoPaymentDisplay;

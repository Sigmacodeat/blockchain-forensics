/**
 * CryptoPaymentModal Component
 * State-of-the-art cryptocurrency payment interface
 * Supports 30+ cryptocurrencies via NOWPayments
 */
import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Check, Copy, ExternalLink, Clock, AlertCircle, Loader2 } from 'lucide-react';
import api from '../lib/api';

interface CryptoPaymentModalProps {
  isOpen: boolean;
  onClose: () => void;
  planName: string;
  priceUSD: number;
  onSuccess?: () => void;
}

interface Currency {
  code: string;
  name: string;
  symbol: string;
  logo: string;
  network: string;
}

interface PaymentData {
  payment_id: number;
  order_id: string;
  pay_address: string;
  pay_amount: number;
  pay_currency: string;
  price_amount: number;
  price_currency: string;
  payment_status: string;
  invoice_url: string;
  expires_at?: string;
}

const CURRENCY_ICONS: Record<string, string> = {
  btc: '₿',
  eth: 'Ξ',
  usdt: '₮',
  usdc: '$',
  bnb: 'BNB',
  sol: 'SOL',
  matic: 'MATIC',
  avax: 'AVAX',
  trx: 'TRX',
  dai: '◈',
  ada: '₳',
  doge: 'Ð',
  ltc: 'Ł',
  xrp: 'XRP',
};

export const CryptoPaymentModal: React.FC<CryptoPaymentModalProps> = ({
  isOpen,
  onClose,
  planName,
  priceUSD,
  onSuccess
}) => {
  const [step, setStep] = useState<'select' | 'payment' | 'success'>('select');
  const [currencies, setCurrencies] = useState<Currency[]>([]);
  const [selectedCurrency, setSelectedCurrency] = useState<Currency | null>(null);
  const [estimatedAmount, setEstimatedAmount] = useState<number>(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>('');
  const [paymentData, setPaymentData] = useState<PaymentData | null>(null);
  const [copied, setCopied] = useState(false);
  const [timeRemaining, setTimeRemaining] = useState<string>('');

  // Fetch available currencies
  useEffect(() => {
    if (isOpen) {
      fetchCurrencies();
    }
  }, [isOpen]);

  // Poll payment status
  useEffect(() => {
    if (paymentData && step === 'payment') {
      const interval = setInterval(() => {
        checkPaymentStatus();
      }, 10000); // Every 10 seconds

      return () => clearInterval(interval);
    }
  }, [paymentData, step]);

  // Update time remaining
  useEffect(() => {
    if (paymentData?.expires_at) {
      const interval = setInterval(() => {
        const now = new Date().getTime();
        const expires = new Date(paymentData.expires_at!).getTime();
        const diff = expires - now;

        if (diff <= 0) {
          setTimeRemaining('Expired');
          clearInterval(interval);
        } else {
          const minutes = Math.floor(diff / 60000);
          const seconds = Math.floor((diff % 60000) / 1000);
          setTimeRemaining(`${minutes}:${seconds.toString().padStart(2, '0')}`);
        }
      }, 1000);

      return () => clearInterval(interval);
    }
  }, [paymentData]);

  const fetchCurrencies = async () => {
    try {
      setLoading(true);
      const response = await api.get('/api/v1/crypto-payments/currencies');
      setCurrencies(response.data.currencies);
    } catch (err: any) {
      setError('Failed to load currencies');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const fetchEstimate = async (currency: Currency) => {
    try {
      setLoading(true);
      const response = await api.post('/api/v1/crypto-payments/estimate', {
        plan: planName,
        currency: currency.code
      });
      setEstimatedAmount(response.data.estimated_amount);
      setError('');
    } catch (err: any) {
      setError('Failed to get estimate');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const createPayment = async () => {
    if (!selectedCurrency) return;

    try {
      setLoading(true);
      setError('');
      const response = await api.post('/api/v1/crypto-payments/create', {
        plan: planName,
        currency: selectedCurrency.code,
        interval: 'monthly',
        recurring: false
      });
      setPaymentData(response.data);
      setStep('payment');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create payment');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const checkPaymentStatus = async () => {
    if (!paymentData) return;

    try {
      const response = await api.get(`/api/v1/crypto-payments/status/${paymentData.payment_id}`);
      const status = response.data.payment_status;

      if (status === 'finished') {
        setStep('success');
        if (onSuccess) onSuccess();
      } else if (status === 'failed' || status === 'expired') {
        setError(`Payment ${status}`);
      }
    } catch (err: any) {
      console.error('Status check error:', err);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleCurrencySelect = async (currency: Currency) => {
    setSelectedCurrency(currency);
    await fetchEstimate(currency);
  };

  const handleClose = () => {
    setStep('select');
    setSelectedCurrency(null);
    setPaymentData(null);
    setError('');
    onClose();
  };

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.95 }}
          className="relative w-full max-w-2xl bg-white dark:bg-slate-800 rounded-2xl shadow-2xl overflow-hidden"
        >
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-slate-200 dark:border-slate-700">
            <div>
              <h2 className="text-2xl font-bold text-slate-900 dark:text-white">
                💎 Pay with Crypto
              </h2>
              <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
                {planName.charAt(0).toUpperCase() + planName.slice(1)} Plan - ${priceUSD}/month
              </p>
            </div>
            <button
              onClick={handleClose}
              className="p-2 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Content */}
          <div className="p-6">
            {error && (
              <div className="mb-4 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg flex items-center gap-3">
                <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400 flex-shrink-0" />
                <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
              </div>
            )}

            {/* Step 1: Select Currency */}
            {step === 'select' && (
              <div>
                <h3 className="text-lg font-semibold mb-4">Select Cryptocurrency</h3>
                
                {loading ? (
                  <div className="flex items-center justify-center py-12">
                    <Loader2 className="w-8 h-8 animate-spin text-primary-600" />
                  </div>
                ) : (
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 max-h-96 overflow-y-auto">
                    {currencies.map((currency) => (
                      <motion.button
                        key={currency.code}
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                        onClick={() => handleCurrencySelect(currency)}
                        className={`p-4 border-2 rounded-xl transition ${
                          selectedCurrency?.code === currency.code
                            ? 'border-primary-600 bg-primary-50 dark:bg-primary-900/20'
                            : 'border-slate-200 dark:border-slate-700 hover:border-primary-300'
                        }`}
                      >
                        <div className="text-3xl mb-2">
                          {CURRENCY_ICONS[currency.code.toLowerCase()] || currency.symbol}
                        </div>
                        <div className="text-sm font-semibold">{currency.symbol}</div>
                        <div className="text-xs text-slate-600 dark:text-slate-400">
                          {currency.name}
                        </div>
                      </motion.button>
                    ))}
                  </div>
                )}

                {selectedCurrency && estimatedAmount > 0 && (
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="mt-6 p-4 bg-slate-50 dark:bg-slate-900/50 rounded-xl"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm text-slate-600 dark:text-slate-400">
                        You'll pay approximately:
                      </span>
                    </div>
                    <div className="text-2xl font-bold text-primary-600">
                      {estimatedAmount.toFixed(8)} {selectedCurrency.symbol}
                    </div>
                    <div className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                      ≈ ${priceUSD} USD
                    </div>
                  </motion.div>
                )}

                <button
                  onClick={createPayment}
                  disabled={!selectedCurrency || loading}
                  className="w-full mt-6 px-6 py-3 bg-gradient-to-r from-primary-600 to-purple-600 text-white font-semibold rounded-xl hover:from-primary-700 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition"
                >
                  {loading ? 'Creating Payment...' : 'Continue to Payment'}
                </button>
              </div>
            )}

            {/* Step 2: Payment */}
            {step === 'payment' && paymentData && (
              <div>
                <div className="mb-6 p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
                  <div className="flex items-center gap-3 mb-2">
                    <Clock className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                    <span className="text-sm font-semibold text-blue-900 dark:text-blue-100">
                      Payment expires in: {timeRemaining}
                    </span>
                  </div>
                  <p className="text-xs text-blue-700 dark:text-blue-300">
                    Send exactly the amount shown below to complete your payment
                  </p>
                </div>

                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium mb-2">Amount to Send</label>
                    <div className="flex items-center gap-3 p-4 bg-slate-50 dark:bg-slate-900/50 rounded-lg">
                      <span className="text-2xl font-bold text-primary-600">
                        {paymentData.pay_amount} {paymentData.pay_currency.toUpperCase()}
                      </span>
                      <button
                        onClick={() => copyToClipboard(paymentData.pay_amount.toString())}
                        className="p-2 hover:bg-slate-200 dark:hover:bg-slate-700 rounded transition"
                      >
                        {copied ? <Check className="w-4 h-4 text-green-600" /> : <Copy className="w-4 h-4" />}
                      </button>
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2">Deposit Address</label>
                    <div className="flex items-center gap-3 p-4 bg-slate-50 dark:bg-slate-900/50 rounded-lg break-all">
                      <code className="flex-1 text-sm">{paymentData.pay_address}</code>
                      <button
                        onClick={() => copyToClipboard(paymentData.pay_address)}
                        className="p-2 hover:bg-slate-200 dark:hover:bg-slate-700 rounded transition flex-shrink-0"
                      >
                        {copied ? <Check className="w-4 h-4 text-green-600" /> : <Copy className="w-4 h-4" />}
                      </button>
                    </div>
                  </div>

                  <div className="p-4 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
                    <p className="text-sm text-yellow-800 dark:text-yellow-200">
                      ⚠️ <strong>Important:</strong> Send only {paymentData.pay_currency.toUpperCase()} to this address. 
                      Sending any other cryptocurrency will result in permanent loss.
                    </p>
                  </div>

                  <a
                    href={paymentData.invoice_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center justify-center gap-2 w-full px-6 py-3 bg-slate-100 dark:bg-slate-700 text-slate-900 dark:text-white font-semibold rounded-xl hover:bg-slate-200 dark:hover:bg-slate-600 transition"
                  >
                    <ExternalLink className="w-5 h-5" />
                    Open Payment Page
                  </a>
                </div>

                <div className="mt-6 text-center text-sm text-slate-600 dark:text-slate-400">
                  Waiting for payment... This will update automatically
                </div>
              </div>
            )}

            {/* Step 3: Success */}
            {step === 'success' && (
              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                className="text-center py-8"
              >
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ delay: 0.2, type: 'spring' }}
                  className="inline-flex items-center justify-center w-20 h-20 bg-green-100 dark:bg-green-900/30 rounded-full mb-6"
                >
                  <Check className="w-10 h-10 text-green-600 dark:text-green-400" />
                </motion.div>
                <h3 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">
                  Payment Successful! 🎉
                </h3>
                <p className="text-slate-600 dark:text-slate-400 mb-6">
                  Your {planName} plan has been activated. Welcome aboard!
                </p>
                <button
                  onClick={handleClose}
                  className="px-8 py-3 bg-gradient-to-r from-primary-600 to-purple-600 text-white font-semibold rounded-xl hover:from-primary-700 hover:to-purple-700 transition"
                >
                  Get Started
                </button>
              </motion.div>
            )}
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
};

export default CryptoPaymentModal;

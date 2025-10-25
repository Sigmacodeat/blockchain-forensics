/**
 * Web3 Payment Button Component
 * One-Click payment with MetaMask, TronLink, etc.
 */
import React, { useEffect, useRef, useState } from 'react';
import { motion } from 'framer-motion';
import { Wallet, Check, Loader2, ExternalLink } from 'lucide-react';
import { useWeb3Wallet } from '@/hooks/useWeb3Wallet';
import { toast } from 'react-hot-toast';
import api from '@/lib/api';
import { track } from '@/lib/analytics';

interface Web3PaymentButtonProps {
  amount: number;
  currency: 'eth' | 'trx' | 'bnb' | 'matic';
  paymentAddress: string;
  plan: string;
  onSuccess: (txHash: string) => void;
}

export const Web3PaymentButton: React.FC<Web3PaymentButtonProps> = ({
  amount,
  currency,
  paymentAddress,
  plan,
  onSuccess
}) => {
  const { wallet, loading: walletLoading, connectMetaMask, connectTronLink, sendTransaction } = useWeb3Wallet();
  const [paying, setPaying] = useState(false);
  const [txHash, setTxHash] = useState<string | null>(null);
  const connectBtnRef = useRef<HTMLButtonElement | null>(null);
  const payBtnRef = useRef<HTMLButtonElement | null>(null);

  const getCurrencyInfo = (curr: string) => {
    const info: Record<string, { name: string; logo: string; decimals: number }> = {
      eth: { name: 'Ethereum', logo: '⟠', decimals: 18 },
      trx: { name: 'Tron', logo: '◈', decimals: 6 },
      bnb: { name: 'BNB', logo: '◆', decimals: 18 },
      matic: { name: 'Polygon', logo: '⬣', decimals: 18 }
    };
    return info[curr] || info.eth;
  };

  const currencyInfo = getCurrencyInfo(currency);

  const handleConnect = async () => {
    // Consent dialog (non-invasive)
    const ok = window.confirm('Sie verbinden Ihre Wallet. Wir speichern keine privaten Schlüssel – nur Transaktionshash & Payment-ID zur Zuordnung. Fortfahren?');
    if (!ok) return;
    if (currency === 'trx') {
      await connectTronLink();
    } else {
      await connectMetaMask();
    }
    track?.('wallet_connect_clicked', { currency });
  };

  const handlePay = async () => {
    if (!wallet.connected) {
      toast.error('Please connect your wallet first!');
      return;
    }

    try {
      setPaying(true);

      // Convert amount to Wei/Sun
      const decimals = currencyInfo.decimals;
      const valueInSmallestUnit = Math.floor(amount * Math.pow(10, decimals)).toString();

      // Send transaction
      const hash = await sendTransaction({
        to: paymentAddress,
        value: valueInSmallestUnit,
        currency
      });

      if (hash) {
        setTxHash(hash);
        
        // Notify backend about transaction
        try {
          await api.post('/api/v1/crypto-payments/web3-payment', {
            tx_hash: hash,
            payment_address: paymentAddress,
            amount,
            currency: currency.toUpperCase(),
            plan
          });
        } catch (error) {
          console.error('Error notifying backend:', error);
        }

        onSuccess(hash);
        toast.success('🎉 Payment successful! Your plan will be activated shortly.');
        track?.('tx_submitted', { currency, amount, plan });
      }
    } catch (error) {
      console.error('Payment error:', error);
      track?.('tx_failed', { currency, reason: (error as any)?.message });
    } finally {
      setPaying(false);
    }
  };

  // Focus management
  useEffect(() => {
    if (!wallet.connected) {
      connectBtnRef.current?.focus();
    } else {
      payBtnRef.current?.focus();
    }
  }, [wallet.connected]);

  if (txHash) {
    // Success state
    const explorerUrl = currency === 'trx' 
      ? `https://tronscan.org/#/transaction/${txHash}`
      : `https://etherscan.io/tx/${txHash}`;

    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="bg-green-50 dark:bg-green-900/20 rounded-lg p-4 border border-green-200 dark:border-green-800"
      >
        <div className="flex items-center gap-2 mb-2">
          <Check className="w-5 h-5 text-green-600" />
          <span className="font-semibold text-green-900 dark:text-green-100">
            Payment Successful!
          </span>
        </div>
        <p className="text-sm text-green-800 dark:text-green-200 mb-3">
          Transaction submitted. Your plan will be activated once confirmed on the blockchain.
        </p>
        <a
          href={explorerUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-2 text-sm text-green-700 dark:text-green-300 hover:underline"
        >
          <ExternalLink className="w-4 h-4" />
          View on Explorer
        </a>
      </motion.div>
    );
  }

  if (!wallet.connected) {
    // Connect wallet state
    return (
      <motion.button
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        onClick={handleConnect}
        disabled={walletLoading}
        id="web3-primary"
        ref={connectBtnRef}
        aria-label={`Wallet verbinden und bezahlen mit ${currency.toUpperCase()}`}
        className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white rounded-lg font-medium transition disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
      >
        {walletLoading ? (
          <>
            <Loader2 className="w-5 h-5 animate-spin" />
            Connecting...
          </>
        ) : (
          <>
            <Wallet className="w-5 h-5" />
            Connect {currency === 'trx' ? 'TronLink' : 'MetaMask'} & Pay
          </>
        )}
      </motion.button>
    );
  }

  // Payment state
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-3"
    >
      {/* Wallet info */}
      <div className="bg-gray-100 dark:bg-slate-800 rounded-lg p-3 text-sm">
        <div className="flex items-center justify-between mb-1">
          <span className="text-gray-600 dark:text-gray-400">Connected:</span>
          <span className="font-mono font-medium text-gray-900 dark:text-white">
            {wallet.address?.slice(0, 6)}...{wallet.address?.slice(-4)}
          </span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-gray-600 dark:text-gray-400">Balance:</span>
          <span className="font-medium text-gray-900 dark:text-white">
            {wallet.balance} {currency.toUpperCase()}
          </span>
        </div>
      </div>

      {/* Payment button */}
      <button
        onClick={handlePay}
        disabled={paying || walletLoading}
        ref={payBtnRef}
        aria-label={`Jetzt ${amount} ${currency.toUpperCase()} bezahlen`}
        className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white rounded-lg font-medium transition disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-emerald-500"
      >
        {paying ? (
          <>
            <Loader2 className="w-5 h-5 animate-spin" />
            Processing Payment...
          </>
        ) : (
          <>
            {currencyInfo.logo} Pay {amount} {currency.toUpperCase()}
          </>
        )}
      </button>

      {/* One-Click info */}
      <p className="text-xs text-center text-gray-500 dark:text-gray-400">
        🚀 One-Click Payment - Confirm in your wallet
        {(currency === 'matic' || currency === 'bnb') && (
          <span className="ml-2 inline-block px-2 py-0.5 text-[10px] rounded bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300">
            Empfohlen: niedrige Gebühren
          </span>
        )}
      </p>
    </motion.div>
  );
};

export default Web3PaymentButton;

/**
 * Tornado Cash Demixing Component - Premium Edition
 * ==================================================
 * 
 * State-of-the-art demixing for Tornado Cash with:
 * - Perfect Dark/Light mode contrast
 * - Full i18n support
 * - Glassmorphism design
 * - Forensic-grade results
 * - AI-powered analysis
 */

import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Search, 
  AlertTriangle, 
  CheckCircle, 
  TrendingDown,
  ArrowRight,
  Clock,
  Percent,
  Network,
  ExternalLink,
  Zap,
  Shield,
  Globe,
  Target,
  Info,
  Sparkles
} from 'lucide-react';

interface DemixResult {
  deposits: Array<{
    tx_hash: string;
    timestamp: string;
    amount: number;
    mixer_address: string;
    denomination: number;
  }>;
  likely_withdrawals: Array<{
    tx_hash: string;
    timestamp: string;
    withdrawal_address: string;
    probability: number;
    deposit_tx: string;
  }>;
  probability_scores: Record<string, number>;
  demixing_path: Array<{
    withdrawal_tx: string;
    withdrawal_address: string;
    path: string[];
    end_label: string;
    probability: number;
  }>;
  confidence: number;
  message: string;
}

export const TornadoDemix: React.FC = () => {
  const { t } = useTranslation();
  const [address, setAddress] = useState('');
  const [chain, setChain] = useState('ethereum');
  const [timeWindow, setTimeWindow] = useState(168); // 1 week
  const [maxHops, setMaxHops] = useState(3);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<DemixResult | null>(null);
  const [error, setError] = useState('');

  const handleDemix = async () => {
    if (!address) return;

    setLoading(true);
    setError('');
    setResult(null);

    try {
      const response = await fetch('/api/v1/demixing/tornado-cash', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          address,
          chain,
          max_hops: maxHops,
          time_window_hours: timeWindow
        })
      });

      if (!response.ok) {
        throw new Error(`Error: ${response.statusText}`);
      }

      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto p-4 sm:p-6 space-y-6">
      {/* Premium Hero Header with Glassmorphism */}
      <motion.div 
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-primary-600 via-purple-600 to-blue-600 p-8 text-white"
      >
        {/* Animated Background Pattern */}
        <div className="absolute inset-0 opacity-10">
          <div className="absolute inset-0" style={{
            backgroundImage: 'radial-gradient(circle at 2px 2px, white 1px, transparent 0)',
            backgroundSize: '32px 32px'
          }} />
        </div>
        
        <div className="relative z-10">
          <div className="flex items-center gap-3 mb-3">
            <div className="p-3 bg-white/20 backdrop-blur-sm rounded-xl">
              <Sparkles className="w-8 h-8" />
            </div>
            <div>
              <h1 className="text-3xl sm:text-4xl font-bold">
                {t('privacyDemixing.title')}
              </h1>
              <p className="text-primary-100 mt-1">
                {t('privacyDemixing.subtitle')}
              </p>
            </div>
          </div>
          
          <p className="text-white/90 text-sm sm:text-base max-w-3xl">
            {t('privacyDemixing.description')}
          </p>
          
          {/* Feature Pills */}
          <div className="flex flex-wrap gap-2 mt-4">
            {[
              { icon: Zap, text: t('privacyDemixing.features.aiPowered') },
              { icon: Clock, text: t('privacyDemixing.features.realTime') },
              { icon: Globe, text: t('privacyDemixing.features.multiChain') },
              { icon: Shield, text: t('privacyDemixing.features.forensicGrade') }
            ].map((feature, idx) => (
              <motion.div
                key={idx}
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: idx * 0.1 }}
                className="flex items-center gap-2 px-3 py-1.5 bg-white/20 backdrop-blur-sm rounded-full text-sm"
              >
                <feature.icon className="w-4 h-4" />
                <span>{feature.text}</span>
              </motion.div>
            ))}
          </div>
        </div>
      </motion.div>

      {/* Premium Analysis Form with Glassmorphism */}
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="bg-white/80 dark:bg-slate-900/80 backdrop-blur-xl rounded-2xl shadow-2xl border border-gray-200/50 dark:border-slate-700/50 p-6 sm:p-8"
      >
        <div className="space-y-6">
          {/* How It Works - Info Box */}
          <motion.div 
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-primary-50/50 dark:bg-primary-900/20 border border-primary-200 dark:border-primary-800/50 rounded-xl p-4"
          >
            <div className="flex items-start gap-3">
              <Info className="w-5 h-5 text-primary-600 dark:text-primary-400 flex-shrink-0 mt-0.5" />
              <div>
                <h3 className="font-semibold text-primary-900 dark:text-primary-100 mb-2">
                  {t('privacyDemixing.info.howItWorks')}
                </h3>
                <ol className="text-sm text-primary-700 dark:text-primary-300 space-y-1.5">
                  <li className="flex items-start gap-2">
                    <span className="font-semibold text-primary-600 dark:text-primary-400">1.</span>
                    <span>{t('privacyDemixing.info.step1')}</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="font-semibold text-primary-600 dark:text-primary-400">2.</span>
                    <span>{t('privacyDemixing.info.step2')}</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="font-semibold text-primary-600 dark:text-primary-400">3.</span>
                    <span>{t('privacyDemixing.info.step3')}</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="font-semibold text-primary-600 dark:text-primary-400">4.</span>
                    <span>{t('privacyDemixing.info.step4')}</span>
                  </li>
                </ol>
              </div>
            </div>
          </motion.div>

          {/* Address Input with Enhanced Styling */}
          <div>
            <label className="block text-sm font-semibold text-gray-900 dark:text-gray-100 mb-2">
              {t('privacyDemixing.form.address')}
            </label>
            <div className="relative">
              <Target className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 dark:text-gray-500" />
              <input
                type="text"
                value={address}
                onChange={(e) => setAddress(e.target.value)}
                placeholder={t('privacyDemixing.form.addressPlaceholder')}
                className="w-full pl-12 pr-4 py-3.5 bg-white dark:bg-slate-800 border-2 border-gray-200 dark:border-slate-700 rounded-xl text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:ring-4 focus:ring-primary-500/20 focus:border-primary-500 dark:focus:border-primary-400 transition-all duration-200"
              />
            </div>
          </div>

          {/* Chain & Parameters Grid with Enhanced Contrast */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-semibold text-gray-900 dark:text-gray-100 mb-2">
                {t('privacyDemixing.form.chain')}
              </label>
              <select
                value={chain}
                onChange={(e) => setChain(e.target.value)}
                className="w-full px-4 py-3 bg-white dark:bg-slate-800 border-2 border-gray-200 dark:border-slate-700 rounded-xl text-gray-900 dark:text-gray-100 focus:ring-4 focus:ring-primary-500/20 focus:border-primary-500 dark:focus:border-primary-400 transition-all duration-200 cursor-pointer"
              >
                <option value="ethereum">{t('privacyDemixing.chains.ethereum')}</option>
                <option value="bsc">{t('privacyDemixing.chains.bsc')}</option>
                <option value="polygon">{t('privacyDemixing.chains.polygon')}</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-semibold text-gray-900 dark:text-gray-100 mb-2">
                {t('privacyDemixing.form.timeWindow')}
              </label>
              <input
                type="number"
                value={timeWindow}
                onChange={(e) => setTimeWindow(Number(e.target.value))}
                min="1"
                max="720"
                className="w-full px-4 py-3 bg-white dark:bg-slate-800 border-2 border-gray-200 dark:border-slate-700 rounded-xl text-gray-900 dark:text-gray-100 focus:ring-4 focus:ring-primary-500/20 focus:border-primary-500 dark:focus:border-primary-400 transition-all duration-200"
              />
            </div>

            <div>
              <label className="block text-sm font-semibold text-gray-900 dark:text-gray-100 mb-2">
                {t('privacyDemixing.form.maxHops')}
              </label>
              <input
                type="number"
                value={maxHops}
                onChange={(e) => setMaxHops(Number(e.target.value))}
                min="1"
                max="10"
                className="w-full px-4 py-3 bg-white dark:bg-slate-800 border-2 border-gray-200 dark:border-slate-700 rounded-xl text-gray-900 dark:text-gray-100 focus:ring-4 focus:ring-primary-500/20 focus:border-primary-500 dark:focus:border-primary-400 transition-all duration-200"
              />
            </div>
          </div>

          {/* Premium Submit Button with 3D Effect */}
          <motion.button
            whileHover={{ scale: 1.02, y: -2 }}
            whileTap={{ scale: 0.98 }}
            onClick={handleDemix}
            disabled={!address || loading}
            className="w-full bg-gradient-to-r from-primary-600 via-purple-600 to-blue-600 hover:from-primary-700 hover:via-purple-700 hover:to-blue-700 text-white py-4 rounded-xl font-bold text-lg shadow-2xl shadow-primary-500/50 disabled:opacity-50 disabled:cursor-not-allowed disabled:shadow-none flex items-center justify-center gap-3 transition-all duration-300 relative overflow-hidden group"
          >
            {/* Shimmer Effect */}
            <div className="absolute inset-0 -translate-x-full group-hover:translate-x-full transition-transform duration-1000 bg-gradient-to-r from-transparent via-white/20 to-transparent" />
            
            {loading ? (
              <>
                <motion.div 
                  animate={{ rotate: 360 }}
                  transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                  className="rounded-full h-6 w-6 border-3 border-white border-t-transparent"
                />
                <span>{t('privacyDemixing.form.analyzing')}</span>
              </>
            ) : (
              <>
                <Search className="w-6 h-6" />
                <span>{t('privacyDemixing.form.startButton')}</span>
              </>
            )}
          </motion.button>
        </div>
      </motion.div>

      {/* Premium Error Display */}
      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="bg-red-50 dark:bg-red-900/20 backdrop-blur-sm border-2 border-red-200 dark:border-red-800/50 rounded-xl p-5 flex items-start gap-4 shadow-lg"
          >
            <div className="p-2 bg-red-100 dark:bg-red-900/40 rounded-lg">
              <AlertTriangle className="w-6 h-6 text-red-600 dark:text-red-400" />
            </div>
            <div className="flex-1">
              <h3 className="font-bold text-red-900 dark:text-red-100 mb-1">
                {t('privacyDemixing.error.title')}
              </h3>
              <p className="text-red-700 dark:text-red-300">{error}</p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Premium Results Section */}
      <AnimatePresence>
        {result && (
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="space-y-6"
          >
            {/* Premium Summary Card with Glassmorphism */}
            <motion.div 
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="bg-white/80 dark:bg-slate-900/80 backdrop-blur-xl rounded-2xl shadow-2xl border border-gray-200/50 dark:border-slate-700/50 p-6 sm:p-8"
            >
              <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-6">
                <div>
                  <h2 className="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-white">
                    {t('privacyDemixing.results.title')}
                  </h2>
                  <p className="text-gray-600 dark:text-gray-400 text-sm mt-1">
                    {result.message}
                  </p>
                </div>
                <motion.div 
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ delay: 0.2, type: "spring" }}
                  className="flex items-center gap-3 px-5 py-3 bg-gradient-to-r from-purple-500 to-blue-500 rounded-xl shadow-lg"
                >
                  <Percent className="w-6 h-6 text-white" />
                  <div>
                    <div className="text-xs text-white/80 font-medium">
                      {t('privacyDemixing.results.confidence')}
                    </div>
                    <div className="text-2xl font-bold text-white">
                      {(result.confidence * 100).toFixed(1)}%
                    </div>
                  </div>
                </motion.div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                {/* Deposits Stat Card */}
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0 }}
                  className="relative overflow-hidden bg-gradient-to-br from-blue-50 to-blue-100/50 dark:from-blue-900/30 dark:to-blue-900/10 border-2 border-blue-200 dark:border-blue-800/50 rounded-xl p-5 hover:shadow-xl transition-shadow duration-300"
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="text-sm font-semibold text-blue-600 dark:text-blue-400 mb-2">
                        {t('privacyDemixing.results.depositsFound')}
                      </div>
                      <div className="text-4xl font-bold text-blue-900 dark:text-blue-100">
                        {result.deposits.length}
                      </div>
                    </div>
                    <div className="p-3 bg-blue-200 dark:bg-blue-800/50 rounded-lg">
                      <TrendingDown className="w-6 h-6 text-blue-600 dark:text-blue-400" />
                    </div>
                  </div>
                </motion.div>

                {/* Withdrawals Stat Card */}
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.1 }}
                  className="relative overflow-hidden bg-gradient-to-br from-purple-50 to-purple-100/50 dark:from-purple-900/30 dark:to-purple-900/10 border-2 border-purple-200 dark:border-purple-800/50 rounded-xl p-5 hover:shadow-xl transition-shadow duration-300"
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="text-sm font-semibold text-purple-600 dark:text-purple-400 mb-2">
                        {t('privacyDemixing.results.likelyWithdrawals')}
                      </div>
                      <div className="text-4xl font-bold text-purple-900 dark:text-purple-100">
                        {result.likely_withdrawals.length}
                      </div>
                    </div>
                    <div className="p-3 bg-purple-200 dark:bg-purple-800/50 rounded-lg">
                      <CheckCircle className="w-6 h-6 text-purple-600 dark:text-purple-400" />
                    </div>
                  </div>
                </motion.div>

                {/* Addresses Stat Card */}
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.2 }}
                  className="relative overflow-hidden bg-gradient-to-br from-green-50 to-green-100/50 dark:from-green-900/30 dark:to-green-900/10 border-2 border-green-200 dark:border-green-800/50 rounded-xl p-5 hover:shadow-xl transition-shadow duration-300"
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="text-sm font-semibold text-green-600 dark:text-green-400 mb-2">
                        {t('privacyDemixing.results.uniqueAddresses')}
                      </div>
                      <div className="text-4xl font-bold text-green-900 dark:text-green-100">
                        {Object.keys(result.probability_scores).length}
                      </div>
                    </div>
                    <div className="p-3 bg-green-200 dark:bg-green-800/50 rounded-lg">
                      <Network className="w-6 h-6 text-green-600 dark:text-green-400" />
                    </div>
                  </div>
                </motion.div>
              </div>
            </motion.div>

          {/* Premium Deposits Section */}
          {result.deposits.length > 0 && (
            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="bg-white/80 dark:bg-slate-900/80 backdrop-blur-xl rounded-2xl shadow-xl border border-gray-200/50 dark:border-slate-700/50 p-6"
            >
              <h3 className="text-xl font-bold mb-4 flex items-center gap-2 text-gray-900 dark:text-white">
                <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
                  <TrendingDown className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                </div>
                {t('privacyDemixing.results.deposits')}
              </h3>
              <div className="space-y-3">
                {result.deposits.map((deposit, idx) => (
                  <motion.div 
                    key={idx}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: idx * 0.05 }}
                    className="bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-900/20 dark:to-purple-900/20 border-2 border-blue-200 dark:border-blue-800/50 rounded-xl p-4 hover:shadow-lg transition-all"
                  >
                    <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 mb-2">
                      <div className="flex items-center gap-3">
                        <div className="px-4 py-2 bg-gradient-to-r from-purple-500 to-blue-500 rounded-lg shadow-md">
                          <span className="text-lg font-bold text-white">
                            {deposit.amount} {chain.toUpperCase()}
                          </span>
                        </div>
                        <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
                          {t('privacyDemixing.results.pool')}: {deposit.denomination}
                        </span>
                      </div>
                      <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400">
                        <Clock className="w-4 h-4" />
                        {new Date(deposit.timestamp).toLocaleString()}
                      </div>
                    </div>
                    <div className="flex items-center gap-2 text-sm">
                      <span className="font-medium text-gray-600 dark:text-gray-400">TX:</span>
                      <a
                        href={`https://etherscan.io/tx/${deposit.tx_hash}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-1 font-mono"
                      >
                        {deposit.tx_hash.slice(0, 10)}...
                        <ExternalLink className="w-3 h-3" />
                      </a>
                    </div>
                  </motion.div>
                ))}
              </div>
            </motion.div>
          )}

          {/* Premium Withdrawals Section */}
          {result.likely_withdrawals.length > 0 && (
            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 }}
              className="bg-white/80 dark:bg-slate-900/80 backdrop-blur-xl rounded-2xl shadow-xl border border-gray-200/50 dark:border-slate-700/50 p-6"
            >
              <h3 className="text-xl font-bold mb-4 flex items-center gap-2 text-gray-900 dark:text-white">
                <div className="p-2 bg-green-100 dark:bg-green-900/30 rounded-lg">
                  <CheckCircle className="w-5 h-5 text-green-600 dark:text-green-400" />
                </div>
                {t('privacyDemixing.results.withdrawals')}
              </h3>
              <div className="space-y-3">
                {result.likely_withdrawals
                  .sort((a, b) => b.probability - a.probability)
                  .slice(0, 10)
                  .map((withdrawal, idx) => (
                    <motion.div 
                      key={idx}
                      initial={{ opacity: 0, scale: 0.95 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ delay: idx * 0.05 }}
                      className="bg-gradient-to-r from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20 border-2 border-green-200 dark:border-green-800/50 rounded-xl p-5 hover:shadow-xl transition-all"
                    >
                      <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4 mb-3">
                        <div className="flex items-center gap-4 flex-1">
                          <motion.div 
                            whileHover={{ scale: 1.1, rotate: 5 }}
                            className="w-20 h-20 bg-gradient-to-br from-purple-500 via-purple-600 to-blue-600 rounded-xl flex items-center justify-center shadow-lg flex-shrink-0"
                          >
                            <span className="text-2xl font-bold text-white">
                              {(withdrawal.probability * 100).toFixed(0)}%
                            </span>
                          </motion.div>
                          <div className="flex-1 min-w-0">
                            <div className="font-mono text-sm sm:text-base font-semibold text-gray-900 dark:text-gray-100 break-all">
                              {withdrawal.withdrawal_address}
                            </div>
                            <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400 mt-2">
                              <Clock className="w-4 h-4 flex-shrink-0" />
                              <span>{new Date(withdrawal.timestamp).toLocaleString()}</span>
                            </div>
                          </div>
                        </div>
                        <a
                          href={`https://etherscan.io/tx/${withdrawal.tx_hash}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600 text-white rounded-lg font-semibold transition-colors shadow-md flex-shrink-0"
                        >
                          {t('privacyDemixing.results.viewTx')}
                          <ExternalLink className="w-4 h-4" />
                        </a>
                      </div>
                      {/* Premium Probability Bar */}
                      <div className="relative w-full h-3 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                        <motion.div
                          initial={{ width: 0 }}
                          animate={{ width: `${withdrawal.probability * 100}%` }}
                          transition={{ duration: 0.8, delay: idx * 0.1 }}
                          className="absolute inset-y-0 left-0 bg-gradient-to-r from-purple-600 via-purple-500 to-blue-500 rounded-full shadow-inner"
                        />
                      </div>
                    </motion.div>
                  ))}
              </div>
            </motion.div>
          )}

          {/* Premium Demixing Paths Section */}
          {result.demixing_path.length > 0 && (
            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5 }}
              className="bg-white/80 dark:bg-slate-900/80 backdrop-blur-xl rounded-2xl shadow-xl border border-gray-200/50 dark:border-slate-700/50 p-6"
            >
              <h3 className="text-xl font-bold mb-4 flex items-center gap-2 text-gray-900 dark:text-white">
                <div className="p-2 bg-purple-100 dark:bg-purple-900/30 rounded-lg">
                  <Network className="w-5 h-5 text-purple-600 dark:text-purple-400" />
                </div>
                {t('privacyDemixing.results.paths')}
              </h3>
              <div className="space-y-4">
                {result.demixing_path.slice(0, 5).map((path, idx) => (
                  <motion.div 
                    key={idx}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: idx * 0.1 }}
                    className="bg-gradient-to-r from-purple-50 to-blue-50 dark:from-purple-900/20 dark:to-blue-900/20 border-2 border-purple-200 dark:border-purple-800/50 rounded-xl p-5 hover:shadow-lg transition-all"
                  >
                    <div className="flex flex-wrap items-center gap-2 mb-4">
                      <span className="inline-flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-purple-500 to-purple-600 text-white rounded-lg text-sm font-bold shadow-md">
                        <Target className="w-4 h-4" />
                        {(path.probability * 100).toFixed(0)}% {t('privacyDemixing.results.match')}
                      </span>
                      <ArrowRight className="w-5 h-5 text-gray-400 dark:text-gray-500" />
                      <span className="inline-flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-green-500 to-emerald-500 text-white rounded-lg text-sm font-bold shadow-md">
                        <CheckCircle className="w-4 h-4" />
                        {path.end_label}
                      </span>
                    </div>
                    <div className="flex items-center gap-2 overflow-x-auto pb-2 scrollbar-thin scrollbar-thumb-gray-300 dark:scrollbar-thumb-gray-600">
                      {path.path.map((addr, addrIdx) => (
                        <React.Fragment key={addrIdx}>
                          <motion.div 
                            whileHover={{ scale: 1.05 }}
                            className="px-4 py-2.5 bg-white dark:bg-slate-800 border-2 border-gray-200 dark:border-slate-600 rounded-lg font-mono text-xs font-semibold text-gray-900 dark:text-gray-100 whitespace-nowrap shadow-sm"
                          >
                            {addr.slice(0, 6)}...{addr.slice(-4)}
                          </motion.div>
                          {addrIdx < path.path.length - 1 && (
                            <ArrowRight className="w-5 h-5 text-purple-500 dark:text-purple-400 flex-shrink-0" />
                          )}
                        </React.Fragment>
                      ))}
                    </div>
                  </motion.div>
                ))}
              </div>
            </motion.div>
          )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

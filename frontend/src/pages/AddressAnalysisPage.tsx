import { useState, useMemo } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useQuery } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { 
  Wallet, TrendingUp, Activity, Clock, Download, ExternalLink, 
  Save, Network, AlertTriangle, Tag, Copy, Check, ArrowRight,
  Shield, Globe, Calendar, DollarSign
} from 'lucide-react'
import toast from 'react-hot-toast'
import api from '@/lib/api'
import { RiskCopilot } from '@/components/RiskCopilot'
import { formatAddress, copyToClipboard } from '@/lib/utils'

interface AddressInfo {
  address: string
  chain: string
  balance?: number
  tx_count?: number
  first_seen?: string
  last_seen?: string
  labels?: string[]
  risk_categories?: string[]
}

interface Transaction {
  tx_hash: string
  from_address: string
  to_address: string
  value: number
  timestamp: string
  block_number: number
}

export default function AddressAnalysisPage() {
  const { address } = useParams<{ address: string }>()
  const { t } = useTranslation()
  const navigate = useNavigate()
  const [copied, setCopied] = useState(false)
  const [chain] = useState('ethereum') // TODO: Auto-detect from address format
  
  // Fetch address info
  const { data: addressInfo, isLoading: infoLoading } = useQuery({
    queryKey: ['address-info', chain, address],
    queryFn: async () => {
      // Mock data - in production würde das vom Backend kommen
      return {
        address: address || '',
        chain: chain,
        balance: 15.234,
        tx_count: 1247,
        first_seen: '2021-03-15T10:30:00Z',
        last_seen: '2024-10-19T15:45:00Z',
        labels: ['Exchange', 'High Volume'],
        risk_categories: []
      } as AddressInfo
    },
    enabled: !!address
  })

  // Fetch recent transactions
  const { data: transactions, isLoading: txLoading } = useQuery({
    queryKey: ['address-transactions', chain, address],
    queryFn: async () => {
      // Mock data
      return Array.from({ length: 10 }, (_, i) => ({
        tx_hash: `0x${Math.random().toString(16).slice(2, 66)}`,
        from_address: i % 2 === 0 ? (address || '') : `0x${Math.random().toString(16).slice(2, 42)}`,
        to_address: i % 2 === 0 ? `0x${Math.random().toString(16).slice(2, 42)}` : (address || ''),
        value: Math.random() * 10,
        timestamp: new Date(Date.now() - i * 3600000).toISOString(),
        block_number: 18000000 + i
      })) as Transaction[]
    },
    enabled: !!address
  })

  const handleCopy = async () => {
    if (address) {
      await copyToClipboard(address)
      setCopied(true)
      toast.success(t('common.copied', 'Kopiert!'))
      setTimeout(() => setCopied(false), 2000)
    }
  }

  const handleCreateCase = async () => {
    try {
      const caseData = {
        title: `Investigation: ${formatAddress(address || '')}`,
        description: `Address analysis for ${address} on ${chain}\n\nBalance: ${addressInfo?.balance || 0} ETH\nTransactions: ${addressInfo?.tx_count || 0}\nLabels: ${(addressInfo?.labels || []).join(', ')}`,
        priority: 'medium',
        tags: ['address-analysis', chain, 'automated'],
        category: 'investigation'
      }
      
      const response = await api.post('/api/v1/cases', caseData)
      toast.success(t('address.case_created', 'Case erstellt'))
      navigate(`/en/cases/${response.data.case_id}`)
    } catch (error) {
      toast.error(t('address.case_error', 'Fehler beim Erstellen'))
    }
  }

  const openInInvestigator = () => {
    navigate(`/en/investigator?address=${address}`)
  }

  const explorerUrl = useMemo(() => {
    const explorers: Record<string, string> = {
      ethereum: `https://etherscan.io/address/${address}`,
      polygon: `https://polygonscan.com/address/${address}`,
      arbitrum: `https://arbiscan.io/address/${address}`,
    }
    return explorers[chain] || explorers.ethereum
  }, [chain, address])

  if (!address) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-slate-950 p-6 flex items-center justify-center">
        <div className="text-center">
          <Wallet className="h-16 w-16 text-slate-400 mx-auto mb-4" />
          <p className="text-slate-600 dark:text-slate-400">{t('address.no_address', 'Keine Adresse angegeben')}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 p-6 space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-3xl font-bold text-slate-900 dark:text-white flex items-center gap-3">
              <div className="p-3 bg-gradient-to-br from-primary-500 to-purple-600 rounded-xl shadow-lg">
                <Wallet className="h-7 w-7 text-white" />
              </div>
              {t('address.title', 'Address Analysis')}
            </h1>
            <div className="mt-2 flex items-center gap-2">
              <code className="text-sm bg-slate-100 dark:bg-slate-800 px-3 py-1.5 rounded-lg font-mono text-slate-700 dark:text-slate-300">
                {address}
              </code>
              <button
                onClick={handleCopy}
                className="p-2 hover:bg-slate-200 dark:hover:bg-slate-700 rounded-lg transition-colors"
                title={t('common.copy', 'Kopieren')}
              >
                {copied ? (
                  <Check className="h-4 w-4 text-emerald-600" />
                ) : (
                  <Copy className="h-4 w-4 text-slate-600 dark:text-slate-400" />
                )}
              </button>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleCreateCase}
              className="px-4 py-2 bg-gradient-to-r from-primary-600 to-purple-600 hover:from-primary-700 hover:to-purple-700 text-white rounded-lg font-medium shadow-md hover:shadow-lg transition-all flex items-center gap-2"
            >
              <Save className="h-4 w-4" />
              {t('address.create_case', 'Case erstellen')}
            </button>
            <button
              onClick={openInInvestigator}
              className="px-4 py-2 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 rounded-lg font-medium transition-colors flex items-center gap-2"
            >
              <Network className="h-4 w-4" />
              {t('address.open_investigator', 'Graph öffnen')}
            </button>
          </div>
        </div>
      </motion.div>

      {/* Risk Score Card */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
      >
        <RiskCopilot 
          chain={chain} 
          address={address} 
          variant="full"
          showDetails={true}
        />
      </motion.div>

      {/* Stats Grid */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4"
      >
        {/* Balance */}
        <div className="bg-white dark:bg-slate-900 rounded-xl p-6 border border-slate-200 dark:border-slate-800">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 bg-emerald-100 dark:bg-emerald-900/30 rounded-lg">
              <DollarSign className="h-5 w-5 text-emerald-600 dark:text-emerald-400" />
            </div>
            <span className="text-sm text-slate-600 dark:text-slate-400">{t('address.balance', 'Balance')}</span>
          </div>
          <p className="text-2xl font-bold text-slate-900 dark:text-white">
            {addressInfo?.balance?.toFixed(4) || '0'} ETH
          </p>
        </div>

        {/* Transactions */}
        <div className="bg-white dark:bg-slate-900 rounded-xl p-6 border border-slate-200 dark:border-slate-800">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
              <Activity className="h-5 w-5 text-blue-600 dark:text-blue-400" />
            </div>
            <span className="text-sm text-slate-600 dark:text-slate-400">{t('address.transactions', 'Transactions')}</span>
          </div>
          <p className="text-2xl font-bold text-slate-900 dark:text-white">
            {addressInfo?.tx_count?.toLocaleString() || '0'}
          </p>
        </div>

        {/* First Seen */}
        <div className="bg-white dark:bg-slate-900 rounded-xl p-6 border border-slate-200 dark:border-slate-800">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 bg-purple-100 dark:bg-purple-900/30 rounded-lg">
              <Calendar className="h-5 w-5 text-purple-600 dark:text-purple-400" />
            </div>
            <span className="text-sm text-slate-600 dark:text-slate-400">{t('address.first_seen', 'First Seen')}</span>
          </div>
          <p className="text-sm font-medium text-slate-900 dark:text-white">
            {addressInfo?.first_seen ? new Date(addressInfo.first_seen).toLocaleDateString() : 'N/A'}
          </p>
        </div>

        {/* Last Seen */}
        <div className="bg-white dark:bg-slate-900 rounded-xl p-6 border border-slate-200 dark:border-slate-800">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 bg-orange-100 dark:bg-orange-900/30 rounded-lg">
              <Clock className="h-5 w-5 text-orange-600 dark:text-orange-400" />
            </div>
            <span className="text-sm text-slate-600 dark:text-slate-400">{t('address.last_seen', 'Last Seen')}</span>
          </div>
          <p className="text-sm font-medium text-slate-900 dark:text-white">
            {addressInfo?.last_seen ? new Date(addressInfo.last_seen).toLocaleDateString() : 'N/A'}
          </p>
        </div>
      </motion.div>

      {/* Labels */}
      {addressInfo?.labels && addressInfo.labels.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="bg-white dark:bg-slate-900 rounded-xl p-6 border border-slate-200 dark:border-slate-800"
        >
          <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4 flex items-center gap-2">
            <Tag className="h-5 w-5 text-primary-600 dark:text-primary-400" />
            {t('address.labels', 'Entity Labels')}
          </h3>
          <div className="flex flex-wrap gap-2">
            {addressInfo.labels.map((label, idx) => (
              <span
                key={idx}
                className="px-3 py-1 bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 rounded-lg text-sm font-medium"
              >
                {label}
              </span>
            ))}
          </div>
        </motion.div>
      )}

      {/* Recent Transactions */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 overflow-hidden"
      >
        <div className="p-6 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
          <h3 className="text-lg font-semibold text-slate-900 dark:text-white flex items-center gap-2">
            <Activity className="h-5 w-5 text-primary-600 dark:text-primary-400" />
            {t('address.recent_tx', 'Recent Transactions')}
          </h3>
          <a
            href={explorerUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm text-primary-600 dark:text-primary-400 hover:underline flex items-center gap-1"
          >
            <Globe className="h-4 w-4" />
            {t('address.view_explorer', 'View on Explorer')}
            <ExternalLink className="h-3 w-3" />
          </a>
        </div>

        {txLoading ? (
          <div className="p-8 text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto"></div>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 dark:divide-slate-800">
              <thead className="bg-slate-50 dark:bg-slate-800">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-700 dark:text-slate-300 uppercase tracking-wider">
                    {t('address.tx_hash', 'TX Hash')}
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-700 dark:text-slate-300 uppercase tracking-wider">
                    {t('address.from', 'From')}
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-700 dark:text-slate-300 uppercase tracking-wider">
                    {t('address.to', 'To')}
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-700 dark:text-slate-300 uppercase tracking-wider">
                    {t('address.value', 'Value')}
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-700 dark:text-slate-300 uppercase tracking-wider">
                    {t('address.time', 'Time')}
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white dark:bg-slate-900 divide-y divide-slate-200 dark:divide-slate-800">
                {(transactions || []).map((tx, idx) => (
                  <tr key={idx} className="hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-primary-600 dark:text-primary-400">
                      {formatAddress(tx.tx_hash)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-slate-600 dark:text-slate-400">
                      {formatAddress(tx.from_address)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-slate-600 dark:text-slate-400">
                      {formatAddress(tx.to_address)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-slate-900 dark:text-white">
                      {tx.value.toFixed(4)} ETH
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-600 dark:text-slate-400">
                      {new Date(tx.timestamp).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </motion.div>
    </div>
  )
}

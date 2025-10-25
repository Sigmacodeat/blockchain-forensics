/**
 * Bitcoin Investigation Dashboard - Premium Criminal Case Analysis
 * 
 * Features:
 * - Multi-Address Investigation
 * - 8+ Years Historical Analysis
 * - UTXO Clustering
 * - Mixer Detection & Demixing
 * - Flow Analysis (Exit Points, Dormant Funds)
 * - AI-Powered Insights
 * - Court-Admissible Evidence Reports
 */

import React, { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { 
  Search, Plus, X, Calendar, Download, FileText, 
  AlertCircle, TrendingUp, DollarSign, MapPin, Shield,
  Activity, Zap, Eye, Target, Filter
} from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { toast } from 'react-hot-toast'

interface InvestigationRequest {
  addresses: string[]
  startDate: string
  endDate: string
  includeClustering: boolean
  includeMixerAnalysis: boolean
  includeFlowAnalysis: boolean
  caseId?: string
}

interface InvestigationResult {
  investigation_id: string
  status: string
  execution_time_seconds: number
  transactions: {
    total_count: number
    total_volume_btc: number
    unique_addresses: number
  }
  clustering: {
    total_clusters: number
    clustered_addresses: number
  }
  mixer_analysis: {
    mixer_interactions: number
    mixers_detected: string[]
  }
  flow_analysis: {
    exit_points: Array<{
      address: string
      exit_type: string
      total_outflow_btc: number
      labels: string[]
    }>
    dormant_funds: Array<{
      address: string
      balance_btc: number
      dormant_days: number
    }>
    total_exit_volume_btc: number
    total_dormant_btc: number
  }
  summary: string
  recommendations: string[]
}

export default function BitcoinInvestigation() {
  const { t } = useTranslation()
  
  // State
  const [addresses, setAddresses] = useState<string[]>([''])
  const [startDate, setStartDate] = useState<string>(
    new Date(Date.now() - 8 * 365 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]
  )
  const [endDate, setEndDate] = useState<string>(new Date().toISOString().split('T')[0])
  const [caseId, setCaseId] = useState<string>('')
  const [includeClustering, setIncludeClustering] = useState<boolean>(true)
  const [includeMixerAnalysis, setIncludeMixerAnalysis] = useState<boolean>(true)
  const [includeFlowAnalysis, setIncludeFlowAnalysis] = useState<boolean>(true)
  
  const [loading, setLoading] = useState<boolean>(false)
  const [result, setResult] = useState<InvestigationResult | null>(null)
  const [activeTab, setActiveTab] = useState<'overview' | 'clustering' | 'mixer' | 'flow' | 'timeline'>('overview')

  // Add/Remove Address
  const addAddress = () => {
    setAddresses([...addresses, ''])
  }

  const removeAddress = (index: number) => {
    setAddresses(addresses.filter((_, i) => i !== index))
  }

  const updateAddress = (index: number, value: string) => {
    const newAddresses = [...addresses]
    newAddresses[index] = value
    setAddresses(newAddresses)
  }

  // Submit Investigation
  const handleInvestigate = async () => {
    // Validate
    const validAddresses = addresses.filter(a => a.trim().length > 0)
    if (validAddresses.length === 0) {
      toast.error('Bitte mindestens eine Bitcoin-Adresse eingeben')
      return
    }

    setLoading(true)
    
    try {
      const response = await fetch('/api/v1/bitcoin-investigation/investigate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          addresses: validAddresses,
          start_date: startDate,
          end_date: endDate,
          include_clustering: includeClustering,
          include_mixer_analysis: includeMixerAnalysis,
          include_flow_analysis: includeFlowAnalysis,
          case_id: caseId || undefined
        })
      })

      if (!response.ok) {
        throw new Error('Investigation failed')
      }

      const data = await response.json()
      setResult(data)
      toast.success('Investigation completed!')
      
    } catch (error) {
      console.error('Investigation error:', error)
      toast.error('Investigation fehlgeschlagen')
    } finally {
      setLoading(false)
    }
  }

  // Download Report
  const downloadReport = async (format: 'pdf' | 'json' | 'csv') => {
    if (!result) return

    try {
      const response = await fetch(
        `/api/v1/bitcoin-investigation/investigations/${result.investigation_id}/report.${format}`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        }
      )

      if (!response.ok) throw new Error('Download failed')

      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `investigation-${result.investigation_id}.${format}`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)

      toast.success(`Report downloaded as ${format.toUpperCase()}`)
    } catch (error) {
      toast.error('Download fehlgeschlagen')
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-purple-50 dark:from-slate-950 dark:via-slate-900 dark:to-slate-950 p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white/80 dark:bg-slate-800/80 backdrop-blur-xl rounded-2xl p-8 shadow-xl border border-slate-200 dark:border-slate-700"
        >
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                Bitcoin Criminal Investigation
              </h1>
              <p className="text-slate-600 dark:text-slate-400 mt-2">
                Multi-Address Analysis über 8+ Jahre mit KI-gestützter Analyse
              </p>
            </div>
            <Shield className="w-16 h-16 text-blue-500 opacity-20" />
          </div>
        </motion.div>

        {/* Investigation Form */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white/80 dark:bg-slate-800/80 backdrop-blur-xl rounded-2xl p-8 shadow-xl border border-slate-200 dark:border-slate-700"
        >
          <h2 className="text-2xl font-bold mb-6 flex items-center gap-2">
            <Target className="w-6 h-6 text-blue-500" />
            Investigation Setup
          </h2>

          {/* Addresses */}
          <div className="space-y-4 mb-6">
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
              Bitcoin Addresses
            </label>
            {addresses.map((address, index) => (
              <div key={index} className="flex gap-2">
                <input
                  type="text"
                  value={address}
                  onChange={(e) => updateAddress(index, e.target.value)}
                  placeholder={`Bitcoin Address ${index + 1} (bc1q..., 1..., 3...)`}
                  className="flex-1 px-4 py-3 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 focus:ring-2 focus:ring-blue-500"
                />
                {addresses.length > 1 && (
                  <button
                    onClick={() => removeAddress(index)}
                    className="px-4 py-3 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors"
                  >
                    <X className="w-5 h-5" />
                  </button>
                )}
              </div>
            ))}
            <button
              onClick={addAddress}
              className="w-full py-3 border-2 border-dashed border-slate-300 dark:border-slate-600 rounded-lg text-slate-600 dark:text-slate-400 hover:border-blue-500 hover:text-blue-500 transition-colors flex items-center justify-center gap-2"
            >
              <Plus className="w-5 h-5" />
              Add Address
            </button>
          </div>

          {/* Date Range */}
          <div className="grid grid-cols-2 gap-4 mb-6">
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                Start Date
              </label>
              <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="w-full px-4 py-3 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                End Date
              </label>
              <input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="w-full px-4 py-3 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900"
              />
            </div>
          </div>

          {/* Case ID */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
              Case ID (Optional)
            </label>
            <input
              type="text"
              value={caseId}
              onChange={(e) => setCaseId(e.target.value)}
              placeholder="e.g., ransomware-2024-001"
              className="w-full px-4 py-3 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900"
            />
          </div>

          {/* Analysis Options */}
          <div className="space-y-3 mb-6">
            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={includeClustering}
                onChange={(e) => setIncludeClustering(e.target.checked)}
                className="w-5 h-5 rounded text-blue-500"
              />
              <span className="text-slate-700 dark:text-slate-300">
                UTXO Clustering (15+ Heuristics)
              </span>
            </label>
            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={includeMixerAnalysis}
                onChange={(e) => setIncludeMixerAnalysis(e.target.checked)}
                className="w-5 h-5 rounded text-blue-500"
              />
              <span className="text-slate-700 dark:text-slate-300">
                Mixer Detection & Demixing
              </span>
            </label>
            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={includeFlowAnalysis}
                onChange={(e) => setIncludeFlowAnalysis(e.target.checked)}
                className="w-5 h-5 rounded text-blue-500"
              />
              <span className="text-slate-700 dark:text-slate-300">
                Flow Analysis (Exit Points, Dormant Funds)
              </span>
            </label>
          </div>

          {/* Submit Button */}
          <button
            onClick={handleInvestigate}
            disabled={loading}
            className="w-full py-4 bg-gradient-to-r from-blue-500 to-purple-500 text-white rounded-lg font-semibold hover:from-blue-600 hover:to-purple-600 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent" />
                Analyzing...
              </>
            ) : (
              <>
                <Search className="w-5 h-5" />
                Start Investigation
              </>
            )}
          </button>
        </motion.div>

        {/* Results */}
        <AnimatePresence>
          {result && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="space-y-6"
            >
              {/* Summary Cards */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl p-6 text-white shadow-lg">
                  <Activity className="w-8 h-8 mb-2 opacity-80" />
                  <div className="text-3xl font-bold">{result.transactions.total_count}</div>
                  <div className="text-sm opacity-90">Transactions</div>
                </div>
                <div className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-xl p-6 text-white shadow-lg">
                  <TrendingUp className="w-8 h-8 mb-2 opacity-80" />
                  <div className="text-3xl font-bold">{result.clustering.total_clusters}</div>
                  <div className="text-sm opacity-90">Wallet Clusters</div>
                </div>
                <div className="bg-gradient-to-br from-orange-500 to-orange-600 rounded-xl p-6 text-white shadow-lg">
                  <AlertCircle className="w-8 h-8 mb-2 opacity-80" />
                  <div className="text-3xl font-bold">{result.mixer_analysis.mixer_interactions}</div>
                  <div className="text-sm opacity-90">Mixer Interactions</div>
                </div>
                <div className="bg-gradient-to-br from-green-500 to-green-600 rounded-xl p-6 text-white shadow-lg">
                  <DollarSign className="w-8 h-8 mb-2 opacity-80" />
                  <div className="text-3xl font-bold">{result.flow_analysis.total_dormant_btc.toFixed(2)}</div>
                  <div className="text-sm opacity-90">Dormant BTC</div>
                </div>
              </div>

              {/* Download Reports */}
              <div className="bg-white/80 dark:bg-slate-800/80 backdrop-blur-xl rounded-2xl p-6 shadow-xl border border-slate-200 dark:border-slate-700">
                <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
                  <Download className="w-5 h-5 text-blue-500" />
                  Evidence Reports
                </h3>
                <div className="flex gap-3">
                  <button
                    onClick={() => downloadReport('pdf')}
                    className="px-6 py-3 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors flex items-center gap-2"
                  >
                    <FileText className="w-5 h-5" />
                    PDF Report
                  </button>
                  <button
                    onClick={() => downloadReport('json')}
                    className="px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors flex items-center gap-2"
                  >
                    <FileText className="w-5 h-5" />
                    JSON Evidence
                  </button>
                  <button
                    onClick={() => downloadReport('csv')}
                    className="px-6 py-3 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors flex items-center gap-2"
                  >
                    <FileText className="w-5 h-5" />
                    CSV Export
                  </button>
                </div>
              </div>

              {/* Summary & Recommendations */}
              <div className="bg-white/80 dark:bg-slate-800/80 backdrop-blur-xl rounded-2xl p-6 shadow-xl border border-slate-200 dark:border-slate-700">
                <h3 className="text-xl font-bold mb-4">Summary</h3>
                <p className="text-slate-700 dark:text-slate-300 mb-6">{result.summary}</p>
                
                <h3 className="text-xl font-bold mb-4">Recommendations</h3>
                <ul className="space-y-2">
                  {result.recommendations.map((rec, index) => (
                    <li key={index} className="flex items-start gap-2 text-slate-700 dark:text-slate-300">
                      <Zap className="w-5 h-5 text-yellow-500 flex-shrink-0 mt-0.5" />
                      <span>{rec}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Exit Points */}
              {result.flow_analysis.exit_points.length > 0 && (
                <div className="bg-white/80 dark:bg-slate-800/80 backdrop-blur-xl rounded-2xl p-6 shadow-xl border border-slate-200 dark:border-slate-700">
                  <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
                    <MapPin className="w-5 h-5 text-blue-500" />
                    Exit Points ({result.flow_analysis.exit_points.length})
                  </h3>
                  <div className="space-y-3">
                    {result.flow_analysis.exit_points.map((exit, index) => (
                      <div key={index} className="p-4 bg-slate-50 dark:bg-slate-900 rounded-lg">
                        <div className="flex justify-between items-start mb-2">
                          <code className="text-sm font-mono">{exit.address}</code>
                          <span className="px-3 py-1 bg-blue-500 text-white text-xs rounded-full">
                            {exit.exit_type}
                          </span>
                        </div>
                        <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                          {exit.total_outflow_btc.toFixed(4)} BTC
                        </div>
                        <div className="flex gap-2 mt-2">
                          {exit.labels.map((label, i) => (
                            <span key={i} className="px-2 py-1 bg-purple-100 dark:bg-purple-900 text-purple-700 dark:text-purple-300 text-xs rounded">
                              {label}
                            </span>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  )
}

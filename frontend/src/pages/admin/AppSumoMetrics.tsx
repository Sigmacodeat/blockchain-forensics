import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import axios from 'axios'
import { 
  DollarSign, 
  Users, 
  TrendingUp, 
  Download,
  Code,
  CheckCircle,
  Clock,
  AlertCircle
} from 'lucide-react'
import { motion } from 'framer-motion'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const PRODUCT_INFO = {
  chatbot: { name: 'AI ChatBot Pro', icon: '💬', color: 'purple' },
  firewall: { name: 'Web3 Wallet Guardian', icon: '🛡️', color: 'green' },
  inspector: { name: 'Crypto Inspector', icon: '🔍', color: 'blue' },
  commander: { name: 'AI Commander', icon: '🎯', color: 'orange' }
}

export default function AppSumoMetrics() {
  const [showCodeGenerator, setShowCodeGenerator] = useState(false)
  const [genProduct, setGenProduct] = useState('chatbot')
  const [genTier, setGenTier] = useState(1)
  const [genCount, setGenCount] = useState(100)

  // Fetch metrics
  const { data: metrics, isLoading: metricsLoading } = useQuery({
    queryKey: ['appsumo-metrics'],
    queryFn: async () => {
      const token = localStorage.getItem('token')
      const res = await axios.get(`${API_URL}/api/v1/appsumo/admin/metrics`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      return res.data
    },
    refetchInterval: 60000 // Refresh every minute
  })

  // Fetch stats
  const { data: stats } = useQuery({
    queryKey: ['appsumo-stats'],
    queryFn: async () => {
      const token = localStorage.getItem('token')
      const res = await axios.get(`${API_URL}/api/v1/appsumo/admin/stats`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      return res.data
    }
  })

  // Fetch recent redemptions
  const { data: recent } = useQuery({
    queryKey: ['appsumo-recent'],
    queryFn: async () => {
      const token = localStorage.getItem('token')
      const res = await axios.get(
        `${API_URL}/api/v1/appsumo/admin/recent-redemptions?limit=10`,
        { headers: { Authorization: `Bearer ${token}` } }
      )
      return res.data
    }
  })

  // Generate codes
  const handleGenerateCodes = async () => {
    try {
      const token = localStorage.getItem('token')
      const res = await axios.post(
        `${API_URL}/api/v1/appsumo/admin/generate-codes`,
        null,
        {
          params: { product: genProduct, tier: genTier, count: genCount },
          headers: { Authorization: `Bearer ${token}` }
        }
      )
      
      // Download as CSV
      const codes = res.data.codes
      const csv = `Code,Product,Tier\n${codes.map((c: string) => `${c},${genProduct},${genTier}`).join('\n')}`
      const blob = new Blob([csv], { type: 'text/csv' })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `appsumo_${genProduct}_tier${genTier}_${genCount}.csv`
      a.click()
      
      alert(`✅ ${codes.length} codes generated and downloaded!`)
      setShowCodeGenerator(false)
    } catch (err) {
      alert('❌ Failed to generate codes')
    }
  }

  if (metricsLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    )
  }

  return (
    <div className="p-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">AppSumo Metrics</h1>
        <p className="text-slate-400">Monitor code redemptions, revenue, and performance</p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-slate-800 p-6 rounded-lg border border-slate-700"
        >
          <div className="flex items-center justify-between mb-4">
            <DollarSign className="w-8 h-8 text-green-400" />
            <span className="text-xs text-slate-400">Total Revenue</span>
          </div>
          <div className="text-3xl font-bold">
            ${((metrics?.total_revenue_cents || 0) / 100).toLocaleString()}
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Net: ${((metrics?.total_revenue_cents || 0) * 0.30 / 100).toLocaleString()}
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-slate-800 p-6 rounded-lg border border-slate-700"
        >
          <div className="flex items-center justify-between mb-4">
            <CheckCircle className="w-8 h-8 text-blue-400" />
            <span className="text-xs text-slate-400">Total Redemptions</span>
          </div>
          <div className="text-3xl font-bold">{metrics?.total_redemptions || 0}</div>
          <p className="text-sm text-slate-400 mt-1">
            {stats?.codes_redeemed || 0} codes used
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-slate-800 p-6 rounded-lg border border-slate-700"
        >
          <div className="flex items-center justify-between mb-4">
            <Users className="w-8 h-8 text-purple-400" />
            <span className="text-xs text-slate-400">Active Users</span>
          </div>
          <div className="text-3xl font-bold">{metrics?.total_users || 0}</div>
          <p className="text-sm text-slate-400 mt-1">
            {stats?.active_products || 0} products active
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="bg-slate-800 p-6 rounded-lg border border-slate-700"
        >
          <div className="flex items-center justify-between mb-4">
            <TrendingUp className="w-8 h-8 text-orange-400" />
            <span className="text-xs text-slate-400">Conversion Rate</span>
          </div>
          <div className="text-3xl font-bold">{metrics?.conversion_rate || 0}%</div>
          <p className="text-sm text-slate-400 mt-1">
            {stats?.codes_remaining || 0} codes remaining
          </p>
        </motion.div>
      </div>

      {/* Product Breakdown */}
      <div className="bg-slate-800 p-6 rounded-lg border border-slate-700 mb-8">
        <h2 className="text-xl font-bold mb-4">Product Breakdown</h2>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-700">
                <th className="text-left py-3 px-4">Product</th>
                <th className="text-right py-3 px-4">Tier 1</th>
                <th className="text-right py-3 px-4">Tier 2</th>
                <th className="text-right py-3 px-4">Tier 3</th>
                <th className="text-right py-3 px-4">Total</th>
                <th className="text-right py-3 px-4">Revenue</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(metrics?.product_breakdown || {}).map(([product, data]: [string, any]) => (
                <tr key={product} className="border-b border-slate-700/50">
                  <td className="py-3 px-4">
                    <div className="flex items-center gap-2">
                      <span className="text-2xl">
                        {PRODUCT_INFO[product as keyof typeof PRODUCT_INFO]?.icon}
                      </span>
                      <span className="font-medium">
                        {PRODUCT_INFO[product as keyof typeof PRODUCT_INFO]?.name}
                      </span>
                    </div>
                  </td>
                  <td className="text-right py-3 px-4">{data.tier_1}</td>
                  <td className="text-right py-3 px-4">{data.tier_2}</td>
                  <td className="text-right py-3 px-4">{data.tier_3}</td>
                  <td className="text-right py-3 px-4 font-bold">{data.redemptions}</td>
                  <td className="text-right py-3 px-4 font-bold text-green-400">
                    ${((data.revenue_cents || 0) / 100).toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Code Generator & Recent Redemptions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Code Generator */}
        <div className="bg-slate-800 p-6 rounded-lg border border-slate-700">
          <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
            <Code className="w-5 h-5" />
            Code Generator
          </h2>
          
          {!showCodeGenerator ? (
            <button
              onClick={() => setShowCodeGenerator(true)}
              className="w-full py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-medium transition-colors"
            >
              Generate Codes for AppSumo
            </button>
          ) : (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">Product</label>
                <select
                  value={genProduct}
                  onChange={(e) => setGenProduct(e.target.value)}
                  className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg"
                >
                  <option value="chatbot">AI ChatBot Pro</option>
                  <option value="firewall">Web3 Wallet Guardian</option>
                  <option value="inspector">Crypto Inspector</option>
                  <option value="commander">AI Commander</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Tier</label>
                <select
                  value={genTier}
                  onChange={(e) => setGenTier(Number(e.target.value))}
                  className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg"
                >
                  <option value={1}>Tier 1</option>
                  <option value={2}>Tier 2</option>
                  <option value={3}>Tier 3</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Count</label>
                <input
                  type="number"
                  value={genCount}
                  onChange={(e) => setGenCount(Number(e.target.value))}
                  min={1}
                  max={10000}
                  className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg"
                />
              </div>

              <div className="flex gap-2">
                <button
                  onClick={handleGenerateCodes}
                  className="flex-1 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
                >
                  <Download className="w-4 h-4" />
                  Generate & Download CSV
                </button>
                <button
                  onClick={() => setShowCodeGenerator(false)}
                  className="px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors"
                >
                  Cancel
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Recent Redemptions */}
        <div className="bg-slate-800 p-6 rounded-lg border border-slate-700">
          <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
            <Clock className="w-5 h-5" />
            Recent Redemptions
          </h2>
          <div className="space-y-3 max-h-96 overflow-y-auto">
            {recent?.map((redemption: any, i: number) => (
              <div
                key={i}
                className="p-3 bg-slate-700/50 rounded-lg border border-slate-600"
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="font-medium">{redemption.user_email}</span>
                  <span className="text-xs text-slate-400">
                    {new Date(redemption.redeemed_at).toLocaleDateString()}
                  </span>
                </div>
                <div className="text-sm text-slate-400">
                  {redemption.product} • Tier {redemption.tier}
                </div>
              </div>
            )) || (
              <p className="text-slate-400 text-sm">No redemptions yet</p>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

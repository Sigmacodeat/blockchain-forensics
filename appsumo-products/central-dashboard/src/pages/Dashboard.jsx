import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { 
  Activity, CheckCircle, XCircle, AlertCircle, TrendingUp, Users, 
  DollarSign, Zap, Shield, BarChart3, MessageSquare, 
  Package, Server, Settings, Eye, PlayCircle, StopCircle,
  ExternalLink, RefreshCw
} from 'lucide-react'

export default function CentralDashboard() {
  const [products, setProducts] = useState([
    {
      id: 'chatbot-pro',
      name: 'AI ChatBot Pro',
      icon: MessageSquare,
      color: 'from-blue-500 to-purple-600',
      port: { frontend: 3001, backend: 8001 },
      status: 'stopped',
      health: 'unknown',
      users: 1247,
      revenue: 56700,
      uptime: 99.9,
      tier: 'production',
      appsumo: { active: true, licenses: 89, tier1: 34, tier2: 32, tier3: 23 }
    },
    {
      id: 'wallet-guardian',
      name: 'Wallet Guardian',
      icon: Shield,
      color: 'from-green-500 to-emerald-600',
      port: { frontend: 3002, backend: 8002 },
      status: 'stopped',
      health: 'unknown',
      users: 3421,
      revenue: 95400,
      uptime: 99.8,
      tier: 'production',
      appsumo: { active: true, licenses: 156, tier1: 52, tier2: 64, tier3: 40 }
    },
    {
      id: 'analytics-pro',
      name: 'Analytics Pro',
      icon: BarChart3,
      color: 'from-blue-600 to-indigo-600',
      port: { frontend: 3003, backend: 8003 },
      status: 'stopped',
      health: 'unknown',
      users: 2156,
      revenue: 125100,
      uptime: 99.9,
      tier: 'production',
      appsumo: { active: true, licenses: 201, tier1: 67, tier2: 84, tier3: 50 }
    }
  ])

  const [refreshing, setRefreshing] = useState(false)

  const checkHealth = async (productId, backendPort) => {
    try {
      const response = await fetch(`http://localhost:${backendPort}/health`)
      if (response.ok) {
        return 'healthy'
      }
      return 'degraded'
    } catch (error) {
      return 'down'
    }
  }

  const refreshStatus = async () => {
    setRefreshing(true)
    const updatedProducts = await Promise.all(
      products.map(async (product) => {
        const health = await checkHealth(product.id, product.port.backend)
        return {
          ...product,
          health,
          status: health === 'healthy' ? 'running' : 'stopped'
        }
      })
    )
    setProducts(updatedProducts)
    setRefreshing(false)
  }

  useEffect(() => {
    refreshStatus()
    const interval = setInterval(refreshStatus, 10000) // Every 10s
    return () => clearInterval(interval)
  }, [])

  const totalStats = {
    totalUsers: products.reduce((sum, p) => sum + p.users, 0),
    totalRevenue: products.reduce((sum, p) => sum + p.revenue, 0),
    totalLicenses: products.reduce((sum, p) => sum + p.appsumo.licenses, 0),
    avgUptime: (products.reduce((sum, p) => sum + p.uptime, 0) / products.length).toFixed(1),
    runningProducts: products.filter(p => p.status === 'running').length
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'running': return 'text-green-400 bg-green-500/20'
      case 'stopped': return 'text-gray-400 bg-gray-500/20'
      case 'degraded': return 'text-yellow-400 bg-yellow-500/20'
      default: return 'text-gray-400 bg-gray-500/20'
    }
  }

  const getHealthIcon = (health) => {
    switch (health) {
      case 'healthy': return <CheckCircle size={20} className="text-green-400" />
      case 'degraded': return <AlertCircle size={20} className="text-yellow-400" />
      case 'down': return <XCircle size={20} className="text-red-400" />
      default: return <Activity size={20} className="text-gray-400" />
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900">
      {/* Header */}
      <header className="bg-slate-900/80 backdrop-blur border-b border-slate-700">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-purple-600 rounded-xl flex items-center justify-center">
                <Package size={24} className="text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-white">AppSumo Central</h1>
                <p className="text-sm text-slate-400">Manage all 12 products from one place</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={refreshStatus}
                disabled={refreshing}
                className="px-4 py-2 bg-blue-500/20 hover:bg-blue-500/30 border border-blue-500/30 rounded-lg transition-colors flex items-center gap-2"
              >
                <RefreshCw size={16} className={`text-blue-400 ${refreshing ? 'animate-spin' : ''}`} />
                <span className="text-sm font-semibold text-blue-400">Refresh</span>
              </button>
              <div className={`px-4 py-2 rounded-lg border ${
                totalStats.runningProducts === products.length 
                  ? 'bg-green-500/20 border-green-500/30' 
                  : 'bg-yellow-500/20 border-yellow-500/30'
              }`}>
                <div className="flex items-center gap-2">
                  <div className={`w-2 h-2 rounded-full ${
                    totalStats.runningProducts === products.length ? 'bg-green-500' : 'bg-yellow-500'
                  } animate-pulse`}></div>
                  <span className={`text-sm font-semibold ${
                    totalStats.runningProducts === products.length ? 'text-green-400' : 'text-yellow-400'
                  }`}>
                    {totalStats.runningProducts}/{products.length} Running
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Global Stats */}
        <div className="grid md:grid-cols-4 gap-6 mb-8">
          <StatCard
            icon={<Users className="text-blue-400" />}
            label="Total Users"
            value={totalStats.totalUsers.toLocaleString()}
            trend="+124 today"
            color="blue"
          />
          <StatCard
            icon={<DollarSign className="text-green-400" />}
            label="Total Revenue"
            value={`$${(totalStats.totalRevenue / 1000).toFixed(1)}k`}
            trend="+$8.2k this month"
            color="green"
          />
          <StatCard
            icon={<Package className="text-purple-400" />}
            label="Active Licenses"
            value={totalStats.totalLicenses}
            trend="+23 this week"
            color="purple"
          />
          <StatCard
            icon={<Activity className="text-indigo-400" />}
            label="Avg Uptime"
            value={`${totalStats.avgUptime}%`}
            trend="Last 30 days"
            color="indigo"
          />
        </div>

        {/* Products Grid */}
        <div className="space-y-4">
          {products.map((product, index) => (
            <motion.div
              key={product.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              className="bg-slate-800/50 backdrop-blur border border-slate-700 rounded-xl p-6 hover:border-slate-600 transition-colors"
            >
              <div className="flex items-center justify-between mb-4">
                {/* Product Info */}
                <div className="flex items-center gap-4">
                  <div className={`w-14 h-14 bg-gradient-to-r ${product.color} rounded-xl flex items-center justify-center`}>
                    <product.icon size={28} className="text-white" />
                  </div>
                  <div>
                    <h3 className="text-lg font-bold text-white">{product.name}</h3>
                    <div className="flex items-center gap-3 mt-1">
                      <span className={`px-2 py-1 rounded text-xs font-semibold ${getStatusColor(product.status)}`}>
                        {product.status.toUpperCase()}
                      </span>
                      <div className="flex items-center gap-1">
                        {getHealthIcon(product.health)}
                        <span className="text-xs text-slate-400">{product.health}</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-2">
                  <a
                    href={`http://localhost:${product.port.frontend}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="px-3 py-2 bg-blue-500/20 hover:bg-blue-500/30 border border-blue-500/30 rounded-lg transition-colors flex items-center gap-2"
                  >
                    <ExternalLink size={16} className="text-blue-400" />
                    <span className="text-sm font-semibold text-blue-400">Open</span>
                  </a>
                  <a
                    href={`http://localhost:${product.port.frontend}/activate`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="px-3 py-2 bg-purple-500/20 hover:bg-purple-500/30 border border-purple-500/30 rounded-lg transition-colors flex items-center gap-2"
                  >
                    <Zap size={16} className="text-purple-400" />
                    <span className="text-sm font-semibold text-purple-400">Activate</span>
                  </a>
                </div>
              </div>

              {/* Metrics */}
              <div className="grid grid-cols-4 gap-4 mt-4 pt-4 border-t border-slate-700">
                <MetricItem label="Users" value={product.users.toLocaleString()} />
                <MetricItem label="Revenue" value={`$${(product.revenue / 1000).toFixed(1)}k`} />
                <MetricItem label="Licenses" value={product.appsumo.licenses} />
                <MetricItem label="Uptime" value={`${product.uptime}%`} />
              </div>

              {/* AppSumo Tiers */}
              <div className="mt-4 pt-4 border-t border-slate-700">
                <div className="flex items-center gap-6">
                  <div className="text-sm text-slate-400">AppSumo Tiers:</div>
                  <div className="flex items-center gap-4">
                    <TierBadge tier="1" count={product.appsumo.tier1} />
                    <TierBadge tier="2" count={product.appsumo.tier2} />
                    <TierBadge tier="3" count={product.appsumo.tier3} />
                  </div>
                </div>
              </div>

              {/* Ports Info */}
              <div className="mt-3 flex items-center gap-4 text-xs text-slate-500">
                <span>Frontend: :{product.port.frontend}</span>
                <span>•</span>
                <span>Backend: :{product.port.backend}</span>
              </div>
            </motion.div>
          ))}
        </div>

        {/* Quick Start Info */}
        <div className="mt-8 bg-slate-800/50 backdrop-blur border border-slate-700 rounded-xl p-6">
          <h3 className="text-lg font-bold text-white mb-4">Quick Start Commands</h3>
          <div className="space-y-3">
            <CommandLine 
              label="Start All Products"
              command="./START_ALL_TOP3.sh"
            />
            <CommandLine 
              label="Stop All Products"
              command="./STOP_ALL_TOP3.sh"
            />
            <CommandLine 
              label="Test License"
              command="Tier 1: TEST-TEST-TEST-TES1 | Tier 2: ABCD-EFGH-IJKL-MNO2 | Tier 3: XXXX-YYYY-ZZZZ-WWW3"
            />
          </div>
        </div>
      </div>
    </div>
  )
}

// Helper Components
function StatCard({ icon, label, value, trend, color }) {
  return (
    <div className="bg-slate-800/50 backdrop-blur border border-slate-700 rounded-xl p-6">
      <div className="flex items-center justify-between mb-2">
        <div className={`w-10 h-10 bg-${color}-500/20 rounded-lg flex items-center justify-center`}>
          {icon}
        </div>
      </div>
      <div className="text-2xl font-bold text-white mb-1">{value}</div>
      <div className="text-sm text-slate-400">{label}</div>
      <div className="text-xs text-slate-500 mt-1">{trend}</div>
    </div>
  )
}

function MetricItem({ label, value }) {
  return (
    <div>
      <div className="text-sm font-semibold text-white">{value}</div>
      <div className="text-xs text-slate-400">{label}</div>
    </div>
  )
}

function TierBadge({ tier, count }) {
  const colors = {
    '1': 'bg-blue-500/20 text-blue-400 border-blue-500/30',
    '2': 'bg-purple-500/20 text-purple-400 border-purple-500/30',
    '3': 'bg-indigo-500/20 text-indigo-400 border-indigo-500/30'
  }
  
  return (
    <div className={`px-3 py-1 rounded-lg border text-xs font-semibold ${colors[tier]}`}>
      T{tier}: {count}
    </div>
  )
}

function CommandLine({ label, command }) {
  return (
    <div>
      <div className="text-sm text-slate-400 mb-1">{label}:</div>
      <div className="bg-slate-900/50 border border-slate-700 rounded-lg p-3 font-mono text-sm text-slate-300">
        {command}
      </div>
    </div>
  )
}

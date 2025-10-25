import PortfolioTracker from '../components/PortfolioTracker'
import { BarChart3, TrendingUp, DollarSign, Activity, Globe, Zap } from 'lucide-react'

export default function Dashboard() {
  const stats = {
    portfolioValue: 45782.34,
    change24h: 3.42,
    chains: 35,
    transactions: 1247
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-purple-50 to-white">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-8 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="w-14 h-14 bg-gradient-to-r from-blue-600 to-purple-600 rounded-xl flex items-center justify-center text-white shadow-lg">
                <BarChart3 size={28} />
              </div>
              <div>
                <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                  CryptoMetrics Analytics Pro
                </h1>
                <p className="text-gray-600">Portfolio Tracking & Analytics</p>
              </div>
            </div>
            <button className="px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:opacity-90 transition-opacity font-semibold shadow-lg">
              Generate Tax Report
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-8 py-8">
        {/* Quick Stats */}
        <div className="grid md:grid-cols-4 gap-6 mb-8">
          <StatCard
            icon={<DollarSign className="text-blue-600" />}
            label="Portfolio Value"
            value={`$${stats.portfolioValue.toLocaleString()}`}
            trend="+3.42%"
            color="blue"
          />
          <StatCard
            icon={<Globe className="text-purple-600" />}
            label="Supported Chains"
            value={stats.chains}
            trend="35+"
            color="purple"
          />
          <StatCard
            icon={<Activity className="text-green-600" />}
            label="Transactions"
            value={stats.transactions}
            trend="+124 today"
            color="green"
          />
          <StatCard
            icon={<Zap className="text-orange-600" />}
            label="Real-Time"
            value="Live"
            trend="< 100ms"
            color="orange"
          />
        </div>

        {/* Portfolio Tracker */}
        <div className="mb-8">
          <PortfolioTracker />
        </div>

        {/* Features */}
        <div className="grid md:grid-cols-3 gap-6">
          <FeatureCard
            title="Multi-Chain Support"
            description="Track assets across 35+ blockchain networks"
            icon="🌐"
          />
          <FeatureCard
            title="Tax Reports"
            description="Generate tax reports for 10+ jurisdictions"
            icon="📋"
          />
          <FeatureCard
            title="NFT Analytics"
            description="Track NFT collections and floor prices"
            icon="🖼️"
          />
          <FeatureCard
            title="DeFi Dashboard"
            description="Monitor 500+ DeFi protocols"
            icon="💰"
          />
          <FeatureCard
            title="White-Label"
            description="Custom branding for your platform"
            icon="🎨"
          />
          <FeatureCard
            title="API Access"
            description="Full REST API for integrations"
            icon="🔌"
          />
        </div>
      </div>
    </div>
  )
}

function StatCard({ icon, label, value, trend, color }) {
  return (
    <div className="bg-white rounded-xl shadow-lg border-2 border-gray-100 p-6 hover:shadow-xl transition-all hover:border-blue-200">
      <div className="flex items-center justify-between mb-4">
        <div className="p-3 bg-gradient-to-br from-gray-50 to-gray-100 rounded-lg">
          {icon}
        </div>
        <span className="text-xs font-semibold text-green-600">{trend}</span>
      </div>
      <h3 className="text-2xl font-bold text-gray-900 mb-1">{value}</h3>
      <p className="text-sm text-gray-600">{label}</p>
    </div>
  )
}

function FeatureCard({ title, description, icon }) {
  return (
    <div className="bg-white rounded-xl shadow-lg border-2 border-gray-100 p-6 hover:shadow-xl transition-all hover:border-purple-200">
      <div className="text-4xl mb-4">{icon}</div>
      <h3 className="font-bold text-gray-900 mb-2">{title}</h3>
      <p className="text-sm text-gray-600">{description}</p>
    </div>
  )
}

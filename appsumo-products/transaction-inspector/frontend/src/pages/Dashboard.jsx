import TransactionTracer from '../components/TransactionTracer'
import { Search, Activity, Shield, TrendingUp } from 'lucide-react'

export default function Dashboard() {
  const stats = {
    totalTraces: 5821,
    chainsSupported: 35,
    avgTraceTime: '2.3s',
    successRate: 98.7
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-purple-50 to-white">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-8 py-6">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 bg-gradient-to-r from-blue-600 to-purple-600 rounded-xl flex items-center justify-center text-white shadow-lg">
              <Search size={28} />
            </div>
            <div>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                Transaction Inspector
              </h1>
              <p className="text-gray-600">Multi-Chain Transaction Tracing</p>
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-8 py-8">
        {/* Stats */}
        <div className="grid md:grid-cols-4 gap-6 mb-8">
          <StatCard
            icon={<Search className="text-blue-600" />}
            label="Total Traces"
            value={stats.totalTraces.toLocaleString()}
            trend="+124 today"
          />
          <StatCard
            icon={<Activity className="text-purple-600" />}
            label="Chains Supported"
            value={stats.chainsSupported}
            trend="35+ networks"
          />
          <StatCard
            icon={<TrendingUp className="text-green-600" />}
            label="Avg Trace Time"
            value={stats.avgTraceTime}
            trend="< 3 seconds"
          />
          <StatCard
            icon={<Shield className="text-indigo-600" />}
            label="Success Rate"
            value={`${stats.successRate}%`}
            trend="High accuracy"
          />
        </div>

        {/* Transaction Tracer */}
        <div className="mb-8">
          <TransactionTracer />
        </div>

        {/* Features */}
        <div className="grid md:grid-cols-3 gap-6">
          <FeatureCard
            title="Multi-Chain Support"
            description="Trace across 35+ blockchain networks"
            icon="🔗"
          />
          <FeatureCard
            title="Real-Time Tracing"
            description="Track transactions in under 3 seconds"
            icon="⚡"
          />
          <FeatureCard
            title="Multi-Hop Detection"
            description="Follow complex transaction paths"
            icon="🔍"
          />
        </div>
      </div>
    </div>
  )
}

function StatCard({ icon, label, value, trend }) {
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

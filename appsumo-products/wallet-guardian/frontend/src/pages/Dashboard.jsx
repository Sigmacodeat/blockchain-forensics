import FirewallScanner from '../components/FirewallScanner'
import { Shield, Zap, TrendingDown, CheckCircle2 } from 'lucide-react'

export default function Dashboard() {
  const stats = {
    totalScans: 3421,
    threatsBlocked: 127,
    protectionRate: 99.8,
    avgScanTime: '0.3s'
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-blue-50 to-white">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-8 py-6">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 bg-gradient-to-r from-purple-600 to-blue-600 rounded-xl flex items-center justify-center text-white shadow-lg">
              <Shield size={28} />
            </div>
            <div>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent">
                Web3 Wallet Guardian
              </h1>
              <p className="text-gray-600">Advanced Security Firewall</p>
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-8 py-8">
        {/* Stats */}
        <div className="grid md:grid-cols-4 gap-6 mb-8">
          <StatCard
            icon={<Shield className="text-purple-600" />}
            label="Total Scans"
            value={stats.totalScans.toLocaleString()}
            color="purple"
          />
          <StatCard
            icon={<Zap className="text-blue-600" />}
            label="Threats Blocked"
            value={stats.threatsBlocked}
            color="blue"
          />
          <StatCard
            icon={<CheckCircle2 className="text-green-600" />}
            label="Protection Rate"
            value={`${stats.protectionRate}%`}
            color="green"
          />
          <StatCard
            icon={<TrendingDown className="text-indigo-600" />}
            label="Avg Scan Time"
            value={stats.avgScanTime}
            color="indigo"
          />
        </div>

        {/* Scanner */}
        <div className="mb-8">
          <FirewallScanner />
        </div>

        {/* Features */}
        <div className="grid md:grid-cols-3 gap-6">
          <FeatureCard
            title="15 ML Models"
            description="Advanced machine learning for threat detection"
            icon="🤖"
          />
          <FeatureCard
            title="Token Scanner"
            description="Analyze token approvals and permissions"
            icon="🔍"
          />
          <FeatureCard
            title="Phishing Guard"
            description="Real-time phishing website detection"
            icon="🛡️"
          />
        </div>
      </div>
    </div>
  )
}

function StatCard({ icon, label, value, color }) {
  return (
    <div className="bg-white rounded-xl shadow-sm border-2 border-gray-100 p-6 hover:shadow-lg transition-all hover:border-purple-200">
      <div className="flex items-center justify-between mb-4">
        <div className="p-3 bg-gradient-to-br from-gray-50 to-gray-100 rounded-lg">
          {icon}
        </div>
      </div>
      <h3 className="text-2xl font-bold text-gray-900 mb-1">{value}</h3>
      <p className="text-sm text-gray-600">{label}</p>
    </div>
  )
}

function FeatureCard({ title, description, icon }) {
  return (
    <div className="bg-white rounded-xl shadow-sm border-2 border-gray-100 p-6 hover:shadow-lg transition-all hover:border-purple-200">
      <div className="text-4xl mb-4">{icon}</div>
      <h3 className="font-bold text-gray-900 mb-2">{title}</h3>
      <p className="text-sm text-gray-600">{description}</p>
    </div>
  )
}

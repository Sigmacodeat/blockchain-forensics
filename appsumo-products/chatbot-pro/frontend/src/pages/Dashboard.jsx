import { useState, useEffect } from 'react'
import { MessageSquare, Users, TrendingUp, Settings, BarChart3, Zap } from 'lucide-react'

export default function Dashboard() {
  const [stats, setStats] = useState({
    totalChats: 1247,
    activeUsers: 89,
    avgResponseTime: '1.2s',
    satisfaction: 94
  })

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-r from-purple-600 to-blue-600 rounded-lg flex items-center justify-center text-white">
                <MessageSquare size={20} />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">AI ChatBot Pro</h1>
                <p className="text-sm text-gray-600">Dashboard</p>
              </div>
            </div>
            <button className="px-4 py-2 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg hover:opacity-90 transition-opacity">
              <Settings size={18} className="inline mr-2" />
              Settings
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-8 py-8">
        {/* Stats Grid */}
        <div className="grid md:grid-cols-4 gap-6 mb-8">
          <StatCard
            icon={<MessageSquare />}
            label="Total Chats"
            value={stats.totalChats.toLocaleString()}
            trend="+12%"
            color="purple"
          />
          <StatCard
            icon={<Users />}
            label="Active Users"
            value={stats.activeUsers}
            trend="+8%"
            color="blue"
          />
          <StatCard
            icon={<Zap />}
            label="Avg Response"
            value={stats.avgResponseTime}
            trend="-5%"
            color="green"
          />
          <StatCard
            icon={<TrendingUp />}
            label="Satisfaction"
            value={`${stats.satisfaction}%`}
            trend="+3%"
            color="indigo"
          />
        </div>

        {/* Recent Activity */}
        <div className="bg-white rounded-xl shadow-sm border p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">Recent Conversations</h2>
            <button className="text-sm text-purple-600 hover:text-purple-700">View All</button>
          </div>

          <div className="space-y-4">
            {[
              { user: 'John Doe', message: 'How can I upgrade my plan?', time: '2 min ago', status: 'active' },
              { user: 'Jane Smith', message: 'What are the pricing options?', time: '5 min ago', status: 'resolved' },
              { user: 'Mike Johnson', message: 'I need help with integration', time: '12 min ago', status: 'active' }
            ].map((chat, idx) => (
              <div key={idx} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors cursor-pointer">
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 bg-gradient-to-r from-purple-400 to-blue-400 rounded-full flex items-center justify-center text-white font-semibold">
                    {chat.user.charAt(0)}
                  </div>
                  <div>
                    <p className="font-medium text-gray-900">{chat.user}</p>
                    <p className="text-sm text-gray-600">{chat.message}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-xs text-gray-500">{chat.time}</p>
                  <span className={`inline-block px-2 py-1 text-xs rounded-full mt-1 ${
                    chat.status === 'active' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-700'
                  }`}>
                    {chat.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Features Grid */}
        <div className="grid md:grid-cols-3 gap-6 mt-8">
          <FeatureCard
            icon={<MessageSquare className="text-purple-600" />}
            title="Multi-Language"
            description="Support for 43 languages with auto-detection"
          />
          <FeatureCard
            icon={<Zap className="text-blue-600" />}
            title="Voice Input"
            description="Speech-to-text in 43 locales"
          />
          <FeatureCard
            icon={<BarChart3 className="text-green-600" />}
            title="Analytics"
            description="Real-time chat analytics and insights"
          />
        </div>
      </div>
    </div>
  )
}

function StatCard({ icon, label, value, trend, color }) {
  const colors = {
    purple: 'from-purple-500 to-purple-600',
    blue: 'from-blue-500 to-blue-600',
    green: 'from-green-500 to-green-600',
    indigo: 'from-indigo-500 to-indigo-600'
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border p-6 hover:shadow-md transition-shadow">
      <div className="flex items-center justify-between mb-4">
        <div className={`p-3 bg-gradient-to-r ${colors[color]} text-white rounded-lg`}>
          {icon}
        </div>
        <span className="text-xs font-semibold text-green-600">{trend}</span>
      </div>
      <h3 className="text-2xl font-bold text-gray-900 mb-1">{value}</h3>
      <p className="text-sm text-gray-600">{label}</p>
    </div>
  )
}

function FeatureCard({ icon, title, description }) {
  return (
    <div className="bg-white rounded-xl shadow-sm border p-6 hover:shadow-md transition-shadow">
      <div className="mb-4">{icon}</div>
      <h3 className="font-semibold text-gray-900 mb-2">{title}</h3>
      <p className="text-sm text-gray-600">{description}</p>
    </div>
  )
}

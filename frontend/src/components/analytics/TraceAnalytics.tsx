import { useQuery } from '@tanstack/react-query'
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import { TrendingUp, Activity, Shield, Target } from 'lucide-react'
import LoadingSpinner from '@/components/ui/LoadingSpinner'

interface AnalyticsData {
  traces_over_time: Array<{ date: string; count: number }>
  risk_distribution: Array<{ level: string; count: number }>
  top_addresses: Array<{ address: string; trace_count: number }>
  daily_stats: Array<{ day: string; traces: number; high_risk: number }>
}

const RISK_COLORS = ['#10b981', '#f59e0b', '#ef4444', '#dc2626']

export default function TraceAnalytics() {
  const { data: analytics, isPending } = useQuery<AnalyticsData>({
    queryKey: ['trace-analytics'],
    queryFn: async () => {
      // Mock data for now
      return {
        traces_over_time: [
          { date: '2025-01-01', count: 5 },
          { date: '2025-01-02', count: 8 },
          { date: '2025-01-03', count: 12 },
          { date: '2025-01-04', count: 15 },
          { date: '2025-01-05', count: 10 },
          { date: '2025-01-06', count: 18 },
          { date: '2025-01-07', count: 22 },
        ],
        risk_distribution: [
          { level: 'Low', count: 45 },
          { level: 'Medium', count: 25 },
          { level: 'High', count: 15 },
          { level: 'Critical', count: 5 },
        ],
        top_addresses: [
          { address: '0x1234...5678', trace_count: 25 },
          { address: '0xabcd...efgh', trace_count: 18 },
          { address: '0x9876...5432', trace_count: 12 },
          { address: '0xdef0...1234', trace_count: 8 },
          { address: '0x5678...abcd', trace_count: 5 },
        ],
        daily_stats: [
          { day: 'Mo', traces: 12, high_risk: 3 },
          { day: 'Di', traces: 19, high_risk: 5 },
          { day: 'Mi', traces: 15, high_risk: 2 },
          { day: 'Do', traces: 22, high_risk: 7 },
          { day: 'Fr', traces: 18, high_risk: 4 },
          { day: 'Sa', traces: 8, high_risk: 1 },
          { day: 'So', traces: 6, high_risk: 0 },
        ],
      }
    },
    refetchInterval: 60000, // Refresh every minute
  })

  if (isPending) {
    return (
      <div className="flex items-center justify-center py-12">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  if (!analytics) return null

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3 mb-6">
        <TrendingUp className="w-6 h-6 text-primary-600" />
        <h2 className="text-2xl font-bold text-foreground">Trace Analytics</h2>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="card p-4 bg-gradient-to-br from-primary-50 to-primary-100">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-primary-600 font-medium">Total Traces</p>
              <p className="text-2xl font-bold text-primary-900">
                {analytics.traces_over_time.reduce((sum, d) => sum + d.count, 0)}
              </p>
            </div>
            <Activity className="w-8 h-8 text-primary-600 opacity-50" />
          </div>
        </div>

        <div className="card p-4 bg-gradient-to-br from-green-50 to-green-100">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-green-600 font-medium">Low Risk</p>
              <p className="text-2xl font-bold text-green-900">
                {analytics.risk_distribution.find((r) => r.level === 'Low')?.count || 0}
              </p>
            </div>
            <Shield className="w-8 h-8 text-green-600 opacity-50" />
          </div>
        </div>

        <div className="card p-4 bg-gradient-to-br from-red-50 to-red-100">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-red-600 font-medium">High Risk</p>
              <p className="text-2xl font-bold text-red-900">
                {analytics.risk_distribution.find((r) => r.level === 'High')?.count || 0}
              </p>
            </div>
            <Target className="w-8 h-8 text-red-600 opacity-50" />
          </div>
        </div>

        <div className="card p-4 bg-gradient-to-br from-purple-50 to-purple-100">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-purple-600 font-medium">Avg Daily</p>
              <p className="text-2xl font-bold text-purple-900">
                {(
                  analytics.daily_stats.reduce((sum, d) => sum + d.traces, 0) /
                  analytics.daily_stats.length
                ).toFixed(1)}
              </p>
            </div>
            <TrendingUp className="w-8 h-8 text-purple-600 opacity-50" />
          </div>
        </div>
      </div>

      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Traces Over Time */}
        <div className="card p-6 bg-card border border-border">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Traces Over Time</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={analytics.traces_over_time}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line
                type="monotone"
                dataKey="count"
                stroke="#0284c7"
                strokeWidth={2}
                dot={{ fill: '#0284c7' }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Risk Distribution */}
        <div className="card p-6 bg-card border border-border">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Risk Distribution</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={analytics.risk_distribution}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ level, count }) => `${level}: ${count}`}
                outerRadius={100}
                fill="#8884d8"
                dataKey="count"
              >
                {analytics.risk_distribution.map((_, index) => (
                  <Cell key={`cell-${index}`} fill={RISK_COLORS[index % RISK_COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Charts Row 2 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Daily Stats */}
        <div className="card p-6 bg-card border border-border">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Daily Activity</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={analytics.daily_stats}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="day" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="traces" fill="#0284c7" name="Total Traces" />
              <Bar dataKey="high_risk" fill="#ef4444" name="High Risk" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Top Addresses */}
        <div className="card p-6 bg-card border border-border">
          <h3 className="text-lg font-semibold text-foreground mb-4">Top Traced Addresses</h3>
          <div className="space-y-3">
            {analytics.top_addresses.map((addr, index) => (
              <div key={addr.address} className="flex items-center justify-between p-3 bg-muted rounded-lg border border-border">
                <div className="flex items-center gap-3">
                  <span className="flex items-center justify-center w-8 h-8 bg-primary-100 text-primary-700 rounded-full font-semibold text-sm">
                    {index + 1}
                  </span>
                  <span className="font-mono text-sm text-foreground">{addr.address}</span>
                </div>
                <span className="text-sm font-medium text-muted-foreground">{addr.trace_count} traces</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

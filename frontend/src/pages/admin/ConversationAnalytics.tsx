/**
 * Conversation Analytics Admin-Dashboard
 * Deep-Dive in User-Journey, Multi-Session-Tracking, Conversion-Funnel
 */

import { useEffect, useState, useCallback } from 'react'
import { BarChart3, Users, MessageSquare, TrendingUp, Filter, Download, Eye, RefreshCw } from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

interface OverviewStats {
  total_sessions: number
  total_messages: number
  total_users: number
  avg_messages_per_session: number
  returning_users_rate: number
  conversion_rate: number
}

interface FunnelMetrics {
  total_visitors: number
  chat_started: number
  chat_started_rate: number
  demo_viewed: number
  demo_viewed_rate: number
  trial_started: number
  trial_started_rate: number
  payment_completed: number
  payment_completed_rate: number
}

interface Session {
  id: string
  user_id: string | null
  anonymous_id: string | null
  ip_address: string
  created_at: string
  message_count: number
  events: Array<{ type: string; timestamp: string }>
}

export default function ConversationAnalytics() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [overview, setOverview] = useState<OverviewStats | null>(null)
  const [funnel, setFunnel] = useState<FunnelMetrics | null>(null)
  const [sessions, setSessions] = useState<Session[]>([])
  const [intents, setIntents] = useState<Record<string, number>>({})
  const [timeRange, setTimeRange] = useState(7)
  const [autoRefresh, setAutoRefresh] = useState(false)

  useEffect(() => {
    if (!user || user.role !== 'admin') {
      navigate('/dashboard')
      return
    }
    fetchAnalytics()
  }, [user, timeRange])

  // Auto-refresh every 30s if enabled
  useEffect(() => {
    if (!autoRefresh) return
    const interval = setInterval(() => {
      fetchAnalytics()
    }, 30000)
    return () => clearInterval(interval)
  }, [autoRefresh, timeRange])

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      // Ctrl/Cmd + E = Export CSV
      if ((e.ctrlKey || e.metaKey) && e.key === 'e') {
        e.preventDefault()
        exportToCSV()
      }
      // Ctrl/Cmd + R = Refresh
      if ((e.ctrlKey || e.metaKey) && e.key === 'r') {
        e.preventDefault()
        fetchAnalytics()
      }
    }
    window.addEventListener('keydown', handleKeyPress)
    return () => window.removeEventListener('keydown', handleKeyPress)
  }, [overview, sessions])

  const fetchAnalytics = async () => {
    try {
      const token = localStorage.getItem('token')
      
      // Overview
      const overviewRes = await fetch(`${API_URL}/api/v1/admin/conversation-analytics/overview?days=${timeRange}`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      const overviewData = await overviewRes.json()
      setOverview(overviewData)

      // Funnel
      const funnelRes = await fetch(`${API_URL}/api/v1/admin/conversation-analytics/funnel?days=30`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      const funnelData = await funnelRes.json()
      setFunnel(funnelData)

      // Sessions
      const sessionsRes = await fetch(`${API_URL}/api/v1/admin/conversation-analytics/sessions?limit=20`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      const sessionsData = await sessionsRes.json()
      setSessions(sessionsData.sessions || [])

      // Intents
      const intentsRes = await fetch(`${API_URL}/api/v1/admin/conversation-analytics/intents?days=${timeRange}`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      const intentsData = await intentsRes.json()
      setIntents(intentsData.intents || {})

      setLoading(false)
    } catch (error) {
      console.error('Error fetching analytics:', error)
      setLoading(false)
    }
  }

  const viewSessionDetails = (sessionId: string) => {
    navigate(`/admin/conversation-analytics/session/${sessionId}`)
  }

  const exportToCSV = useCallback(() => {
    if (!sessions.length) {
      toast.error('No data to export')
      return
    }

    const headers = ['Session ID', 'User', 'Messages', 'Events', 'Created']
    const rows = sessions.map(s => [
      s.id,
      s.user_id || s.anonymous_id || 'Unknown',
      s.message_count,
      s.events.length,
      new Date(s.created_at).toLocaleDateString()
    ])

    const csv = [
      headers.join(','),
      ...rows.map(row => row.join(','))
    ].join('\n')

    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `conversation-analytics-${new Date().toISOString()}.csv`
    a.click()
    URL.revokeObjectURL(url)
    toast.success('Exported to CSV! 📥')
  }, [sessions])

  const exportToPDF = useCallback(() => {
    window.print()
    toast.success('Print dialog opened! 🖨️')
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6" role="main" aria-label="Conversation Analytics Dashboard">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Conversation Analytics</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Deep-Dive in User-Journey & Multi-Session-Tracking
          </p>
          <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
            Shortcuts: Ctrl+E (Export) • Ctrl+R (Refresh)
          </p>
        </div>
        
        <div className="flex items-center gap-3">
          {/* Auto-Refresh Toggle */}
          <button
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={`flex items-center gap-2 px-3 py-2 rounded-lg border transition-colors ${
              autoRefresh 
                ? 'bg-green-100 border-green-300 text-green-700 dark:bg-green-900 dark:border-green-700 dark:text-green-300'
                : 'bg-white border-gray-300 text-gray-700 dark:bg-gray-800 dark:border-gray-600 dark:text-gray-300'
            }`}
            aria-label={autoRefresh ? 'Auto-refresh enabled' : 'Auto-refresh disabled'}
            aria-pressed={autoRefresh}
          >
            <RefreshCw className={`h-4 w-4 ${autoRefresh ? 'animate-spin' : ''}`} />
            Auto {autoRefresh ? 'ON' : 'OFF'}
          </button>

          {/* Export Buttons */}
          <button
            onClick={exportToCSV}
            className="flex items-center gap-2 px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            aria-label="Export data to CSV"
          >
            <Download className="h-4 w-4" />
            CSV
          </button>
          
          <button
            onClick={exportToPDF}
            className="flex items-center gap-2 px-3 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
            aria-label="Export data to PDF"
          >
            <Download className="h-4 w-4" />
            PDF
          </button>

          {/* Time Range Selector */}
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(Number(e.target.value))}
            className="px-4 py-2 border rounded-lg dark:bg-gray-800 dark:border-gray-700"
            aria-label="Select time range"
          >
            <option value={1}>Last 24 hours</option>
            <option value={7}>Last 7 days</option>
            <option value={30}>Last 30 days</option>
            <option value={90}>Last 90 days</option>
          </select>
        </div>
      </div>

      {/* Overview Stats */}
      {overview && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6" role="region" aria-label="Overview statistics">
          <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700" role="article" aria-label="Total sessions statistic">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-blue-100 dark:bg-blue-900 rounded-lg" aria-hidden="true">
                <MessageSquare className="h-6 w-6 text-blue-600 dark:text-blue-400" />
              </div>
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Total Sessions</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white" aria-live="polite">{overview.total_sessions}</p>
              </div>
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-green-100 dark:bg-green-900 rounded-lg">
                <Users className="h-6 w-6 text-green-600 dark:text-green-400" />
              </div>
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Unique Users</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">{overview.total_users}</p>
              </div>
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-purple-100 dark:bg-purple-900 rounded-lg">
                <TrendingUp className="h-6 w-6 text-purple-600 dark:text-purple-400" />
              </div>
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Conversion Rate</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">{overview.conversion_rate}%</p>
              </div>
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-orange-100 dark:bg-orange-900 rounded-lg">
                <BarChart3 className="h-6 w-6 text-orange-600 dark:text-orange-400" />
              </div>
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Avg Messages/Session</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">{overview.avg_messages_per_session}</p>
              </div>
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-pink-100 dark:bg-pink-900 rounded-lg">
                <Users className="h-6 w-6 text-pink-600 dark:text-pink-400" />
              </div>
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Returning Users</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">{overview.returning_users_rate}%</p>
              </div>
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-cyan-100 dark:bg-cyan-900 rounded-lg">
                <MessageSquare className="h-6 w-6 text-cyan-600 dark:text-cyan-400" />
              </div>
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Total Messages</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">{overview.total_messages}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Conversion Funnel */}
      {funnel && (
        <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-6">Conversion Funnel (30 Days)</h2>
          
          <div className="space-y-4">
            {/* Visitors */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Page Visitors</span>
                <span className="text-sm font-bold text-gray-900 dark:text-white">{funnel.total_visitors}</span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-4">
                <div className="bg-blue-600 h-4 rounded-full" style={{ width: '100%' }}></div>
              </div>
            </div>

            {/* Chat Started */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Chat Started</span>
                <span className="text-sm font-bold text-gray-900 dark:text-white">
                  {funnel.chat_started} ({funnel.chat_started_rate}%)
                </span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-4">
                <div className="bg-green-600 h-4 rounded-full" style={{ width: `${funnel.chat_started_rate}%` }}></div>
              </div>
            </div>

            {/* Demo Viewed */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Demo Viewed</span>
                <span className="text-sm font-bold text-gray-900 dark:text-white">
                  {funnel.demo_viewed} ({funnel.demo_viewed_rate}%)
                </span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-4">
                <div className="bg-purple-600 h-4 rounded-full" style={{ width: `${funnel.demo_viewed_rate}%` }}></div>
              </div>
            </div>

            {/* Trial Started */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Trial Started</span>
                <span className="text-sm font-bold text-gray-900 dark:text-white">
                  {funnel.trial_started} ({funnel.trial_started_rate}%)
                </span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-4">
                <div className="bg-orange-600 h-4 rounded-full" style={{ width: `${funnel.trial_started_rate}%` }}></div>
              </div>
            </div>

            {/* Payment Completed */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Payment Completed</span>
                <span className="text-sm font-bold text-gray-900 dark:text-white">
                  {funnel.payment_completed} ({funnel.payment_completed_rate}%)
                </span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-4">
                <div className="bg-emerald-600 h-4 rounded-full" style={{ width: `${funnel.payment_completed_rate}%` }}></div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Intent Distribution */}
      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700">
        <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-6">Top Intents</h2>
        
        <div className="space-y-3">
          {Object.entries(intents)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 8)
            .map(([intent, count]) => (
              <div key={intent} className="flex items-center justify-between">
                <span className="text-sm text-gray-700 dark:text-gray-300 capitalize">
                  {intent.replace(/_/g, ' ')}
                </span>
                <div className="flex items-center gap-3">
                  <div className="w-32 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                    <div
                      className="bg-blue-600 h-2 rounded-full"
                      style={{
                        width: `${(count / Math.max(...Object.values(intents))) * 100}%`
                      }}
                    ></div>
                  </div>
                  <span className="text-sm font-bold text-gray-900 dark:text-white w-8">{count}</span>
                </div>
              </div>
            ))}
        </div>
      </div>

      {/* Recent Sessions */}
      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700">
        <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-6">Recent Sessions</h2>
        
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-200 dark:border-gray-700">
                <th className="text-left py-3 px-4 text-sm font-medium text-gray-700 dark:text-gray-300">Session ID</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-gray-700 dark:text-gray-300">User</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-gray-700 dark:text-gray-300">Messages</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-gray-700 dark:text-gray-300">Events</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-gray-700 dark:text-gray-300">Created</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-gray-700 dark:text-gray-300">Actions</th>
              </tr>
            </thead>
            <tbody>
              {sessions.map((session) => (
                <tr key={session.id} className="border-b border-gray-100 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700/50">
                  <td className="py-3 px-4 text-sm text-gray-900 dark:text-white font-mono">
                    {session.id.substring(0, 12)}...
                  </td>
                  <td className="py-3 px-4 text-sm text-gray-700 dark:text-gray-300">
                    {session.user_id ? `User ${session.user_id.substring(0, 8)}` : 
                     session.anonymous_id ? `Anon ${session.anonymous_id.substring(5, 13)}` : 'Unknown'}
                  </td>
                  <td className="py-3 px-4 text-sm text-gray-700 dark:text-gray-300">{session.message_count}</td>
                  <td className="py-3 px-4 text-sm text-gray-700 dark:text-gray-300">{session.events.length}</td>
                  <td className="py-3 px-4 text-sm text-gray-700 dark:text-gray-300">
                    {new Date(session.created_at).toLocaleDateString()}
                  </td>
                  <td className="py-3 px-4">
                    <button
                      onClick={() => viewSessionDetails(session.id)}
                      className="text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300 flex items-center gap-1 text-sm"
                    >
                      <Eye className="h-4 w-4" />
                      View
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

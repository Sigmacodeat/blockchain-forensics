/**
 * Chat Analytics Dashboard (Admin-only)
 * Zeigt Chat-Statistiken, Feedback, häufige Fragen etc.
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { 
  MessageCircle, 
  ThumbsUp, 
  ThumbsDown, 
  TrendingUp, 
  Users,
  Clock,
  BarChart3,
  Activity
} from 'lucide-react'

interface ChatStats {
  total_conversations: number
  total_messages: number
  positive_feedback: number
  negative_feedback: number
  avg_messages_per_conversation: number
  active_sessions_24h: number
  top_intents: Array<{ intent: string; count: number }>
  hourly_distribution: Array<{ hour: number; count: number }>
}

export default function ChatAnalytics() {
  const [timeRange, setTimeRange] = useState<'24h' | '7d' | '30d'>('24h')

  // Fetch Chat-Analytics
  const { data: stats, isLoading } = useQuery<ChatStats>({
    queryKey: ['chat-analytics', timeRange],
    queryFn: async () => {
      const response = await fetch(
        `/api/v1/admin/chat-analytics?range=${timeRange}`
      )
      if (!response.ok) throw new Error('Failed to fetch analytics')
      return response.json()
    }
  })

  const StatCard = ({ 
    title, 
    value, 
    icon: Icon, 
    trend, 
    color = 'primary' 
  }: { 
    title: string
    value: string | number
    icon: any
    trend?: string
    color?: string
  }) => (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white dark:bg-slate-800 rounded-lg p-6 shadow-sm border border-gray-200 dark:border-slate-700"
    >
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-muted-foreground">{title}</p>
          <p className="text-3xl font-bold mt-2">{value}</p>
          {trend && (
            <p className="text-xs text-green-600 dark:text-green-400 mt-1 flex items-center gap-1">
              <TrendingUp className="w-3 h-3" />
              {trend}
            </p>
          )}
        </div>
        <div className={`p-3 rounded-lg bg-${color}-100 dark:bg-${color}-900/20`}>
          <Icon className={`w-6 h-6 text-${color}-600 dark:text-${color}-400`} />
        </div>
      </div>
    </motion.div>
  )

  if (isLoading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600" />
        </div>
      </div>
    )
  }

  const feedbackRate = stats
    ? ((stats.positive_feedback / (stats.positive_feedback + stats.negative_feedback)) * 100).toFixed(1)
    : '0'

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-3">
            <MessageCircle className="w-8 h-8 text-primary-600" />
            Chat Analytics
          </h1>
          <p className="text-muted-foreground mt-1">
            Übersicht über Chat-Performance und User-Feedback
          </p>
        </div>

        {/* Time Range Selector */}
        <div className="flex items-center gap-2 bg-gray-100 dark:bg-slate-800 rounded-lg p-1">
          {['24h', '7d', '30d'].map((range) => (
            <button
              key={range}
              onClick={() => setTimeRange(range as any)}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                timeRange === range
                  ? 'bg-white dark:bg-slate-700 shadow-sm'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              {range === '24h' ? '24 Stunden' : range === '7d' ? '7 Tage' : '30 Tage'}
            </button>
          ))}
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <StatCard
          title="Konversationen"
          value={stats?.total_conversations.toLocaleString() || '0'}
          icon={MessageCircle}
          trend="+12% vs. vorherige Periode"
          color="primary"
        />
        <StatCard
          title="Nachrichten"
          value={stats?.total_messages.toLocaleString() || '0'}
          icon={Activity}
          trend="+18% vs. vorherige Periode"
          color="blue"
        />
        <StatCard
          title="Positive Bewertungen"
          value={`${feedbackRate}%`}
          icon={ThumbsUp}
          trend="+5% vs. vorherige Periode"
          color="green"
        />
        <StatCard
          title="Aktive Sessions (24h)"
          value={stats?.active_sessions_24h.toLocaleString() || '0'}
          icon={Users}
          trend="+8% vs. vorherige Periode"
          color="purple"
        />
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Intents */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white dark:bg-slate-800 rounded-lg p-6 shadow-sm border border-gray-200 dark:border-slate-700"
        >
          <div className="flex items-center gap-3 mb-4">
            <BarChart3 className="w-5 h-5 text-primary-600" />
            <h3 className="text-lg font-semibold">Häufigste Anfragen</h3>
          </div>
          <div className="space-y-3">
            {stats?.top_intents?.map((intent, index) => (
              <div key={intent.intent} className="flex items-center gap-3">
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-medium">{intent.intent}</span>
                    <span className="text-xs text-muted-foreground">
                      {intent.count} Mal
                    </span>
                  </div>
                  <div className="h-2 bg-gray-200 dark:bg-slate-700 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-primary-600 to-blue-600 rounded-full"
                      style={{
                        width: `${(intent.count / (stats.top_intents[0]?.count || 1)) * 100}%`
                      }}
                    />
                  </div>
                </div>
              </div>
            )) || (
              <p className="text-sm text-muted-foreground text-center py-4">
                Keine Daten verfügbar
              </p>
            )}
          </div>
        </motion.div>

        {/* Hourly Distribution */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-white dark:bg-slate-800 rounded-lg p-6 shadow-sm border border-gray-200 dark:border-slate-700"
        >
          <div className="flex items-center gap-3 mb-4">
            <Clock className="w-5 h-5 text-primary-600" />
            <h3 className="text-lg font-semibold">Aktivität nach Stunde</h3>
          </div>
          <div className="flex items-end justify-between gap-1 h-40">
            {stats?.hourly_distribution?.map((hour) => {
              const maxCount = Math.max(
                ...(stats.hourly_distribution?.map((h) => h.count) || [1])
              )
              const heightPercentage = (hour.count / maxCount) * 100

              return (
                <div
                  key={hour.hour}
                  className="flex-1 flex flex-col items-center gap-1 group"
                >
                  <div className="relative flex-1 w-full flex items-end">
                    <div
                      className="w-full bg-gradient-to-t from-primary-600 to-blue-600 rounded-t-sm transition-all group-hover:from-primary-500 group-hover:to-blue-500"
                      style={{ height: `${heightPercentage}%` }}
                      title={`${hour.hour}:00 - ${hour.count} Messages`}
                    />
                  </div>
                  <span className="text-xs text-muted-foreground">
                    {hour.hour}
                  </span>
                </div>
              )
            }) || (
              <p className="text-sm text-muted-foreground text-center py-4 w-full">
                Keine Daten verfügbar
              </p>
            )}
          </div>
        </motion.div>
      </div>

      {/* Feedback Details */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="mt-6 bg-white dark:bg-slate-800 rounded-lg p-6 shadow-sm border border-gray-200 dark:border-slate-700"
      >
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-3">
          <ThumbsUp className="w-5 h-5 text-green-600" />
          Feedback-Übersicht
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="text-center p-4 bg-green-50 dark:bg-green-900/10 rounded-lg">
            <ThumbsUp className="w-8 h-8 text-green-600 mx-auto mb-2" />
            <p className="text-2xl font-bold text-green-600">
              {stats?.positive_feedback.toLocaleString() || '0'}
            </p>
            <p className="text-sm text-muted-foreground">Positive Bewertungen</p>
          </div>
          <div className="text-center p-4 bg-red-50 dark:bg-red-900/10 rounded-lg">
            <ThumbsDown className="w-8 h-8 text-red-600 mx-auto mb-2" />
            <p className="text-2xl font-bold text-red-600">
              {stats?.negative_feedback.toLocaleString() || '0'}
            </p>
            <p className="text-sm text-muted-foreground">Negative Bewertungen</p>
          </div>
          <div className="text-center p-4 bg-primary-50 dark:bg-primary-900/10 rounded-lg">
            <BarChart3 className="w-8 h-8 text-primary-600 mx-auto mb-2" />
            <p className="text-2xl font-bold text-primary-600">
              {stats?.avg_messages_per_conversation.toFixed(1) || '0'}
            </p>
            <p className="text-sm text-muted-foreground">Ø Messages pro Chat</p>
          </div>
        </div>
      </motion.div>
    </div>
  )
}

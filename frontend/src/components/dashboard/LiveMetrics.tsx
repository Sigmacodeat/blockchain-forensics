import { useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Activity, Shield, TrendingUp, Users, Database, Zap } from 'lucide-react'
import { useWebSocketEvent } from '@/hooks/useWebSocket'
import api from '@/lib/api'
import { motion } from 'framer-motion'
import MetricSparkline from './MetricSparkline'

interface SystemMetrics {
  total_traces: number
  total_addresses: number
  high_risk_addresses: number
  sanctioned_addresses: number
  traces_today: number
  active_investigations: number
}

export default function LiveMetrics() {
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null)
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date())
  const [previousMetrics, setPreviousMetrics] = useState<SystemMetrics | null>(null)

  // Fetch initial metrics
  const { data: initialMetrics } = useQuery({
    queryKey: ['system-metrics'],
    queryFn: async () => {
      const response = await api.get('/api/v1/admin/stats')
      return response.data as SystemMetrics
    },
    refetchInterval: 30000, // Refresh every 30s
  })

  // Set initial metrics
  useEffect(() => {
    if (initialMetrics) {
      setPreviousMetrics(metrics)
      setMetrics(initialMetrics)
    }
  }, [initialMetrics])

  // Listen for real-time updates via WebSocket
  useWebSocketEvent<{ metrics: SystemMetrics }>(
    'trace.completed',
    () => {
      // Update metrics when traces complete
      if (metrics) {
        setMetrics({
          ...metrics,
          total_traces: (metrics.total_traces || 0) + 1,
          traces_today: (metrics.traces_today || 0) + 1,
        })
        setLastUpdate(new Date())
      }
    },
    true
  )

  // Calculate trends
  const getTrend = (current: number, previous: number | undefined) => {
    if (!previous || previous === 0) return 0
    return ((current - previous) / previous) * 100
  }

  const stats = [
    {
      label: 'Total Traces',
      value: metrics?.total_traces || 0,
      prevValue: previousMetrics?.total_traces,
      icon: Activity,
      gradient: 'from-primary-500 to-primary-700',
      iconColor: 'text-primary-600',
      bgColor: 'bg-primary-50 dark:bg-primary-900/20',
      borderColor: 'border-primary-200 dark:border-primary-800',
    },
    {
      label: 'Traces Today',
      value: metrics?.traces_today || 0,
      prevValue: previousMetrics?.traces_today,
      icon: Zap,
      gradient: 'from-green-500 to-emerald-700',
      iconColor: 'text-green-600',
      bgColor: 'bg-green-50 dark:bg-green-900/20',
      borderColor: 'border-green-200 dark:border-green-800',
    },
    {
      label: 'High-Risk Addresses',
      value: metrics?.high_risk_addresses || 0,
      prevValue: previousMetrics?.high_risk_addresses,
      icon: Shield,
      gradient: 'from-red-500 to-orange-700',
      iconColor: 'text-red-600',
      bgColor: 'bg-red-50 dark:bg-red-900/20',
      borderColor: 'border-red-200 dark:border-red-800',
    },
    {
      label: 'Sanctioned Entities',
      value: metrics?.sanctioned_addresses || 0,
      prevValue: previousMetrics?.sanctioned_addresses,
      icon: TrendingUp,
      gradient: 'from-orange-500 to-amber-700',
      iconColor: 'text-orange-600',
      bgColor: 'bg-orange-50 dark:bg-orange-900/20',
      borderColor: 'border-orange-200 dark:border-orange-800',
    },
    {
      label: 'Total Addresses',
      value: metrics?.total_addresses || 0,
      prevValue: previousMetrics?.total_addresses,
      icon: Database,
      gradient: 'from-purple-500 to-violet-700',
      iconColor: 'text-purple-600',
      bgColor: 'bg-purple-50 dark:bg-purple-900/20',
      borderColor: 'border-purple-200 dark:border-purple-800',
    },
    {
      label: 'Active Investigations',
      value: metrics?.active_investigations || 0,
      prevValue: previousMetrics?.active_investigations,
      icon: Users,
      gradient: 'from-indigo-500 to-blue-700',
      iconColor: 'text-indigo-600',
      bgColor: 'bg-indigo-50 dark:bg-indigo-900/20',
      borderColor: 'border-indigo-200 dark:border-indigo-800',
    },
  ]

  return (
    <div data-tour="metrics">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-3">
          <span className="text-3xl">📊</span>
          Live System Metrics
        </h2>
        <div className="flex items-center gap-2 px-3 py-1.5 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-full">
          <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
          <span className="text-xs font-medium text-green-700 dark:text-green-300">
            Live • {lastUpdate.toLocaleTimeString()}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {stats.map((stat, index) => {
          const Icon = stat.icon
          const trend = getTrend(stat.value, stat.prevValue)
          const isPositive = trend > 0
          const isNegative = trend < 0
          
          return (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.08, type: 'spring', stiffness: 100 }}
              className="group relative overflow-hidden rounded-xl bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-700 p-6 hover:shadow-xl transition-all duration-300 hover:-translate-y-1"
            >
              {/* Gradient Background on Hover */}
              <div className={`absolute inset-0 bg-gradient-to-br ${stat.gradient} opacity-0 group-hover:opacity-5 transition-opacity duration-300`} />
              
              <div className="relative">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <p className="text-xs font-medium text-gray-600 dark:text-gray-400 uppercase tracking-wider mb-2">
                      {stat.label}
                    </p>
                    <div className="flex items-baseline gap-3">
                      <motion.p
                        key={stat.value}
                        initial={{ scale: 1.1, opacity: 0 }}
                        animate={{ scale: 1, opacity: 1 }}
                        className="text-3xl font-bold text-gray-900 dark:text-white"
                      >
                        {stat.value.toLocaleString()}
                      </motion.p>
                      
                      {/* Trend Indicator */}
                      {trend !== 0 && (
                        <motion.span
                          initial={{ opacity: 0, x: -10 }}
                          animate={{ opacity: 1, x: 0 }}
                          className={`flex items-center gap-1 text-xs font-semibold ${
                            isPositive 
                              ? 'text-green-600 dark:text-green-400' 
                              : 'text-red-600 dark:text-red-400'
                          }`}
                        >
                          {isPositive ? '↗' : '↘'}
                          {Math.abs(trend).toFixed(1)}%
                        </motion.span>
                      )}
                    </div>
                  </div>
                  
                  {/* Icon with Gradient */}
                  <div className={`relative ${stat.bgColor} ${stat.borderColor} border p-3 rounded-xl shadow-sm group-hover:shadow-md transition-shadow`}>
                    <Icon className={`w-6 h-6 ${stat.iconColor}`} />
                    <div className={`absolute inset-0 bg-gradient-to-br ${stat.gradient} opacity-0 group-hover:opacity-10 rounded-xl transition-opacity`} />
                  </div>
                </div>
                
                {/* Real Sparkline */}
                <MetricSparkline
                  value={stat.value}
                  prevValue={stat.prevValue}
                  gradient={stat.gradient}
                />
              </div>
            </motion.div>
          )
        })}
      </div>
    </div>
  )
}

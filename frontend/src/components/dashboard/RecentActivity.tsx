import { useQuery } from '@tanstack/react-query'
import { Activity, Clock, CheckCircle, AlertTriangle } from 'lucide-react'
import { Link } from 'react-router-dom'
import LinkLocalized from '@/components/LinkLocalized'
import { formatAddress } from '@/lib/utils'
import { formatDistanceToNow } from 'date-fns'
import { de } from 'date-fns/locale'

interface TraceActivity {
  trace_id: string
  source_address: string
  status: string
  total_nodes: number
  high_risk_count: number
  created_at: string
}

export default function RecentActivity() {
  const { data: recentTraces, isPending, error } = useQuery<TraceActivity[]>({
    queryKey: ['recent-activity'],
    queryFn: async () => {
      const res = await fetch('/api/v1/trace/recent?limit=10')
      if (!res.ok) throw new Error('Failed to load recent traces')
      const data = await res.json()
      return Array.isArray(data) ? data : []
    },
    refetchInterval: 10000, // Refresh every 10s
  })

  if (isPending) {
    return (
      <div className="relative overflow-hidden rounded-xl bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-700 p-6">
        <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
          <Activity className="w-5 h-5 text-primary-600" />
          Recent Activity
        </h2>
        <div className="flex flex-col items-center justify-center py-12">
          <div className="relative">
            <div className="absolute inset-0 bg-primary-500 rounded-full opacity-20 animate-ping"></div>
            <div className="relative animate-spin rounded-full h-12 w-12 border-4 border-gray-200 dark:border-slate-700 border-t-primary-600"></div>
          </div>
          <p className="mt-4 text-sm text-gray-500 dark:text-gray-400">Lade aktuelle Aktivitäten...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="relative overflow-hidden rounded-xl bg-white dark:bg-slate-800 border border-gray-200 dark:border-slate-700 p-6 shadow-lg hover:shadow-xl transition-shadow" data-tour="recent-activity">
      {/* Subtle Gradient Background */}
      <div className="absolute top-0 right-0 w-64 h-64 bg-gradient-to-br from-primary-500/5 to-purple-500/5 rounded-full blur-3xl -mr-32 -mt-32" />
      
      <div className="relative">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
            <div className="relative">
              <Activity className="w-6 h-6 text-primary-600 dark:text-primary-400" />
              <span className="absolute -top-1 -right-1 w-2 h-2 bg-green-500 rounded-full animate-pulse" />
            </div>
            Recent Activity
          </h2>
          <LinkLocalized 
            to="/admin" 
            className="group flex items-center gap-1 px-3 py-1.5 text-sm font-medium text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300 bg-primary-50 dark:bg-primary-900/20 hover:bg-primary-100 dark:hover:bg-primary-900/30 rounded-lg transition-all"
          >
            Alle anzeigen
            <span className="transform group-hover:translate-x-1 transition-transform">→</span>
          </LinkLocalized>
        </div>

        {error && (
          <div className="flex items-center gap-2 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-sm text-red-600 dark:text-red-400 mb-4">
            <AlertTriangle className="w-4 h-4" />
            <span>Fehler beim Laden der Aktivitäten</span>
          </div>
        )}

        {recentTraces && recentTraces.length > 0 ? (
          <div className="space-y-3">
            {recentTraces.slice(0, 5).map((trace, index) => (
              <LinkLocalized
                key={trace.trace_id}
                to={`/trace/${trace.trace_id}`}
                className="group relative block p-4 bg-gradient-to-r from-gray-50 to-gray-50/50 dark:from-slate-700/50 dark:to-slate-700/20 rounded-xl border border-gray-200 dark:border-slate-600 hover:border-primary-300 dark:hover:border-primary-600 hover:shadow-md transition-all duration-300"
                style={{ animationDelay: `${index * 50}ms` }}
              >
                {/* Timeline Connector */}
                {index < recentTraces.length - 1 && (
                  <div className="absolute left-7 top-full w-0.5 h-3 bg-gradient-to-b from-gray-300 to-transparent dark:from-slate-600" />
                )}
                
                <div className="flex items-start justify-between gap-4">
                  <div className="flex items-start gap-3 flex-1">
                    {/* Status Icon with Glow */}
                    <div className="relative flex-shrink-0 mt-0.5">
                      {trace.status === 'completed' ? (
                        <>
                          <div className="absolute inset-0 bg-green-500 rounded-full blur opacity-30 animate-pulse" />
                          <CheckCircle className="relative w-5 h-5 text-green-600 dark:text-green-400" />
                        </>
                      ) : (
                        <>
                          <div className="absolute inset-0 bg-yellow-500 rounded-full blur opacity-30 animate-pulse" />
                          <AlertTriangle className="relative w-5 h-5 text-yellow-600 dark:text-yellow-400" />
                        </>
                      )}
                    </div>
                    
                    <div className="flex-1 min-w-0">
                      {/* Address */}
                      <div className="flex items-center gap-2 mb-2">
                        <span className="font-mono text-sm font-semibold text-gray-900 dark:text-white group-hover:text-primary-600 dark:group-hover:text-primary-400 transition-colors">
                          {formatAddress(trace.source_address, 8)}
                        </span>
                        <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                          trace.status === 'completed' 
                            ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300'
                            : 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300'
                        }`}>
                          {trace.status}
                        </span>
                      </div>
                      
                      {/* Stats */}
                      <div className="flex items-center gap-3 text-xs text-gray-600 dark:text-gray-400">
                        <span className="flex items-center gap-1">
                          <span className="w-1.5 h-1.5 bg-blue-500 rounded-full" />
                          {trace.total_nodes} Nodes
                        </span>
                        {trace.high_risk_count > 0 && (
                          <span className="flex items-center gap-1 px-2 py-0.5 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-full text-red-600 dark:text-red-400 font-semibold">
                            <span className="w-1.5 h-1.5 bg-red-500 rounded-full animate-pulse" />
                            {trace.high_risk_count} High-Risk
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                  
                  {/* Time */}
                  <div className="flex items-center gap-1.5 text-xs text-gray-500 dark:text-gray-400 flex-shrink-0">
                    <Clock className="w-3.5 h-3.5" />
                    <span className="whitespace-nowrap">
                      {formatDistanceToNow(new Date(trace.created_at), {
                        addSuffix: true,
                        locale: de,
                      })}
                    </span>
                  </div>
                </div>
                
                {/* Hover Arrow Indicator */}
                <div className="absolute right-4 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 group-hover:translate-x-1 transition-all duration-300">
                  <span className="text-primary-600 dark:text-primary-400">→</span>
                </div>
              </LinkLocalized>
            ))}
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500 dark:text-gray-400">
            <div className="relative inline-block mb-4">
              <div className="absolute inset-0 bg-gray-300 dark:bg-slate-600 rounded-full blur-xl opacity-20 animate-pulse" />
              <Activity className="relative w-16 h-16 text-gray-300 dark:text-slate-600" />
            </div>
            <p className="text-gray-500 dark:text-gray-400 mb-1 font-medium">Keine aktuellen Aktivitäten</p>
            <p className="text-xs text-gray-400 dark:text-gray-500 mb-6">Starte deinen ersten Trace, um hier Aktivitäten zu sehen</p>
            <LinkLocalized 
              to="/trace" 
              className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-primary-600 to-purple-600 hover:from-primary-700 hover:to-purple-700 text-white font-semibold rounded-xl shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 transition-all duration-300"
            >
              <Activity className="w-4 h-4" />
              Ersten Trace starten
            </LinkLocalized>
          </div>
        )}
      </div>
    </div>
  )
}

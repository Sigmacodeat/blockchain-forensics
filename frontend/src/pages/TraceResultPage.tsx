import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Activity, AlertTriangle, Shield, Download, ExternalLink } from 'lucide-react'
import api from '@/lib/api'
import type { TraceResult } from '@/lib/types'
import TraceGraph from '@/components/TraceGraph'
import TraceProgress from '@/components/TraceProgress'
import LoadingSpinner from '@/components/ui/LoadingSpinner'
import ErrorMessage from '@/components/ui/error-message'
import ExportModal from '@/components/modals/ExportModal'
import ReportModal from '@/components/modals/ReportModal'
import { useTraceProgress } from '@/hooks/useTraceProgress'
import { formatAddress } from '@/lib/utils'
import { Button } from '@/components/ui/button'

export default function TraceResultPage() {
  const { t } = useTranslation()
  const { traceId } = useParams<{ traceId: string }>()
  const [isExportModalOpen, setIsExportModalOpen] = useState(false)
  const [isReportModalOpen, setIsReportModalOpen] = useState(false)

  // Real-time progress updates
  const { progress, isCompleted: wsCompleted, result: wsResult } = useTraceProgress(traceId)

  const { data: trace, isPending, error, refetch } = useQuery({
    queryKey: ['trace', traceId],
    queryFn: async () => {
      const response = await api.get<TraceResult>(`/api/v1/trace/${traceId}`)
      return response.data
    },
    enabled: !!traceId,
  })

  // Refetch when WebSocket signals completion
  useEffect(() => {
    if (wsCompleted && wsResult) {
      refetch()
    }
  }, [wsCompleted, wsResult, refetch])

  if (isPending) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <LoadingSpinner size="lg" />
        <p className="text-center text-gray-600 mt-4">{t('trace.result.loading', 'Lade Trace-Ergebnisse...')}</p>
      </div>
    )
  }

  if (error || !trace) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <ErrorMessage
          title={t('trace.result.error_title', 'Fehler beim Laden')}
          message={(error as any)?.response?.data?.detail || t('trace.result.not_found', 'Trace nicht gefunden')}
        />
      </div>
    )
  }

  // Show progress if trace is not yet completed
  const showProgress = progress && !trace?.completed

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Real-Time Progress */}
      {showProgress && (
        <div className="mb-6">
          <TraceProgress progress={progress} isCompleted={false} />
        </div>
      )}

      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <Activity className="w-8 h-8 text-primary-600" />
              <h1 className="text-3xl font-bold text-gray-900">{t('trace.result.title', 'Trace Results')}</h1>
            </div>
            <p className="text-gray-600 font-mono text-sm">ID: {traceId}</p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => setIsExportModalOpen(true)} className="flex items-center gap-2">
              <Download className="w-4 h-4" />
              {t('trace.result.export', 'Export')}
            </Button>
            <Button onClick={() => setIsReportModalOpen(true)} className="flex items-center gap-2">
              <ExternalLink className="w-4 h-4" />
              {t('trace.result.report', 'Report')}
            </Button>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="card p-4">
            <p className="text-sm text-gray-600 mb-1">{t('trace.result.total_nodes', 'Total Nodes')}</p>
            <p className="text-2xl font-bold text-gray-900">{trace.total_nodes}</p>
          </div>
          <div className="card p-4">
            <p className="text-sm text-gray-600 mb-1">{t('trace.result.total_edges', 'Total Edges')}</p>
            <p className="text-2xl font-bold text-gray-900">{trace.total_edges}</p>
          </div>
          <div className="card p-4">
            <p className="text-sm text-gray-600 mb-1">{t('trace.result.max_hop', 'Max Hop')}</p>
            <p className="text-2xl font-bold text-gray-900">{trace.max_hop_reached}</p>
          </div>
          <div className="card p-4">
            <p className="text-sm text-gray-600 mb-1">{t('trace.result.high_risk', 'High Risk')}</p>
            <p className="text-2xl font-bold text-danger-600">
              {trace.high_risk_addresses.length}
            </p>
          </div>
        </div>
      </div>

      {/* Graph Visualization */}
      <div className="card p-6 mb-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">{t('trace.result.flow_graph', 'Transaction Flow Graph')}</h2>
        <TraceGraph trace={trace} />
      </div>

      {/* High-Risk Addresses */}
      {trace.high_risk_addresses.length > 0 && (
        <div className="card p-6 mb-6 border-danger-200 bg-danger-50">
          <div className="flex items-center gap-2 mb-4">
            <AlertTriangle className="w-5 h-5 text-danger-600" />
            <h2 className="text-lg font-semibold text-danger-900">{t('trace.result.high_risk_title', 'High-Risk Addresses')} ({trace.high_risk_addresses.length})</h2>
          </div>
          <div className="space-y-2">
            {trace.high_risk_addresses.slice(0, 10).map((address) => {
              const node = trace.nodes[address]
              return (
                <div
                  key={address}
                  className="flex items-center justify-between p-3 bg-white rounded-lg"
                >
                  <div>
                    <p className="font-mono text-sm text-gray-900">
                      {formatAddress(address, 8)}
                    </p>
                    <div className="flex gap-2 mt-1">
                      {node?.labels.map((label) => (
                        <span
                          key={label}
                          className="px-2 py-0.5 bg-danger-100 text-danger-800 text-xs rounded"
                        >
                          {label}
                        </span>
                      ))}
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-gray-600">{t('trace.result.taint', 'Taint')}</p>
                    <p className="font-semibold text-danger-600">
                      {node ? (node.taint_received * 100).toFixed(2) : '0'}%
                    </p>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Sanctioned Addresses */}
      {trace.sanctioned_addresses.length > 0 && (
        <div className="card p-6 mb-6 border-red-300 bg-red-50">
          <div className="flex items-center gap-2 mb-4">
            <Shield className="w-5 h-5 text-red-600" />
            <h2 className="text-lg font-semibold text-red-900">{t('trace.result.sanctioned_title', 'OFAC Sanctioned Entities')} ({trace.sanctioned_addresses.length})</h2>
          </div>
          <p className="text-sm text-red-800 mb-4">{t('trace.result.sanctioned_warning', '⚠️ Diese Adressen stehen auf OFAC-Sanktionslisten. Interaktionen sind illegal!')}</p>
          <div className="space-y-2">
            {trace.sanctioned_addresses.map((address) => (
              <div
                key={address}
                className="p-3 bg-white rounded-lg font-mono text-sm text-red-900"
              >
                {formatAddress(address, 8)}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Metadata */}
      <div className="card p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">{t('trace.result.details', 'Trace Details')}</h2>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <p className="text-gray-600">{t('trace.result.source', 'Source Address')}</p>
            <p className="font-mono text-gray-900">{formatAddress(trace.source_address)}</p>
          </div>
          <div>
            <p className="text-gray-600">{t('trace.result.direction', 'Direction')}</p>
            <p className="text-gray-900 capitalize">{trace.direction}</p>
          </div>
          <div>
            <p className="text-gray-600">{t('trace.result.taint_model', 'Taint Model')}</p>
            <p className="text-gray-900 capitalize">{trace.taint_model}</p>
          </div>
          <div>
            <p className="text-gray-600">{t('trace.result.exec_time', 'Execution Time')}</p>
            <p className="text-gray-900">{trace.execution_time_seconds?.toFixed(2)}s</p>
          </div>
        </div>
      </div>

      {/* Modals */}
      <ExportModal
        isOpen={isExportModalOpen}
        onClose={() => setIsExportModalOpen(false)}
        trace={trace}
      />
      <ReportModal
        isOpen={isReportModalOpen}
        onClose={() => setIsReportModalOpen(false)}
        trace={trace}
      />
    </div>
  )
}

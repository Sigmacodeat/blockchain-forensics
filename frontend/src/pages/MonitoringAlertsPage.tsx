import { useEffect, useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useLocation } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'

interface AlertItem {
  id: string
  rule_id: string
  entity_type: string
  entity_id: string
  chain: string
  severity: 'low' | 'medium' | 'high' | 'critical'
  status: 'open' | 'assigned' | 'snoozed' | 'closed'
  assignee?: string | null
  first_seen_at: string
  last_seen_at: string
  hits: number
  context?: Record<string, any> | null
}

interface AlertEventItem {
  id: number
  alert_id: string
  created_at: string
  actor?: string | null
  type: string
  payload?: Record<string, any> | null
}

export default function MonitoringAlertsPage() {
  const { t } = useTranslation()
  const qc = useQueryClient()
  const location = useLocation()
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [severityFilter, setSeverityFilter] = useState<string>('')
  const [source, setSource] = useState<'persisted'|'realtime'>('persisted')
  const [query, setQuery] = useState<string>('')
  const [debouncedQuery, setDebouncedQuery] = useState<string>('')
  const [page, setPage] = useState<number>(1)
  const pageSize = 20
  const [selectedAlert, setSelectedAlert] = useState<AlertItem | null>(null)
  const [sortKey, setSortKey] = useState<keyof AlertItem>('last_seen_at')
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc')
  const [toast, setToast] = useState<{ visible: boolean; message: string }>({ visible: false, message: '' })

  const { data: alerts, isPending, refetch } = useQuery<AlertItem[]>({
    queryKey: ['monitorAlerts', source, statusFilter, severityFilter],
    queryFn: async () => {
      const params = new URLSearchParams()
      // Persisted supports status + severity; realtime nur severity
      if (source === 'persisted' && statusFilter) params.set('status', statusFilter)
      if (severityFilter) params.set('severity', severityFilter)
      const base = source === 'persisted' ? '/api/v1/monitor/alerts' : '/api/v1/monitor/alerts/realtime'
      const url = `${base}${params.toString() ? `?${params.toString()}` : ''}`
      const res = await api.get<AlertItem[]>(url)
      return res.data
    },
    staleTime: 10_000,
  })

  // Mutations for KPI annotations
  const setDisposition = useMutation({
    mutationFn: async (payload: { id: string; disposition: 'false_positive' | 'true_positive' | 'benign' | 'unknown' }) => {
      const res = await api.post(`/api/v1/alerts/disposition/${payload.id}`, { disposition: payload.disposition })
      return res.data
    },
    onSuccess: () => setToast({ visible: true, message: t('monitor.alerts.toasts.disposition_set', 'Disposition gesetzt') }),
    onError: () => setToast({ visible: true, message: t('monitor.alerts.toasts.disposition_failed', 'Disposition fehlgeschlagen') })
  })

  const setEventTime = useMutation({
    mutationFn: async (payload: { id: string; event_time: string }) => {
      const res = await api.post(`/api/v1/alerts/event-time/${payload.id}`, { event_time: payload.event_time })
      return res.data
    },
    onSuccess: () => setToast({ visible: true, message: t('monitor.alerts.toasts.event_time_set', 'Eventzeit gesetzt') }),
    onError: () => setToast({ visible: true, message: t('monitor.alerts.toasts.event_time_failed', 'Eventzeit fehlgeschlagen') })
  })

  // Initialize filters from query params
  useEffect(() => {
    const params = new URLSearchParams(location.search)
    const qStatus = params.get('status')
    const qSeverity = params.get('severity')
    const qSource = params.get('source') as 'persisted' | 'realtime' | null
    if (qStatus) setStatusFilter(qStatus)
    if (qSeverity) setSeverityFilter(qSeverity)
    if (qSource === 'persisted' || qSource === 'realtime') setSource(qSource)
    // Note: ageBucket currently nicht serverseitig filterbar; könnte später ergänzt werden
  }, [location.search])

  const updateMutation = useMutation({
    mutationFn: async (payload: { id: string; status?: string; assignee?: string; note?: string }) => {
      const res = await api.patch(`/api/v1/monitor/alerts/${payload.id}`, {
        status: payload.status,
        assignee: payload.assignee,
        note: payload.note,
      })
      return res.data
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['monitorAlerts'] })
      refetch()
    },
  })

  const { data: events } = useQuery<AlertEventItem[]>({
    queryKey: ['monitorAlertEvents', selectedAlert?.id],
    queryFn: async () => {
      if (!selectedAlert) return []
      const res = await api.get(`/api/v1/monitor/alerts/${selectedAlert.id}/events`)
      return res.data
    },
    enabled: !!selectedAlert,
  })

  const filtered = useMemo(() => {
    let list = alerts || []
    // rule_id filter from URL (client-side) if present
    const params = new URLSearchParams(location.search)
    const qRule = params.get('rule_id')?.trim()
    if (qRule) {
      const ruleLc = qRule.toLowerCase()
      list = list.filter(a => a.rule_id.toLowerCase().includes(ruleLc))
    }
    if (!debouncedQuery.trim()) return list
    const q = debouncedQuery.trim().toLowerCase()
    return list.filter(a =>
      a.rule_id.toLowerCase().includes(q) || a.entity_id.toLowerCase().includes(q)
    )
  }, [alerts, debouncedQuery, location.search])
  
  // Debounce Query Input
  useEffect(() => {
    const t = setTimeout(() => setDebouncedQuery(query), 300)
    return () => clearTimeout(t)
  }, [query])

  const sorted = useMemo(() => {
    const list = [...filtered]
    list.sort((a, b) => {
      const va = (a[sortKey] as any) ?? ''
      const vb = (b[sortKey] as any) ?? ''
      if (typeof va === 'number' && typeof vb === 'number') {
        return sortDir === 'asc' ? va - vb : vb - va
      }
      const sa = String(va)
      const sb = String(vb)
      return sortDir === 'asc' ? sa.localeCompare(sb) : sb.localeCompare(sa)
    })
    return list
  }, [filtered, sortKey, sortDir])

  const totalPages = Math.max(1, Math.ceil(filtered.length / pageSize))
  const pageItems = useMemo(() => {
    const start = (page - 1) * pageSize
    return sorted.slice(start, start + pageSize)
  }, [sorted, page])

  const onSort = (key: keyof AlertItem) => {
    if (sortKey === key) setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'))
    else { setSortKey(key); setSortDir('desc') }
  }

  const exportCsv = (rows: AlertItem[]) => {
    const headers = ['id','rule_id','matched_rule','entity_type','entity_id','chain','severity','status','hits','first_seen_at','last_seen_at']
    const lines = [headers.join(',')]
    for (const r of rows) {
      const matchedRule = (r.context as any)?.matched_rule ?? (r.context as any)?.metadata?.matched_rule ?? ''
      const vals = [r.id, r.rule_id, matchedRule, r.entity_type, r.entity_id, r.chain, r.severity, r.status, String(r.hits), r.first_seen_at, r.last_seen_at]
      lines.push(vals.map(v => `"${String(v).replace(/"/g,'""')}"`).join(','))
    }
    const blob = new Blob([lines.join('\n')], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `alerts_page_${page}.csv`
    a.click()
    URL.revokeObjectURL(url)
  }

  const downloadServerCsv = async () => {
    try {
      const params = new URLSearchParams()
      if (statusFilter) params.set('status', statusFilter)
      if (severityFilter) params.set('severity', severityFilter)
      if (debouncedQuery) params.set('q', debouncedQuery)
      params.set('limit', '10000')
      const url = `/api/v1/monitor/alerts/export${params.toString() ? `?${params.toString()}` : ''}`
      const res = await fetch(url)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const blob = await res.blob()
      const href = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = href
      a.download = 'alerts.csv'
      a.click()
      URL.revokeObjectURL(href)
      setToast({ visible: true, message: t('monitor.alerts.toasts.export_started', 'Server-Export gestartet') })
    } catch (e) {
      setToast({ visible: true, message: t('monitor.alerts.toasts.export_failed', 'Server-Export fehlgeschlagen') })
    } finally {
      setTimeout(() => setToast({ visible: false, message: '' }), 1200)
    }
  }

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">{t('monitor.alerts.title', 'Monitoring Alerts')}</h1>
        <p className="text-gray-600">{t('monitor.alerts.subtitle', 'Realtime-Regeln und persistierte Alerts (KYT)')}</p>
      </div>

      <div className="bg-white rounded-lg shadow p-4 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          <div>
            <label className="block text-sm text-gray-600 mb-1">{t('monitor.alerts.filters.source', 'Quelle')}</label>
            <select className="input" value={source} onChange={(e) => { setSource(e.target.value as 'persisted'|'realtime'); setPage(1) }}>
              <option value="persisted">{t('monitor.alerts.filters.source_persisted', 'Persistiert (KYT)')}</option>
              <option value="realtime">{t('monitor.alerts.filters.source_realtime', 'Realtime (Alert-Engine)')}</option>
            </select>
          </div>
          <div>
            <label className="block text-sm text-gray-600 mb-1">{t('monitor.alerts.filters.status', 'Status')}</label>
            <select className="input" value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} disabled={source==='realtime'}>
              <option value="">{t('monitor.alerts.filters.all', '(alle)')}</option>
              <option value="open">{t('monitor.alerts.status.open', 'open')}</option>
              <option value="assigned">{t('monitor.alerts.status.assigned', 'assigned')}</option>
              <option value="snoozed">{t('monitor.alerts.status.snoozed', 'snoozed')}</option>
              <option value="closed">{t('monitor.alerts.status.closed', 'closed')}</option>
            </select>
          </div>
          <div>
            <label className="block text-sm text-gray-600 mb-1">{t('monitor.alerts.filters.severity', 'Severity')}</label>
            <select className="input" value={severityFilter} onChange={(e) => setSeverityFilter(e.target.value)}>
              <option value="">{t('monitor.alerts.filters.all', '(alle)')}</option>
              <option value="low">{t('monitor.alerts.severity.low', 'low')}</option>
              <option value="medium">{t('monitor.alerts.severity.medium', 'medium')}</option>
              <option value="high">{t('monitor.alerts.severity.high', 'high')}</option>
              <option value="critical">{t('monitor.alerts.severity.critical', 'critical')}</option>
            </select>
          </div>
          <div>
            <label className="block text-sm text-gray-600 mb-1">{t('monitor.alerts.filters.search_label', 'Suche (rule_id / entity_id)')}</label>
            <input className="input" placeholder={t('monitor.alerts.filters.search_placeholder', 'Suche...')} value={query} onChange={(e) => { setPage(1); setQuery(e.target.value) }} />
          </div>
          <div className="flex items-end">
            <button className="btn-secondary" onClick={() => { setStatusFilter(''); setSeverityFilter(''); }}>{t('monitor.alerts.actions.reset', 'Zurücksetzen')}</button>
          </div>
          <div className="flex items-end justify-end">
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <button className="btn-secondary" disabled={page <= 1} onClick={() => setPage((p) => Math.max(1, p - 1))}>{t('monitor.alerts.pagination.prev', 'Zurück')}</button>
              <span>{t('monitor.alerts.pagination.page', 'Seite')} {page} / {totalPages}</span>
              <button className="btn-secondary" disabled={page >= totalPages} onClick={() => setPage((p) => Math.min(totalPages, p + 1))}>{t('monitor.alerts.pagination.next', 'Weiter')}</button>
              <button className="btn-primary" disabled={pageItems.length === 0} title={pageItems.length === 0 ? t('monitor.alerts.csv.no_page_data', 'Keine Daten auf dieser Seite') : t('monitor.alerts.csv.export_page_title', 'CSV der Seite exportieren')} onClick={() => exportCsv(pageItems)}>{t('monitor.alerts.csv.export_page', 'CSV Export (Seite)')}</button>
              <button className="btn-primary" disabled={filtered.length === 0} title={filtered.length === 0 ? t('monitor.alerts.csv.no_filtered_data', 'Keine Daten gefiltert') : t('monitor.alerts.csv.export_all_title', 'CSV aller gefilterten Zeilen (Server) exportieren')} onClick={downloadServerCsv}>{t('monitor.alerts.csv.export_all', 'CSV Export (Alle)')}</button>
            </div>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow">
        <div className="overflow-x-auto">
          <table className="min-w-full">
            <thead>
              <tr className="bg-gray-50 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                <th className="px-4 py-3 cursor-pointer" onClick={() => onSort('id')}>ID {sortKey==='id' ? (sortDir==='asc'?'▲':'▼') : ''}</th>
                <th className="px-4 py-3 cursor-pointer" onClick={() => onSort('rule_id')}>Rule {sortKey==='rule_id' ? (sortDir==='asc'?'▲':'▼') : ''}</th>
                <th className="px-4 py-3">Policy-Regel</th>
                <th className="px-4 py-3 cursor-pointer" onClick={() => onSort('entity_id')}>Entity {sortKey==='entity_id' ? (sortDir==='asc'?'▲':'▼') : ''}</th>
                <th className="px-4 py-3 cursor-pointer" onClick={() => onSort('chain')}>Chain {sortKey==='chain' ? (sortDir==='asc'?'▲':'▼') : ''}</th>
                <th className="px-4 py-3 cursor-pointer" onClick={() => onSort('severity')}>Severity {sortKey==='severity' ? (sortDir==='asc'?'▲':'▼') : ''}</th>
                <th className="px-4 py-3 cursor-pointer" onClick={() => onSort('status')}>Status {sortKey==='status' ? (sortDir==='asc'?'▲':'▼') : ''}</th>
                <th className="px-4 py-3 cursor-pointer" onClick={() => onSort('hits')}>Hits {sortKey==='hits' ? (sortDir==='asc'?'▲':'▼') : ''}</th>
                <th className="px-4 py-3 cursor-pointer" onClick={() => onSort('last_seen_at')}>Zeit {sortKey==='last_seen_at' ? (sortDir==='asc'?'▲':'▼') : ''}</th>
                <th className="px-4 py-3">Aktionen</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {isPending && (
                <tr><td className="px-4 py-3 text-sm" colSpan={9}>{t('monitor.alerts.loading', 'Lade Alerts...')}</td></tr>
              )}
              {!isPending && filtered.length === 0 && (
                <tr><td className="px-4 py-6 text-sm text-gray-500" colSpan={9}>{t('monitor.alerts.empty', 'Keine Alerts gefunden')}</td></tr>
              )}
              {pageItems.map((a) => (
                <tr key={a.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-sm font-mono truncate max-w-[180px]">{a.id}</td>
                  <td className="px-4 py-3 text-sm">{a.rule_id}</td>
                  <td className="px-4 py-3 text-sm">{(a.context as any)?.matched_rule ?? (a.context as any)?.metadata?.matched_rule ?? ''}</td>
                  <td className="px-4 py-3 text-sm">{a.entity_type}:{' '}{a.entity_id}</td>
                  <td className="px-4 py-3 text-sm">{a.chain}</td>
                  <td className="px-4 py-3 text-sm">
                    <span className={`px-2 py-1 rounded text-xs ${a.severity === 'critical' ? 'bg-red-100 text-red-700' : a.severity === 'high' ? 'bg-orange-100 text-orange-700' : a.severity === 'medium' ? 'bg-yellow-100 text-yellow-700' : 'bg-green-100 text-green-700'}`}>{a.severity}</span>
                  </td>
                  <td className="px-4 py-3 text-sm">{a.status}</td>
                  <td className="px-4 py-3 text-sm">{a.hits}</td>
                  <td className="px-4 py-3 text-xs text-gray-500">
                    <div>{t('monitor.alerts.table.first', 'first')}: {new Date(a.first_seen_at).toLocaleString()}</div>
                    <div>{t('monitor.alerts.table.last', 'last')}: {new Date(a.last_seen_at).toLocaleString()}</div>
                  </td>
                  <td className="px-4 py-3 text-sm">
                    <div className="flex gap-2">
                      <button className="btn-secondary" onClick={() => setSelectedAlert(a)} title={t('monitor.alerts.actions.details_title', 'Details anzeigen')}>{t('monitor.alerts.actions.details', 'Details')}</button>
                      <button className="btn-secondary" title={t('monitor.alerts.actions.copy_alert_id_title', 'Alert-ID kopieren')} onClick={async () => {
                        try { await navigator.clipboard.writeText(a.id); setToast({ visible: true, message: t('monitor.alerts.toasts.id_copied', 'ID kopiert') }) } catch { setToast({ visible: true, message: t('monitor.alerts.toasts.copy_failed', 'Kopieren fehlgeschlagen') }) } finally { setTimeout(() => setToast({ visible: false, message: '' }), 1200) }
                      }}>{t('monitor.alerts.actions.copy_id', 'Copy ID')}</button>
                      <button className="btn-secondary" title={t('monitor.alerts.actions.copy_rule_id_title', 'Rule-ID kopieren')} onClick={async () => {
                        try { await navigator.clipboard.writeText(a.rule_id); setToast({ visible: true, message: t('monitor.alerts.toasts.rule_copied', 'Rule kopiert') }) } catch { setToast({ visible: true, message: t('monitor.alerts.toasts.copy_failed', 'Kopieren fehlgeschlagen') }) } finally { setTimeout(() => setToast({ visible: false, message: '' }), 1200) }
                      }}>{t('monitor.alerts.actions.copy_rule', 'Copy Rule')}</button>
                      <button className="btn-secondary" title={t('monitor.alerts.actions.copy_entity_id_title', 'Entity-ID kopieren')} onClick={async () => {
                        try { await navigator.clipboard.writeText(a.entity_id); setToast({ visible: true, message: t('monitor.alerts.toasts.entity_copied', 'Entity kopiert') }) } catch { setToast({ visible: true, message: t('monitor.alerts.toasts.copy_failed', 'Kopieren fehlgeschlagen') }) } finally { setTimeout(() => setToast({ visible: false, message: '' }), 1200) }
                      }}>{t('monitor.alerts.actions.copy_entity', 'Copy Entity')}</button>
                      {a.status !== 'closed' && (
                        <button className="btn-primary" title={t('monitor.alerts.actions.close_title', 'Alert schließen')} onClick={() => updateMutation.mutate({ id: a.id, status: 'closed' })}>{t('monitor.alerts.actions.close', 'Close')}</button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {toast.visible && (
        <div className="fixed bottom-6 right-6 bg-gray-900 text-white text-sm px-4 py-2 rounded shadow-lg z-50" role="status" aria-live="polite">
          {toast.message}
        </div>
      )}

      {/* Drawer/Modal */}
      {selectedAlert && (
        <div className="fixed inset-0 bg-black/40 flex items-end md:items-center justify-center z-50" onClick={() => setSelectedAlert(null)}>
          <div className="bg-white w-full md:max-w-3xl rounded-t-2xl md:rounded-2xl shadow-xl p-6" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">{t('monitor.alerts.modal.title', 'Alert Details')}</h3>
              <button className="text-gray-500 hover:text-gray-700" onClick={() => setSelectedAlert(null)}>✕</button>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <div className="text-sm text-gray-500">{t('monitor.alerts.modal.alert_id', 'Alert ID')}</div>
                <div className="font-mono text-sm">{selectedAlert.id}</div>
              </div>
              <div>
                <div className="text-sm text-gray-500">{t('monitor.alerts.modal.rule_id', 'Rule ID')}</div>
                <div className="font-mono text-sm">{selectedAlert.rule_id}</div>
              </div>
              <div>
                <div className="text-sm text-gray-500">{t('monitor.alerts.modal.entity', 'Entity')}</div>
                <div className="text-sm">{selectedAlert.entity_type}: {selectedAlert.entity_id}</div>
              </div>
              <div>
                <div className="text-sm text-gray-500">{t('monitor.alerts.modal.chain', 'Chain')}</div>
                <div className="text-sm">{selectedAlert.chain}</div>
              </div>
              <div>
                <div className="text-sm text-gray-500">{t('monitor.alerts.modal.severity', 'Severity')}</div>
                <div className="text-sm">{selectedAlert.severity}</div>
              </div>
              <div className="md:col-span-2">
                <div className="text-sm text-gray-500">{t('monitor.alerts.modal.context', 'Context')}</div>
                <pre className="text-xs bg-gray-50 border p-3 rounded overflow-auto max-h-48">{JSON.stringify(selectedAlert.context, null, 2)}</pre>
              </div>
            </div>

            <div className="mt-6">
              <h4 className="font-semibold mb-2 text-sm">{t('monitor.alerts.audit.title', 'Audit Trail')}</h4>
              {!events || events.length === 0 ? (
                <div className="text-sm text-gray-500">{t('monitor.alerts.audit.empty', 'Keine Events')}</div>
              ) : (
                <div className="border rounded divide-y max-h-64 overflow-auto">
                  {events.map((ev) => (
                    <div key={ev.id} className="p-3 text-sm flex items-start gap-3">
                      <div className="text-xs text-gray-500 w-40">{new Date(ev.created_at).toLocaleString()}</div>
                      <div>
                        <div className="font-mono text-xs text-gray-600">{ev.type}</div>
                        {ev.payload && (
                          <pre className="text-xs bg-gray-50 border p-2 rounded overflow-auto">{JSON.stringify(ev.payload, null, 2)}</pre>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* KPI Annotation Actions */}
            <div className="mt-6">
              <h4 className="font-semibold mb-2 text-sm">{t('monitor.alerts.kpi.title', 'KPI-Annotationen')}</h4>
              <div className="flex flex-wrap gap-2">
                <button
                  className="btn-secondary"
                  onClick={() => selectedAlert && setDisposition.mutate({ id: selectedAlert.id, disposition: 'false_positive' })}
                >
                  {t('monitor.alerts.kpi.false_positive', 'Als False Positive markieren')}
                </button>
                <button
                  className="btn-secondary"
                  onClick={() => selectedAlert && setDisposition.mutate({ id: selectedAlert.id, disposition: 'true_positive' })}
                >
                  {t('monitor.alerts.kpi.true_positive', 'Als True Positive markieren')}
                </button>
                <button
                  className="btn-secondary"
                  title={t('monitor.alerts.kpi.event_time_title', 'Eventzeit = first_seen_at')}
                  onClick={() => selectedAlert && setEventTime.mutate({ id: selectedAlert.id, event_time: selectedAlert.first_seen_at })}
                >
                  {t('monitor.alerts.kpi.event_time_set', 'Eventzeit setzen (first_seen_at)')}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

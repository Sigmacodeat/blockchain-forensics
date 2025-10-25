import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useMutation } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import LinkLocalized from '@/components/LinkLocalized'
import { useLocalePath } from '@/hooks/useLocalePath'
import { Activity, AlertCircle } from 'lucide-react'
import api from '@/lib/api'
import type { TraceRequest, TraceStatusResponse } from '@/lib/types'
import { toast } from '@/lib/toast'
import { Button } from '@/components/ui/button'

export default function TracePage() {
  const navigate = useNavigate()
  const { t } = useTranslation()
  const localePath = useLocalePath()
  const [remaining, setRemaining] = useState<number | null>(null)
  const [loadingRemaining, setLoadingRemaining] = useState(false)
  const [insufficientCredits, setInsufficientCredits] = useState(false)
  const [tenantPlan, setTenantPlan] = useState<string>('')
  const [formData, setFormData] = useState<TraceRequest>({
    source_address: '',
    direction: 'forward',
    max_depth: 5,
    max_nodes: 1000,
    taint_model: 'proportional',
    min_taint_threshold: 0.01,
    save_to_graph: true,
  })

  // Agent-Tool Trace (ohne Persist in /trace/start)
  const [agentPayload, setAgentPayload] = useState({
    address: '',
    max_depth: 5,
    direction: 'forward',
    from_timestamp: '',
    to_timestamp: '',
    min_taint_threshold: 0.01,
    max_nodes: 1000,
    enable_native: true,
    enable_token: true,
    enable_bridge: true,
    enable_utxo: true,
    native_decay: 1.0,
    token_decay: 1.0,
    bridge_decay: 0.9,
    utxo_decay: 1.0,
  })

  const agentTraceMutation = useMutation({
    mutationFn: async (payload: typeof agentPayload) => {
      const body = {
        ...payload,
        // leere Strings nicht senden
        from_timestamp: payload.from_timestamp || undefined,
        to_timestamp: payload.to_timestamp || undefined,
      }
      const res = await api.post('/api/v1/agent/tools/trace-address', body)
      return res.data
    },
  })

  const traceMutation = useMutation({
    mutationFn: async (data: TraceRequest) => {
      const response = await api.post<TraceStatusResponse>(`/api/v1/trace/start`, data)
      return response.data
    },
    onSuccess: (data) => {
      navigate(`/trace/${data.trace_id}`)
    },
    onError: (err: any) => {
      if (err?.response?.status === 402) {
        // hint upgrade
        setInsufficientCredits(true)
        // no toast util here; rely on inline banner below
        try { toast.error('Nicht genügend Credits für den Trace. Bitte Plan upgraden.') } catch {}
      }
    }
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    traceMutation.mutate(formData)
  }

  useEffect(() => {
    // Load current tenant plan once
    let ignore = false
    async function loadPlan() {
      try {
        const r = await fetch('/api/v1/billing/tenant/plan')
        if (!r.ok) throw new Error('failed')
        const j = await r.json()
        if (!ignore) setTenantPlan(j.plan_id || '')
      } catch { if (!ignore) setTenantPlan('') }
    }
    loadPlan()
    return () => { ignore = true }
  }, [])

  useEffect(() => {
    let ignore = false
    async function loadRemaining() {
      try {
        setLoadingRemaining(true)
        const res = await fetch(`/api/v1/billing/usage/remaining`)
        if (!res.ok) throw new Error('failed')
        const r = await res.json()
        if (!ignore) setRemaining(r.unlimited ? null : r.remaining)
      } catch {
        if (!ignore) setRemaining(null)
      } finally {
        if (!ignore) setLoadingRemaining(false)
      }
    }
    loadRemaining()
    return () => { ignore = true }
  }, [tenantPlan])

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {insufficientCredits && (
        <div className="mb-4 p-4 border-2 border-amber-400 bg-amber-50 dark:bg-amber-950 dark:border-amber-600 rounded-lg text-sm">
          <p className="text-amber-900 dark:text-amber-200 font-medium">
            {t('trace.banner.insufficient', 'Nicht genügend Credits für den Trace.')} <LinkLocalized className="underline hover:text-amber-700 dark:hover:text-amber-100" to="/pricing">{t('trace.banner.upgrade', 'Jetzt Plan upgraden')}</LinkLocalized>.
          </p>
        </div>
      )}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-4">
          <Activity className="w-8 h-8 text-primary-600 dark:text-primary-400" />
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">{t('trace.header.title', 'Transaction Tracing')}</h1>
        </div>
        <p className="text-gray-600 dark:text-gray-400">{t('trace.header.subtitle', 'Rekursives N-Hop-Tracing mit Taint-Propagation für forensische Geldfluss-Verfolgung')}</p>
      </div>

      <div className="card p-6 bg-card border border-border">
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Tenant Plan Display */}
          <div className="flex flex-wrap items-center gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">{t('trace.plan.current', 'Aktueller Tenant-Plan')}</label>
              <div className="input w-64 bg-gray-50 dark:bg-slate-700 text-gray-700 dark:text-gray-200 border-gray-200 dark:border-slate-600">{tenantPlan || '—'}</div>
            </div>
            <div className="mt-7 text-sm text-gray-600 dark:text-gray-400">
              {loadingRemaining ? t('trace.plan.loading', 'Lade Credits…') : (remaining===null ? t('trace.plan.unlimited', 'Credits: Unlimited') : `${t('trace.plan.remaining', 'Credits verfügbar')}: ${remaining}`)}
            </div>
            <Button type="button" variant="outline" className="mt-7" onClick={()=>navigate(localePath('/pricing'))}>{t('trace.plan.to_pricing', 'Zu Pricing')}</Button>
          </div>
          {/* Source Address */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              {t('trace.form.source', 'Quell-Adresse *')}
            </label>
            <input
              type="text"
              className="input bg-white dark:bg-slate-700 border-gray-300 dark:border-slate-600 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500"
              placeholder={t('trace.form.source_ph', '0x...')}
              value={formData.source_address}
              onChange={(e) => setFormData({ ...formData, source_address: e.target.value })}
              required
            />
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">{t('trace.form.source_help', 'Ethereum-Adresse, von der aus getraced werden soll')}</p>
          </div>

          {/* Direction */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">{t('trace.form.direction', 'Trace-Richtung')}</label>
            <select
              className="input bg-white dark:bg-slate-700 border-gray-300 dark:border-slate-600 text-gray-900 dark:text-white"
              value={formData.direction}
              onChange={(e) => setFormData({ ...formData, direction: e.target.value as any })}
            >
              <option value="forward">{t('trace.form.dir_forward', 'Forward (Ausgänge verfolgen)')}</option>
              <option value="backward">{t('trace.form.dir_backward', 'Backward (Eingänge verfolgen)')}</option>
              <option value="both">{t('trace.form.dir_both', 'Both (Beide Richtungen)')}</option>
            </select>
          </div>

          {/* Taint Model */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">{t('trace.form.taint_model', 'Taint-Modell')}</label>
            <select
              className="input bg-white dark:bg-slate-700 border-gray-300 dark:border-slate-600 text-gray-900 dark:text-white"
              value={formData.taint_model}
              onChange={(e) => setFormData({ ...formData, taint_model: e.target.value as any })}
            >
              <option value="proportional">{t('trace.form.model_proportional', 'Proportional (Empfohlen)')}</option>
              <option value="fifo">{t('trace.form.model_fifo', 'FIFO (First-In-First-Out)')}</option>
              <option value="haircut">{t('trace.form.model_haircut', 'Haircut (Fester Abschlag)')}</option>
            </select>
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">{t('trace.form.model_help', 'Proportional: Taint verteilt sich proportional zum Wert-Verhältnis')}</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Max Depth */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">{t('trace.form.max_depth', 'Max. Tiefe')}</label>
              <input
                type="number"
                className="input bg-white dark:bg-slate-700 border-gray-300 dark:border-slate-600 text-gray-900 dark:text-white"
                min="1"
                max="10"
                value={formData.max_depth}
                onChange={(e) => setFormData({ ...formData, max_depth: parseInt(e.target.value) })}
              />
              <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">{t('trace.form.max_depth_help', 'Maximale Hop-Anzahl (1-10)')}</p>
            </div>

            {/* Max Nodes */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">{t('trace.form.max_nodes', 'Max. Nodes')}</label>
              <input
                type="number"
                className="input bg-white dark:bg-slate-700 border-gray-300 dark:border-slate-600 text-gray-900 dark:text-white"
                min="10"
                max="10000"
                value={formData.max_nodes}
                onChange={(e) => setFormData({ ...formData, max_nodes: parseInt(e.target.value) })}
              />
              <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">{t('trace.form.max_nodes_help', 'Maximale Anzahl Adressen')}</p>
            </div>
          </div>

          {/* Min Taint Threshold */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">{t('trace.form.min_taint', 'Min. Taint-Schwellwert')}</label>
            <input
              type="number"
              className="input bg-white dark:bg-slate-700 border-gray-300 dark:border-slate-600 text-gray-900 dark:text-white"
              step="0.001"
              min="0"
              max="1"
              value={formData.min_taint_threshold}
              onChange={(e) => setFormData({ ...formData, min_taint_threshold: parseFloat(e.target.value) })}
            />
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">{t('trace.form.min_taint_help', 'Mindest-Taint-Wert zum Weiterverfolgen (0-1, z.B. 0.01 = 1%)')}</p>
          </div>

          {/* Error Message */}
          {traceMutation.isError && (
            <div className="p-4 bg-red-50 dark:bg-red-950 border-2 border-red-300 dark:border-red-600 rounded-lg flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
              <div className="text-sm text-red-800 dark:text-red-200">
                <p className="font-medium mb-1">{t('trace.error.title', 'Fehler beim Starten des Traces')}</p>
                <p>{(traceMutation.error as any)?.response?.data?.detail || t('trace.error.unknown', 'Unbekannter Fehler')}</p>
              </div>
            </div>
          )}

          {/* Submit */}
          <div className="flex gap-4">
            <Button
              type="submit"
              disabled={traceMutation.isPending}
            >
              {traceMutation.isPending ? t('trace.actions.submitting', 'Trace wird gestartet...') : t('trace.actions.submit', 'Trace starten')}
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={() => setFormData({
                source_address: '',
                direction: 'forward',
                max_depth: 5,
                max_nodes: 1000,
                taint_model: 'proportional',
                min_taint_threshold: 0.01,
                save_to_graph: true,
              })}
            >
              {t('trace.actions.reset', 'Zurücksetzen')}
            </Button>
          </div>
        </form>
      </div>

      {/* Agent Tool Trace (zeitgefiltert, ohne Persist) */}
      <div className="mt-8 card p-6 bg-card border border-border">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">{t('trace.agent.title', 'Agent-Tool Trace (Zeitfenster, ohne Persistenz)')}</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">{t('trace.agent.address', 'Adresse *')}</label>
            <input
              type="text"
              className="input bg-white dark:bg-slate-700 border-gray-300 dark:border-slate-600 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500"
              placeholder={t('trace.agent.address_ph', '0x...')}
              value={agentPayload.address}
              onChange={(e) => setAgentPayload({ ...agentPayload, address: e.target.value })}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">{t('trace.agent.direction', 'Richtung')}</label>
            <select
              className="input bg-white dark:bg-slate-700 border-gray-300 dark:border-slate-600 text-gray-900 dark:text-white"
              value={agentPayload.direction}
              onChange={(e) => setAgentPayload({ ...agentPayload, direction: e.target.value as any })}
            >
              <option value="forward">{t('trace.agent.dir_forward', 'forward')}</option>
              <option value="backward">{t('trace.agent.dir_backward', 'backward')}</option>
              <option value="both">{t('trace.agent.dir_both', 'both')}</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">{t('trace.agent.from', 'Von (ISO Timestamp)')}</label>
            <input
              type="text"
              className="input bg-white dark:bg-slate-700 border-gray-300 dark:border-slate-600 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500"
              placeholder={t('trace.agent.from_ph', '2021-01-01T00:00:00Z')}
              value={agentPayload.from_timestamp}
              onChange={(e) => setAgentPayload({ ...agentPayload, from_timestamp: e.target.value })}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">{t('trace.agent.to', 'Bis (ISO Timestamp)')}</label>
            <input
              type="text"
              className="input bg-white dark:bg-slate-700 border-gray-300 dark:border-slate-600 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500"
              placeholder={t('trace.agent.to_ph', '2023-12-31T23:59:59Z')}
              value={agentPayload.to_timestamp}
              onChange={(e) => setAgentPayload({ ...agentPayload, to_timestamp: e.target.value })}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">{t('trace.agent.max_depth', 'Max. Tiefe')}</label>
            <input
              type="number"
              className="input bg-white dark:bg-slate-700 border-gray-300 dark:border-slate-600 text-gray-900 dark:text-white"
              min={1}
              max={10}
              value={agentPayload.max_depth}
              onChange={(e) => setAgentPayload({ ...agentPayload, max_depth: parseInt(e.target.value) })}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">{t('trace.agent.min_taint', 'Min. Taint')}</label>
            <input
              type="number"
              className="input bg-white dark:bg-slate-700 border-gray-300 dark:border-slate-600 text-gray-900 dark:text-white"
              step={0.001}
              min={0}
              max={1}
              value={agentPayload.min_taint_threshold}
              onChange={(e) => setAgentPayload({ ...agentPayload, min_taint_threshold: parseFloat(e.target.value) })}
            />
          </div>
        </div>
        <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="flex items-center gap-3">
            <input id="en_bridge" type="checkbox" className="checkbox" checked={agentPayload.enable_bridge} onChange={(e) => setAgentPayload({ ...agentPayload, enable_bridge: e.target.checked })} />
            <label htmlFor="en_bridge" className="text-sm">{t('trace.agent.enable_bridge', 'Enable Bridge')}</label>
          </div>
          <div className="flex items-center gap-3">
            <input id="en_utxo" type="checkbox" className="checkbox" checked={agentPayload.enable_utxo} onChange={(e) => setAgentPayload({ ...agentPayload, enable_utxo: e.target.checked })} />
            <label htmlFor="en_utxo" className="text-sm">{t('trace.agent.enable_utxo', 'Enable UTXO')}</label>
          </div>
        </div>
        <div className="mt-6 flex gap-4">
          <Button
            type="button"
            disabled={agentTraceMutation.isPending || !agentPayload.address}
            onClick={() => agentTraceMutation.mutate(agentPayload)}
          >
            {agentTraceMutation.isPending ? t('trace.agent.submitting', 'Agent-Trace läuft...') : t('trace.agent.run', 'Agent-Tool Trace ausführen')}
          </Button>
          <Button type="button" variant="outline" onClick={() => setAgentPayload({
            address: '',
            max_depth: 5,
            direction: 'forward',
            from_timestamp: '',
            to_timestamp: '',
            min_taint_threshold: 0.01,
            max_nodes: 1000,
            enable_native: true,
            enable_token: true,
            enable_bridge: true,
            enable_utxo: true,
            native_decay: 1.0,
            token_decay: 1.0,
            bridge_decay: 0.9,
            utxo_decay: 1.0,
          })}>{t('trace.actions.reset', 'Zurücksetzen')}</Button>
        </div>
        {agentTraceMutation.isSuccess && (
          <pre className="mt-6 text-xs bg-gray-50 dark:bg-slate-900 border border-gray-200 dark:border-slate-700 text-gray-900 dark:text-gray-200 p-4 rounded overflow-auto max-h-80">{JSON.stringify(agentTraceMutation.data, null, 2)}</pre>
        )}
        {agentTraceMutation.isError && (
          <div className="mt-4 p-4 bg-red-50 dark:bg-red-950 border-2 border-red-300 dark:border-red-600 rounded-lg flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
            <div className="text-sm text-red-800 dark:text-red-200">
              <p className="font-medium mb-1">{t('trace.agent.error_title', 'Fehler beim Agent-Tool Trace')}</p>
              <p>{(agentTraceMutation.error as any)?.response?.data?.detail || t('trace.error.unknown', 'Unbekannter Fehler')}</p>
            </div>
          </div>
        )}
      </div>

      {/* Info Box */}
      <div className="mt-6 card p-6 bg-muted/50 border-2 border-border">
        <h3 className="font-semibold text-blue-900 dark:text-blue-200 mb-2">{t('trace.info.title', 'ℹ️ Hinweise')}</h3>
        <ul className="text-sm text-blue-800 dark:text-blue-300 space-y-1">
          <li>• {t('trace.info.item1', 'Traces können je nach Tiefe und Nodes einige Sekunden bis Minuten dauern')}</li>
          <li>• {t('trace.info.item2', 'Ergebnisse werden in Neo4j gespeichert für spätere Analysen')}</li>
          <li>• {t('trace.info.item3', 'High-Risk-Adressen werden automatisch markiert')}</li>
          <li>• {t('trace.info.item4', 'Sanctioned Entities (OFAC) werden sofort erkannt')}</li>
        </ul>
      </div>
    </div>
  )
}

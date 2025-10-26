import React from 'react'
import { useI18n } from '@/contexts/I18nContext'
import { useToastSuccess, useToastError } from '@/components/ui/toast'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

type CaseItem = {
  slug: string
  name: string
  description?: string | null
  addresses: Array<{ chain: string; address: string }>
  auto_trace?: boolean
}

type CreatePayload = {
  slug: string
  name: string
  description?: string
  addresses: Array<{ chain: string; address: string }>
  auto_trace?: boolean
}

type NewsCaseEvent = {
  type: 'news_case.snapshot' | 'news_case.status' | 'news_case.tx' | 'news_case.kyt'
  slug: string
  snapshot?: any
  tx?: any
  risk_level?: string
  risk_score?: number
  alerts?: any[]
  from_labels?: string[]
  to_labels?: string[]
  timestamp: number
}

export default function NewsCasesManager() {
  const { currentLanguage } = useI18n()
  const [loading, setLoading] = React.useState(false)
  const [error, setError] = React.useState<string | null>(null)
  const [items, setItems] = React.useState<CaseItem[]>([])
  const toastSuccess = useToastSuccess()
  const toastError = useToastError()

  // WS State per slug
  const [wsStates, setWsStates] = React.useState<Record<string, { connected: boolean; txCount: number; kytAlerts: number; lastUpdate: number }>>({})

  const [form, setForm] = React.useState<CreatePayload>({
    slug: '',
    name: '',
    description: '',
    addresses: [{ chain: 'ethereum', address: '' }],
    auto_trace: false,
  })

  // WS Hook für jeden NewsCase
  const updateWsState = React.useCallback((slug: string, update: Partial<typeof wsStates[string]>) => {
    setWsStates(prev => ({
      ...prev,
      [slug]: { ...prev[slug], ...update }
    }))
  }, [])

  // Für jeden gelisteten Item WS-Verbindung aufbauen
  React.useEffect(() => {
    const wsConnections: Record<string, WebSocket> = {}
    items.forEach(item => {
      const wsUrl = `${API_URL.replace('http', 'ws')}/api/v1/ws/news-cases/${item.slug}?backlog=50`
      const ws = new WebSocket(wsUrl)

      ws.onopen = () => {
        console.log('WebSocket connected:', wsUrl)
        updateWsState(item.slug, { connected: true })
      }

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data)
          const eventData = message as unknown as NewsCaseEvent
          if (eventData.type === 'news_case.tx') {
            updateWsState(item.slug, { txCount: (wsStates[item.slug]?.txCount || 0) + 1, lastUpdate: Date.now() })
          } else if (eventData.type === 'news_case.kyt') {
            updateWsState(item.slug, { kytAlerts: (wsStates[item.slug]?.kytAlerts || 0) + 1, lastUpdate: Date.now() })
          } else if (eventData.type === 'news_case.status' || eventData.type === 'news_case.snapshot') {
            updateWsState(item.slug, { lastUpdate: Date.now() })
          }
        } catch (e) {
          console.error('Failed to parse WebSocket message:', e)
        }
      }

      ws.onerror = (error) => {
        console.error('WebSocket error:', error)
      }

      ws.onclose = () => {
        console.log('WebSocket disconnected')
        updateWsState(item.slug, { connected: false })
      }

      wsConnections[item.slug] = ws
    })

    return () => {
      // Cleanup wenn Items ändern
      Object.values(wsConnections).forEach(ws => ws.close())
    }
  }, [items, updateWsState])

  // Simple chain/address validation
  const validateAddress = (chain: string, address: string): string | null => {
    const a = (address || '').trim()
    const c = (chain || 'ethereum').toLowerCase()
    if (!a) return 'Adresse darf nicht leer sein'
    switch (c) {
      case 'ethereum':
      case 'polygon':
      case 'bsc':
      case 'arbitrum':
      case 'optimism':
      case 'base':
        if (!/^0x[a-fA-F0-9]{40}$/.test(a)) return 'Ungültige EVM-Adresse (0x...)'
        return null
      case 'bitcoin':
        if (!/^(bc1[ac-hj-np-z0-9]{11,71}|[13][a-km-zA-HJ-NP-Z1-9]{25,34})$/.test(a)) return 'Ungültige Bitcoin-Adresse'
        return null
      case 'solana':
        if (!/^[1-9A-HJ-NP-Za-km-z]{32,44}$/.test(a)) return 'Ungültige Solana-Adresse'
        return null
      case 'tron':
        if (!/^T[1-9A-HJ-NP-Za-km-z]{33}$/.test(a)) return 'Ungültige Tron-Adresse'
        return null
      default:
        return null
    }
  }

  const anyInvalid = React.useMemo(() => {
    return form.addresses.some((a) => !!validateAddress(a.chain, a.address))
  }, [form.addresses])

  const fetchList = React.useCallback(async () => {
    setError(null)
    try {
      const res = await fetch(`${API_URL}/api/v1/news-cases`, { credentials: 'include' })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      setItems((data.cases || []) as CaseItem[])
    } catch (e: any) {
      setError(e?.message || 'Fehler beim Laden')
    }
  }, [])

  React.useEffect(() => { void fetchList() }, [fetchList])

  const onAddAddress = () => {
    setForm((f) => ({ ...f, addresses: [...f.addresses, { chain: 'ethereum', address: '' }] }))
  }
  const onRemoveAddress = (idx: number) => {
    setForm((f) => ({ ...f, addresses: f.addresses.filter((_, i) => i !== idx) }))
  }

  const onCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      // client-side validation
      if (!form.slug.trim() || !form.name.trim()) {
        throw new Error('Slug und Name sind erforderlich')
      }
      const bad = form.addresses.find((a) => !!validateAddress(a.chain, a.address))
      if (bad) {
        throw new Error('Bitte überprüfe die eingegebenen Adressen (Format/Chain)')
      }
      const res = await fetch(`${API_URL}/api/v1/news-cases`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(form),
      })
      if (!res.ok) {
        const t = await res.text()
        throw new Error(t || `HTTP ${res.status}`)
      }
      setForm({ slug: '', name: '', description: '', addresses: [{ chain: 'ethereum', address: '' }], auto_trace: false })
      await fetchList()
      toastSuccess('NewsCase erstellt', 'Der NewsCase wurde erfolgreich erstellt.')
    } catch (e: any) {
      setError(e?.message || 'Fehler beim Erstellen')
      toastError('Fehler beim Erstellen', e?.message)
    } finally {
      setLoading(false)
    }
  }

  const onDelete = async (slug: string) => {
    if (!confirm(`NewsCase "${slug}" löschen?`)) return
    try {
      const res = await fetch(`${API_URL}/api/v1/news-cases/${encodeURIComponent(slug)}`, {
        method: 'DELETE',
        credentials: 'include',
      })
      if (!res.ok && res.status !== 204) throw new Error(`HTTP ${res.status}`)
      await fetchList()
      toastSuccess('NewsCase gelöscht', `"${slug}" wurde entfernt.`)
    } catch (e: any) {
      setError(e?.message || 'Fehler beim Löschen')
      toastError('Fehler beim Löschen', e?.message)
    }
  }

  const toggleAutoTrace = async (slug: string, current?: boolean) => {
    try {
      const res = await fetch(`${API_URL}/api/v1/news-cases/${encodeURIComponent(slug)}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ auto_trace: !current })
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      await fetchList()
      toastSuccess('Auto-Trace aktualisiert', `${!current ? 'Aktiviert' : 'Deaktiviert'} für "${slug}"`)
    } catch (e: any) {
      setError(e?.message || 'Fehler beim Aktualisieren von Auto-Trace')
      toastError('Fehler beim Aktualisieren', e?.message)
    }
  }

  return (
    <div className="p-6">
      <h1 className="text-2xl font-semibold">News Cases</h1>
      <p className="text-slate-600 dark:text-slate-400 mt-1">Öffentliche Slug-basierte Live-Tracker für Adressen.</p>

      <div className="mt-6 grid lg:grid-cols-2 gap-6">
        <form onSubmit={onCreate} className="rounded-lg border border-slate-200 dark:border-slate-800 p-4 bg-white dark:bg-slate-900">
          <div className="text-lg font-medium">Neu erstellen</div>
          <div className="mt-4 grid gap-3">
            <div>
              <label className="text-sm font-medium">Slug</label>
              <input value={form.slug} onChange={(e) => setForm({ ...form, slug: e.target.value })} className="mt-1 w-full rounded border px-3 py-2 bg-transparent" placeholder="binance-hack-2025" required />
            </div>
            <div>
              <label className="text-sm font-medium">Name</label>
              <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="mt-1 w-full rounded border px-3 py-2 bg-transparent" placeholder="Binance Hack 2025" required />
            </div>
            <div>
              <label className="text-sm font-medium">Beschreibung</label>
              <textarea value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} className="mt-1 w-full rounded border px-3 py-2 bg-transparent" rows={3} placeholder="Kurze Beschreibung" />
            </div>
            <div className="flex items-center gap-2">
              <input id="auto_trace" type="checkbox" checked={!!form.auto_trace} onChange={(e) => setForm({ ...form, auto_trace: e.target.checked })} />
              <label htmlFor="auto_trace" className="text-sm">Auto-Trace bei neuen Transaktionen</label>
            </div>
            <div>
              <div className="flex items-center justify-between">
                <label className="text-sm font-medium">Adressen</label>
                <button type="button" onClick={onAddAddress} className="text-sm text-primary-600">+ Adresse</button>
              </div>
              <div className="mt-2 grid gap-2">
                {form.addresses.map((a, idx) => (
                  <div key={idx} className="grid grid-cols-12 gap-2 items-center">
                    <select value={a.chain} onChange={(e) => setForm((f) => { const next = [...f.addresses]; next[idx] = { ...next[idx], chain: e.target.value }; return { ...f, addresses: next } })} className="col-span-4 rounded border px-2 py-2 bg-transparent">
                      <option value="ethereum">ethereum</option>
                      <option value="bitcoin">bitcoin</option>
                      <option value="polygon">polygon</option>
                      <option value="tron">tron</option>
                      <option value="solana">solana</option>
                    </select>
                    {(() => { const err = validateAddress(a.chain, a.address); return (
                      <div className="col-span-7">
                        <input
                          value={a.address}
                          onChange={(e) => setForm((f) => { const next = [...f.addresses]; next[idx] = { ...next[idx], address: e.target.value }; return { ...f, addresses: next } })}
                          className={`w-full rounded border px-3 py-2 bg-transparent font-mono ${err ? 'border-red-500 focus:ring-red-300' : ''}`}
                          placeholder="0x... / bc1q..."
                          required
                        />
                        {err && <div className="mt-1 text-xs text-red-600">{err}</div>}
                      </div>
                    )})()}
                    <button type="button" onClick={() => onRemoveAddress(idx)} className="col-span-1 text-sm text-red-600">✕</button>
                  </div>
                ))}
              </div>
            </div>
            <div className="pt-2">
              <button type="submit" disabled={loading || anyInvalid} className="inline-flex items-center px-4 py-2 rounded bg-primary text-white disabled:opacity-60 disabled:cursor-not-allowed">
                {loading ? 'Erstelle…' : 'Erstellen'}
              </button>
            </div>
          </div>
          {error && <div className="mt-3 text-sm text-red-600">{error}</div>}
        </form>

        <div className="rounded-lg border border-slate-200 dark:border-slate-800 p-4 bg-white dark:bg-slate-900">
          <div className="text-lg font-medium">Vorhandene NewsCases</div>
          <div className="mt-3 grid gap-2">
            {items.length === 0 && (
              <div className="text-sm text-slate-500">Noch keine Einträge.</div>
            )}
            {items.map((it) => {
              const wsState = wsStates[it.slug] || { connected: false, txCount: 0, kytAlerts: 0, lastUpdate: 0 }
              const hasActivity = wsState.txCount > 0 || wsState.kytAlerts > 0
              const lastUpdateStr = wsState.lastUpdate ? new Date(wsState.lastUpdate).toLocaleTimeString() : ''
              
              return (
              <div key={it.slug} className="rounded border border-slate-200 dark:border-slate-800 p-3">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-medium flex items-center gap-2">
                      {it.name}
                      {wsState.connected && <span className="text-green-500">🟢</span>}
                      {!wsState.connected && <span className="text-red-500">🔴</span>}
                      {hasActivity && (
                        <span className="bg-red-100 text-red-800 text-xs px-2 py-1 rounded">{wsState.txCount} TX, {wsState.kytAlerts} Alerts</span>
                      )}
                    </div>
                    <div className="text-xs text-slate-500">Slug: <code className="bg-slate-100 px-1 rounded">{it.slug}</code></div>
                    {typeof (it as any).auto_trace !== 'undefined' && (
                      <div className="text-xs mt-0.5">
                        Auto-Trace: {(it as any).auto_trace ? 'aktiv' : 'aus'}
                      </div>
                    )}
                    {lastUpdateStr && <div className="text-xs text-slate-400">Letztes Update: {lastUpdateStr}</div>}
                  </div>
                  <div className="flex items-center gap-2">
                    <a href={`/${currentLanguage}/news/${encodeURIComponent(it.slug)}`} target="_blank" rel="noreferrer" className="text-sm text-primary-600">Öffnen</a>
                    <button onClick={() => toggleAutoTrace(it.slug, it.auto_trace)} className="text-sm text-indigo-600">{it.auto_trace ? 'Auto-Trace deaktivieren' : 'Auto-Trace aktivieren'}</button>
                    <button onClick={() => onDelete(it.slug)} className="text-sm text-red-600">Löschen</button>
                  </div>
                </div>
                {it.addresses && it.addresses.length > 0 && (
                  <div className="text-xs text-slate-600 dark:text-slate-400 mt-2">
                    <div className="font-medium">Adressen</div>
                    <ul className="list-disc pl-5">
                      {it.addresses.map((a, i) => (
                        <li key={i}><span className="font-mono">{a.chain}</span>: <span className="font-mono break-all">{a.address}</span></li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
              )
            })}
          </div>
        </div>
      </div>
    </div>
  )
}

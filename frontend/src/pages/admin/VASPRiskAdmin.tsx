import React from 'react'

function pretty(obj: any) {
  try { return JSON.stringify(obj, null, 2) } catch { return String(obj) }
}

const riskLevelBadge = (level: string) => {
  const map: Record<string, string> = {
    low: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900 dark:text-emerald-100',
    medium: 'bg-amber-100 text-amber-700 dark:bg-amber-900 dark:text-amber-100',
    high: 'bg-orange-100 text-orange-700 dark:bg-orange-900 dark:text-orange-100',
    critical: 'bg-rose-100 text-rose-700 dark:bg-rose-900 dark:text-rose-100',
    unknown: 'bg-slate-200 text-slate-700 dark:bg-slate-800 dark:text-slate-200',
  }
  const cls = map[level?.toLowerCase?.() || 'unknown'] || map.unknown
  return <span className={`px-2 py-0.5 rounded-full text-[11px] uppercase tracking-wide ${cls}`}>{level}</span>
}

const complianceBadge = (status: string) => {
  const map: Record<string, string> = {
    compliant: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900 dark:text-emerald-100',
    pending_review: 'bg-amber-100 text-amber-700 dark:bg-amber-900 dark:text-amber-100',
    non_compliant: 'bg-orange-100 text-orange-700 dark:bg-orange-900 dark:text-orange-100',
    sanctioned: 'bg-rose-100 text-rose-700 dark:bg-rose-900 dark:text-rose-100',
    unknown: 'bg-slate-200 text-slate-700 dark:bg-slate-800 dark:text-slate-200',
  }
  const cls = map[status?.toLowerCase?.() || 'unknown'] || map.unknown
  return <span className={`px-2 py-0.5 rounded-full text-[11px] uppercase tracking-wide ${cls}`}>{status}</span>
}

const VASPRiskAdmin: React.FC = () => {
  const [loading, setLoading] = React.useState(false)
  const [message, setMessage] = React.useState<string>("")
  const [summary, setSummary] = React.useState<any | null>(null)
  const [history, setHistory] = React.useState<any[]>([])
  const [filterVasp, setFilterVasp] = React.useState<string>("")
  const [batchIds, setBatchIds] = React.useState<string>("binance,coinbase,kraken")
  const [lastRecord, setLastRecord] = React.useState<any | null>(null)
  const [reviewStatus, setReviewStatus] = React.useState<string>("pending_review")
  const [reviewAction, setReviewAction] = React.useState<string>("")
  const [reviewNotes, setReviewNotes] = React.useState<string>("")

  const loadSummary = React.useCallback(async () => {
    setLoading(true)
    setMessage("")
    try {
      const res = await fetch('/api/v1/compliance/vasp/risk/summary')
      if (!res.ok) throw new Error(await res.text())
      setSummary(await res.json())
    } catch (e: any) {
      setMessage(`Fehler (summary): ${e?.message || e}`)
    } finally { setLoading(false) }
  }, [])

  const loadLast = React.useCallback(async (vasp?: string) => {
    if (!vasp) { setLastRecord(null); return }
    try {
      const res = await fetch(`/api/v1/compliance/vasp/${encodeURIComponent(vasp)}/risk/last?auto_score_if_missing=false`)
      if (!res.ok) throw new Error(await res.text())
      const data = await res.json()
      setLastRecord(data.record || null)
    } catch (e: any) {
      setLastRecord(null)
    }
  }, [])

  const loadHistory = React.useCallback(async (vasp?: string) => {
    setLoading(true)
    setMessage("")
    try {
      const url = new URL('/api/v1/compliance/vasp/risk/history', window.location.origin)
      if (vasp) url.searchParams.set('vasp_id', vasp)
      url.searchParams.set('limit', '100')
      const res = await fetch(url.toString().replace(window.location.origin, ''))
      if (!res.ok) throw new Error(await res.text())
      const data = await res.json()
      setHistory(data.items || [])
    } catch (e: any) {
      setMessage(`Fehler (history): ${e?.message || e}`)
    } finally { setLoading(false) }
  }, [])

  const saveReview = React.useCallback(async () => {
    if (!filterVasp) return
    setLoading(true)
    setMessage("")
    try {
      const res = await fetch(`/api/v1/compliance/vasp/${encodeURIComponent(filterVasp)}/risk/review`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          status: reviewStatus,
          reviewed_by: 'admin',
          notes: reviewNotes,
          recommended_action: reviewAction || undefined,
        })
      })
      if (!res.ok) throw new Error(await res.text())
      setMessage('Review gespeichert')
      await loadHistory(filterVasp)
      await loadLast(filterVasp)
    } catch (e: any) {
      setMessage(`Fehler (review): ${e?.message || e}`)
    } finally { setLoading(false) }
  }, [filterVasp, reviewStatus, reviewNotes, reviewAction, loadHistory, loadLast])

  React.useEffect(() => { loadSummary(); loadHistory() }, [loadSummary, loadHistory])

  const scoreOne = async (vaspId: string) => {
    if (!vaspId) return
    setLoading(true)
    setMessage("")
    try {
      const res = await fetch(`/api/v1/compliance/vasp/${encodeURIComponent(vaspId)}/risk/score`, { method: 'POST' })
      if (!res.ok) throw new Error(await res.text())
      await loadSummary(); await loadHistory(filterVasp || undefined)
      await loadLast(filterVasp || undefined)
      setMessage(`Scoring ausgelöst für ${vaspId}`)
    } catch (e: any) {
      setMessage(`Fehler (score-one): ${e?.message || e}`)
    } finally { setLoading(false) }
  }

  const scoreBatch = async () => {
    const ids = (batchIds || '').split(',').map(s => s.trim()).filter(Boolean)
    if (!ids.length) return
    setLoading(true)
    setMessage("")
    try {
      const res = await fetch('/api/v1/compliance/vasp/risk/score-many', {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ vasp_ids: ids })
      })
      if (!res.ok) throw new Error(await res.text())
      await loadSummary(); await loadHistory(filterVasp || undefined)
      await loadLast(filterVasp || undefined)
      setMessage(`Batch-Scoring ausgelöst für ${ids.length} VASPs`)
    } catch (e: any) {
      setMessage(`Fehler (score-many): ${e?.message || e}`)
    } finally { setLoading(false) }
  }

  const runOnce = async () => {
    setLoading(true)
    setMessage("")
    try {
      const res = await fetch('/api/v1/compliance/vasp/risk/run-once', { method: 'POST' })
      if (!res.ok) throw new Error(await res.text())
      await loadSummary(); await loadHistory(filterVasp || undefined)
      await loadLast(filterVasp || undefined)
      setMessage('Worker run-once gestartet')
    } catch (e: any) {
      setMessage(`Fehler (run-once): ${e?.message || e}`)
    } finally { setLoading(false) }
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">VASP Risk (Admin)</h1>
        <div className="flex items-center gap-2">
          <button onClick={loadSummary} className="px-3 py-2 rounded bg-slate-200 dark:bg-slate-700">Refresh</button>
          <button onClick={runOnce} className="px-3 py-2 rounded bg-blue-600 text-white disabled:opacity-50" disabled={loading}>Worker Run Once</button>
        </div>
      </div>

      {!!message && (
        <div className="p-3 rounded bg-yellow-100 text-yellow-900 dark:bg-yellow-900 dark:text-yellow-100">{message}</div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="border rounded p-4 bg-white dark:bg-slate-900 dark:border-slate-800">
          <h2 className="font-semibold mb-3">Summary</h2>
          {summary ? (
            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div className="rounded bg-slate-50 dark:bg-slate-800 p-3">
                  <div className="text-xs uppercase tracking-wide text-slate-500">VASPs gescored</div>
                  <div className="text-2xl font-semibold mt-1">{summary.total_vasps_scored ?? 0}</div>
                </div>
                <div className="rounded bg-slate-50 dark:bg-slate-800 p-3">
                  <div className="text-xs uppercase tracking-wide text-slate-500">Ø Score</div>
                  <div className="text-2xl font-semibold mt-1">{(summary.avg_risk_score ?? 0).toFixed(2)}</div>
                </div>
              </div>
              <div>
                <div className="text-xs uppercase text-slate-500 mb-2">Risk Level</div>
                <div className="flex flex-wrap gap-2">
                  {(Object.entries(summary.by_risk_level || {}) as Array<[string, number]>).map(([level, count]) => (
                    <span key={level} className="inline-flex items-center gap-2">
                      {riskLevelBadge(level)}
                      <span className="text-xs text-slate-600 dark:text-slate-300">{count}</span>
                    </span>
                  ))}
                </div>
              </div>
              <div>
                <div className="text-xs uppercase text-slate-500 mb-2">Compliance Status</div>
                <div className="flex flex-wrap gap-2">
                  {(Object.entries(summary.by_compliance_status || {}) as Array<[string, number]>).map(([status, count]) => (
                    <span key={status} className="inline-flex items-center gap-2">
                      {complianceBadge(status)}
                      <span className="text-xs text-slate-600 dark:text-slate-300">{count}</span>
                    </span>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="text-sm opacity-70">Keine Daten</div>
          )}
        </div>

        <div className="border rounded p-4 bg-white dark:bg-slate-900 dark:border-slate-800">
          <h2 className="font-semibold mb-3">Batch</h2>
          <label className="text-xs opacity-70">VASPs (Komma-getrennt)</label>
          <input className="w-full mt-1 p-2 rounded bg-slate-50 dark:bg-slate-800" value={batchIds} onChange={e => setBatchIds(e.target.value)} />
          <div className="mt-3 flex gap-2">
            <button onClick={scoreBatch} className="px-3 py-2 rounded bg-green-600 text-white disabled:opacity-50" disabled={loading}>Score Many</button>
          </div>
          <div className="mt-4 text-xs opacity-70">Tipp: bekannte IDs – binance, coinbase, kraken, gemini, uniswap</div>
        </div>

        <div className="border rounded p-4 bg-white dark:bg-slate-900 dark:border-slate-800">
          <h2 className="font-semibold mb-3">Einzel-Scoring</h2>
          <div className="flex gap-2">
            <input className="flex-1 p-2 rounded bg-slate-50 dark:bg-slate-800" placeholder="vasp_id (z.B. binance)" value={filterVasp} onChange={e => setFilterVasp(e.target.value)} />
            <button onClick={() => scoreOne(filterVasp)} className="px-3 py-2 rounded bg-indigo-600 text-white disabled:opacity-50" disabled={loading || !filterVasp}>Score</button>
            <button onClick={() => { loadHistory(filterVasp); loadLast(filterVasp) }} className="px-3 py-2 rounded bg-slate-200 dark:bg-slate-700 disabled:opacity-50" disabled={loading}>History</button>
          </div>
          <div className="mt-4 text-xs opacity-70">Letzter Record: <code>/api/v1/compliance/vasp/{'{'}id{'}'}/risk/last</code></div>
        </div>
      </div>

      {/* Review Editor */}
      <div className="border rounded p-4 bg-white dark:bg-slate-900 dark:border-slate-800">
        <h2 className="font-semibold mb-3">Review</h2>
        {lastRecord ? (
          <div className="mb-4 text-sm grid grid-cols-1 md:grid-cols-3 gap-3">
            <div>
              <div className="text-xs uppercase text-slate-500">VASP</div>
              <div className="font-mono">{lastRecord.vasp_id}</div>
            </div>
            <div>
              <div className="text-xs uppercase text-slate-500">Risk</div>
              <div>{riskLevelBadge(lastRecord.overall_risk)} <span className="ml-2 font-mono">{(lastRecord.risk_score ?? 0).toFixed(2)}</span></div>
            </div>
            <div>
              <div className="text-xs uppercase text-slate-500">Status</div>
              <div>{complianceBadge(lastRecord.compliance_status)}</div>
            </div>
          </div>
        ) : (
          <div className="text-sm opacity-70 mb-4">Kein letzter Record geladen.</div>
        )}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <div>
            <label className="text-xs opacity-70">Review-Status</label>
            <select className="w-full mt-1 p-2 rounded bg-slate-50 dark:bg-slate-800" value={reviewStatus} onChange={e => setReviewStatus(e.target.value)}>
              <option value="approved">approved</option>
              <option value="review">review</option>
              <option value="rejected">rejected</option>
              <option value="monitor">monitor</option>
              <option value="pending_review">pending_review</option>
            </select>
          </div>
          <div>
            <label className="text-xs opacity-70">Empfohlene Aktion</label>
            <input className="w-full mt-1 p-2 rounded bg-slate-50 dark:bg-slate-800" placeholder="approve/review/reject/monitor" value={reviewAction} onChange={e => setReviewAction(e.target.value)} />
          </div>
          <div className="md:col-span-1">
            <label className="text-xs opacity-70">Notizen</label>
            <textarea className="w-full mt-1 p-2 h-[42px] rounded bg-slate-50 dark:bg-slate-800" placeholder="Kommentar/Begründung" value={reviewNotes} onChange={e => setReviewNotes(e.target.value)} />
          </div>
        </div>
        <div className="mt-3">
          <button onClick={saveReview} className="px-3 py-2 rounded bg-emerald-600 text-white disabled:opacity-50" disabled={loading || !filterVasp}>Review speichern</button>
        </div>
      </div>

      <div className="border rounded p-4 bg-white dark:bg-slate-900 dark:border-slate-800">
        <h2 className="font-semibold mb-3">History</h2>
        {history.length === 0 ? (
          <div className="text-sm opacity-70">Keine Einträge</div>
        ) : (
          <div className="overflow-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="text-left border-b dark:border-slate-800">
                  <th className="py-2 pr-4">Zeit</th>
                  <th className="py-2 pr-4">VASP</th>
                  <th className="py-2 pr-4">Risk</th>
                  <th className="py-2 pr-4">Score</th>
                  <th className="py-2 pr-4">Status</th>
                  <th className="py-2 pr-4">Faktoren</th>
                </tr>
              </thead>
              <tbody>
                {history.map((r: any, i: number) => (
                  <tr key={i} className="border-b last:border-0 dark:border-slate-800">
                    <td className="py-2 pr-4 whitespace-nowrap">{new Date(r.scored_at).toLocaleString()}</td>
                    <td className="py-2 pr-4">{r.vasp_id}</td>
                    <td className="py-2 pr-4">{riskLevelBadge(r.overall_risk)}</td>
                    <td className="py-2 pr-4 font-mono">{(r.risk_score ?? 0).toFixed(2)}</td>
                    <td className="py-2 pr-4">{complianceBadge(r.compliance_status)}</td>
                    <td className="py-2 pr-4">
                      <div className="flex flex-wrap gap-1 max-w-lg">
                        {(r.risk_factors || []).length
                          ? r.risk_factors.map((rf: string, idx: number) => (
                              <span key={idx} className="px-2 py-0.5 text-[11px] rounded-full bg-slate-200 text-slate-700 dark:bg-slate-800 dark:text-slate-200">
                                {rf}
                              </span>
                            ))
                          : <span className="text-xs text-slate-500">Keine</span>}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}

export default VASPRiskAdmin

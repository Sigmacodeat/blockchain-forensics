import React from 'react'

function jsonPretty(obj: any) {
  try {
    return JSON.stringify(obj, null, 2)
  } catch {
    return String(obj)
  }
}

const SOARPlaybooksAdmin: React.FC = () => {
  const [loading, setLoading] = React.useState(false)
  const [playbooks, setPlaybooks] = React.useState<any[]>([])
  const [evalInput, setEvalInput] = React.useState<string>(`{
  "address": "0xabc...",
  "value_usd": 15000,
  "labels": [],
  "metadata": {"from_address": "0xfrom", "to_address": "0xto", "chain": "ethereum"}
}`)
  const [evalResult, setEvalResult] = React.useState<any | null>(null)
  const [runResult, setRunResult] = React.useState<any | null>(null)
  const [message, setMessage] = React.useState<string>("")
  const renderCaseActions = (actions: any[]) => {
    if (!actions?.length) return null
    return (
      <div className="mt-2 space-y-2">
        {actions.map((action, idx) => {
          const caseId = action?.case_id
          return (
            <div
              key={idx}
              className="border rounded px-3 py-2 text-xs bg-slate-50 dark:bg-slate-900 dark:border-slate-800"
            >
              <div className="flex items-center justify-between">
                <span className="font-semibold">{action?.type}</span>
                <span className={`px-2 py-0.5 rounded text-[11px] uppercase ${action?.status === 'ok' ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900 dark:text-emerald-100' : action?.status === 'error' ? 'bg-rose-100 text-rose-700 dark:bg-rose-900 dark:text-rose-100' : 'bg-slate-200 text-slate-700 dark:bg-slate-800 dark:text-slate-200'}`}>{action?.status}</span>
              </div>
              {caseId && (
                <div className="mt-2">
                  <a
                    className="inline-flex items-center gap-1 text-xs text-blue-600 hover:text-blue-500 dark:text-blue-300"
                    href={`/${document.documentElement.getAttribute('lang') || 'en'}/cases/${caseId}`}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    <span className="inline-flex items-center gap-1">
                      <span>Case öffnen</span>
                      <svg className="w-3 h-3" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 19.5l15-15m0 0H8.25m11.25 0v11.25" />
                      </svg>
                    </span>
                  </a>
                </div>
              )}
              {action?.error && (
                <div className="mt-2 text-rose-500">{String(action.error)}</div>
              )}
            </div>
          )
        })}
      </div>
    )
  }

  const loadPlaybooks = React.useCallback(async () => {
    setLoading(true)
    setMessage("")
    try {
      const res = await fetch('/api/v1/soar/playbooks')
      if (!res.ok) throw new Error(await res.text())
      const data = await res.json()
      setPlaybooks(data.playbooks || [])
    } catch (e: any) {
      setMessage(`Fehler beim Laden: ${e?.message || e}`)
    } finally {
      setLoading(false)
    }
  }, [])

  React.useEffect(() => { loadPlaybooks() }, [loadPlaybooks])

  const reloadPlaybooks = async () => {
    setLoading(true)
    setMessage("")
    try {
      const res = await fetch('/api/v1/soar/reload', { method: 'POST' })
      if (!res.ok) throw new Error(await res.text())
      await loadPlaybooks()
      setMessage('Playbooks neu geladen')
    } catch (e: any) {
      setMessage(`Reload fehlgeschlagen: ${e?.message || e}`)
    } finally {
      setLoading(false)
    }
  }

  const evaluateOnly = async () => {
    setLoading(true)
    setEvalResult(null)
    setMessage("")
    try {
      const body = JSON.parse(evalInput)
      const res = await fetch('/api/v1/soar/evaluate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ event: body })
      })
      if (!res.ok) throw new Error(await res.text())
      const data = await res.json()
      setEvalResult(data)
    } catch (e: any) {
      setMessage(`Evaluate fehlgeschlagen: ${e?.message || e}`)
    } finally {
      setLoading(false)
    }
  }

  const runPlaybooks = async () => {
    setLoading(true)
    setRunResult(null)
    setMessage("")
    try {
      const body = JSON.parse(evalInput)
      const res = await fetch('/api/v1/soar/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ event: body })
      })
      if (!res.ok) throw new Error(await res.text())
      const data = await res.json()
      setRunResult(data)
    } catch (e: any) {
      setMessage(`Run fehlgeschlagen: ${e?.message || e}`)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">SOAR Playbooks (Admin)</h1>
        <div className="flex items-center gap-2">
          <button onClick={loadPlaybooks} className="px-3 py-2 rounded bg-slate-200 dark:bg-slate-700">Aktualisieren</button>
          <button onClick={reloadPlaybooks} className="px-3 py-2 rounded bg-blue-600 text-white disabled:opacity-50" disabled={loading}>Reload</button>
        </div>
      </div>

      {!!message && (
        <div className="p-3 rounded bg-yellow-100 text-yellow-900 dark:bg-yellow-900 dark:text-yellow-100">{message}</div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="border rounded p-4 bg-white dark:bg-slate-900 dark:border-slate-800">
          <h2 className="font-semibold mb-3">Playbooks</h2>
          {loading && <div className="text-sm opacity-70">Lade...</div>}
          {!loading && playbooks.length === 0 && (
            <div className="text-sm opacity-70">Keine Playbooks gefunden.</div>
          )}
          <ul className="space-y-2">
            {playbooks.map((pb, idx) => (
              <li key={idx} className="p-3 rounded border dark:border-slate-800 bg-white/80 dark:bg-slate-900/80">
                <div className="flex items-center justify-between">
                  <div className="text-sm font-medium">
                    {pb.name}
                    <span className="ml-1 text-xs text-slate-500">({pb.id})</span>
                  </div>
                  <span
                    className={`px-2 py-0.5 rounded text-[11px] uppercase ${pb.enabled ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900 dark:text-emerald-100' : 'bg-slate-200 text-slate-700 dark:bg-slate-700 dark:text-slate-200'}`}
                  >
                    {pb.enabled ? 'aktiv' : 'deaktiviert'}
                  </span>
                </div>
                {pb.tags?.length ? (
                  <div className="mt-2 flex flex-wrap gap-2">
                    {pb.tags.map((tag: string) => (
                      <span
                        key={tag}
                        className="px-2 py-0.5 text-[11px] rounded-full bg-indigo-100 text-indigo-700 dark:bg-indigo-900 dark:text-indigo-200"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                ) : (
                  <div className="mt-2 text-xs text-slate-500">Keine Tags</div>
                )}
              </li>
            ))}
          </ul>
        </div>

        <div className="border rounded p-4 bg-white dark:bg-slate-900 dark:border-slate-800">
          <h2 className="font-semibold mb-3">Event testen</h2>
          <textarea className="w-full h-48 bg-slate-50 dark:bg-slate-800 p-2 rounded text-sm font-mono" value={evalInput} onChange={e => setEvalInput(e.target.value)} />
          <div className="mt-3 flex gap-2">
            <button onClick={evaluateOnly} className="px-3 py-2 rounded bg-slate-200 dark:bg-slate-700 disabled:opacity-50" disabled={loading}>Evaluate</button>
            <button onClick={runPlaybooks} className="px-3 py-2 rounded bg-green-600 text-white disabled:opacity-50" disabled={loading}>Run</button>
          </div>

          {evalResult && (
            <div className="mt-4">
              <div className="text-sm font-semibold">Evaluate Result</div>
              <pre className="text-xs bg-slate-50 dark:bg-slate-800 p-2 rounded overflow-auto max-h-60">{jsonPretty(evalResult)}</pre>
            </div>
          )}
          {runResult && (
            <div className="mt-4">
              <div className="text-sm font-semibold">Run Result</div>
              <pre className="text-xs bg-slate-50 dark:bg-slate-800 p-2 rounded overflow-auto max-h-60">{jsonPretty(runResult)}</pre>
              {runResult?.matches?.map((match: any, idx: number) => (
                <div key={idx} className="mt-3 border rounded p-3 bg-white dark:bg-slate-900 dark:border-slate-800">
                  <div className="text-sm font-semibold flex items-center justify-between">
                    <span>{match?.name || 'Playbook'}</span>
                    <span className="text-xs text-slate-500">{match?.playbook_id}</span>
                  </div>
                  {renderCaseActions(match?.actions)}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default SOARPlaybooksAdmin

import { useState } from 'react'

export default function ForensicTrace() {
  const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'
  const [source, setSource] = useState('')
  const [direction, setDirection] = useState('forward')
  const [maxDepth, setMaxDepth] = useState(3)
  const [loading, setLoading] = useState(false)
  const [trace, setTrace] = useState(null)
  const [error, setError] = useState('')

  const startTrace = async () => {
    setLoading(true)
    setError('')
    setTrace(null)
    try {
      const res = await fetch(`${API_BASE}/api/trace/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          source_address: source,
          direction,
          max_depth: Number(maxDepth),
          max_nodes: 500,
          save_to_graph: false,
        })
      })
      if (!res.ok) {
        const txt = await res.text()
        throw new Error(txt || 'Trace start failed')
      }
      const data = await res.json()
      setTrace(data)
    } catch (e) {
      setError(String(e.message || e))
    } finally {
      setLoading(false)
    }
  }

  const download = (format) => {
    if (!trace?.trace_id) return
    const url = `${API_BASE}/api/trace/${trace.trace_id}/report?format=${format}`
    window.open(url, '_blank')
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border-2 border-gray-100 p-6">
      <h3 className="font-bold text-gray-900 mb-4">Forensic Trace</h3>
      <div className="grid md:grid-cols-4 gap-3 mb-4">
        <input value={source} onChange={(e) => setSource(e.target.value)} placeholder="Source Address (0x..., bc1..., ...)" className="border-2 border-gray-200 rounded-lg px-3 py-2" />
        <select value={direction} onChange={(e) => setDirection(e.target.value)} className="border-2 border-gray-200 rounded-lg px-3 py-2">
          <option value="forward">forward</option>
          <option value="backward">backward</option>
          <option value="both">both</option>
        </select>
        <input type="number" min={1} max={10} value={maxDepth} onChange={(e) => setMaxDepth(e.target.value)} className="border-2 border-gray-200 rounded-lg px-3 py-2" />
        <button onClick={startTrace} disabled={loading || !source} className="px-6 py-3 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg font-semibold disabled:opacity-50">
          {loading ? 'Starting...' : 'Start Trace'}
        </button>
      </div>
      {error && <div className="text-red-600 text-sm mb-2">{error}</div>}
      {trace && (
        <div className="text-sm text-gray-800">
          <div className="mb-2"><strong>Trace ID:</strong> {trace.trace_id}</div>
          <div className="flex gap-2">
            <button onClick={() => download('json')} className="px-3 py-2 bg-gray-100 rounded">JSON</button>
            <button onClick={() => download('csv')} className="px-3 py-2 bg-gray-100 rounded">CSV</button>
            <button onClick={() => download('pdf')} className="px-3 py-2 bg-gray-100 rounded">PDF</button>
          </div>
        </div>
      )}
    </div>
  )
}

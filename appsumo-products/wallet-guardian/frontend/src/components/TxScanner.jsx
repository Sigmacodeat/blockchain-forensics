import { useState } from 'react'

export default function TxScanner() {
  const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'
  const [form, setForm] = useState({
    chain: 'ethereum',
    from_address: '',
    to_address: '',
    value: '0',
  })
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')

  const onChange = (e) => setForm({ ...form, [e.target.name]: e.target.value })

  const onSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    setResult(null)
    try {
      const res = await fetch(`${API_BASE}/api/tx/scan`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          chain: form.chain,
          from_address: form.from_address,
          to_address: form.to_address,
          value: form.value,
          data: '',
          gas: 21000,
        })
      })
      if (!res.ok) {
        const txt = await res.text()
        throw new Error(txt || 'Scan failed')
      }
      const data = await res.json()
      setResult(data)
    } catch (err) {
      setError(String(err.message || err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border-2 border-gray-100 p-6">
      <h3 className="font-bold text-gray-900 mb-4">Transaction Scanner</h3>
      <form onSubmit={onSubmit} className="grid md:grid-cols-4 gap-3 mb-4">
        <select name="chain" value={form.chain} onChange={onChange} className="border-2 border-gray-200 rounded-lg px-3 py-2">
          <option value="ethereum">Ethereum</option>
          <option value="bitcoin">Bitcoin</option>
          <option value="solana">Solana</option>
        </select>
        <input name="from_address" value={form.from_address} onChange={onChange} placeholder="From (0x...)" className="border-2 border-gray-200 rounded-lg px-3 py-2" />
        <input name="to_address" value={form.to_address} onChange={onChange} placeholder="To (0x...)" className="border-2 border-gray-200 rounded-lg px-3 py-2" />
        <input name="value" value={form.value} onChange={onChange} placeholder="Value" className="border-2 border-gray-200 rounded-lg px-3 py-2" />
        <button type="submit" disabled={loading} className="md:col-span-4 px-6 py-3 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg font-semibold disabled:opacity-50">
          {loading ? 'Scanning...' : 'Scan Transaction'}
        </button>
      </form>
      {error && <div className="text-red-600 text-sm mb-2">{error}</div>}
      {result && (
        <div className="text-sm text-gray-800">
          <div className="mb-2"><strong>Allowed:</strong> {String(result.allowed)}</div>
          <div className="mb-2"><strong>Threat Level:</strong> {result.threat_level}</div>
          <div className="mb-2"><strong>Recommended Action:</strong> {result.recommended_action}</div>
          {Array.isArray(result.threat_types) && result.threat_types.length > 0 && (
            <div className="mb-2"><strong>Threats:</strong> {result.threat_types.join(', ')}</div>
          )}
        </div>
      )}
    </div>
  )
}

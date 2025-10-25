import { useState } from 'react'
import { Search, ArrowRight, AlertCircle, CheckCircle, Loader2, ExternalLink } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'

export default function TransactionTracer() {
  const [txHash, setTxHash] = useState('')
  const [chain, setChain] = useState('ethereum')
  const [tracing, setTracing] = useState(false)
  const [result, setResult] = useState(null)

  const chains = [
    { id: 'ethereum', name: 'Ethereum', symbol: 'ETH' },
    { id: 'polygon', name: 'Polygon', symbol: 'MATIC' },
    { id: 'bsc', name: 'BSC', symbol: 'BNB' },
    { id: 'arbitrum', name: 'Arbitrum', symbol: 'ARB' },
    { id: 'optimism', name: 'Optimism', symbol: 'OP' }
  ]

  const handleTrace = async () => {
    if (!txHash.trim()) return
    
    setTracing(true)
    setResult(null)

    try {
      const response = await fetch('http://localhost:8003/api/trace', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tx_hash: txHash, chain })
      })

      const data = await response.json()
      setResult(data)
    } catch (error) {
      setResult({ error: 'Trace failed' })
    } finally {
      setTracing(false)
    }
  }

  return (
    <div className="w-full max-w-4xl mx-auto">
      {/* Input Card */}
      <div className="bg-white rounded-xl shadow-lg border-2 border-blue-100 p-6 mb-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-12 h-12 bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg flex items-center justify-center text-white">
            <Search size={24} />
          </div>
          <div>
            <h2 className="text-xl font-bold text-gray-900">Transaction Tracer</h2>
            <p className="text-sm text-gray-600">Track transactions across chains</p>
          </div>
        </div>

        {/* Chain Selection */}
        <div className="mb-4">
          <label className="block text-sm font-semibold text-gray-700 mb-2">Chain</label>
          <div className="grid grid-cols-5 gap-2">
            {chains.map(c => (
              <button
                key={c.id}
                onClick={() => setChain(c.id)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  chain === c.id
                    ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-md'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {c.symbol}
              </button>
            ))}
          </div>
        </div>

        {/* TX Hash Input */}
        <div className="flex gap-2">
          <input
            type="text"
            value={txHash}
            onChange={(e) => setTxHash(e.target.value)}
            placeholder="Enter transaction hash (0x...)"
            className="flex-1 px-4 py-3 border-2 border-gray-200 rounded-lg focus:outline-none focus:border-blue-500 transition-colors"
          />
          <button
            onClick={handleTrace}
            disabled={!txHash.trim() || tracing}
            className="px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:opacity-90 disabled:opacity-50 transition-opacity font-semibold flex items-center gap-2"
          >
            {tracing ? (
              <>
                <Loader2 size={20} className="animate-spin" />
                Tracing...
              </>
            ) : (
              <>
                <Search size={20} />
                Trace
              </>
            )}
          </button>
        </div>
      </div>

      {/* Results */}
      <AnimatePresence>
        {result && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
          >
            <TraceResult result={result} chain={chain} />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

function TraceResult({ result, chain }) {
  if (result.error) {
    return (
      <div className="bg-red-50 border-2 border-red-200 rounded-xl p-6">
        <div className="flex items-center gap-3">
          <AlertCircle size={24} className="text-red-600" />
          <div>
            <h3 className="font-bold text-red-900">Error</h3>
            <p className="text-sm text-red-700">{result.error}</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Status Card */}
      <div className={`rounded-xl p-6 ${
        result.status === 'success' 
          ? 'bg-green-50 border-2 border-green-200' 
          : 'bg-red-50 border-2 border-red-200'
      }`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {result.status === 'success' ? (
              <CheckCircle size={32} className="text-green-600" />
            ) : (
              <AlertCircle size={32} className="text-red-600" />
            )}
            <div>
              <h3 className="text-lg font-bold">{result.status === 'success' ? 'Success' : 'Failed'}</h3>
              <p className="text-sm opacity-75">Block #{result.block_number}</p>
            </div>
          </div>
          <a
            href={`https://etherscan.io/tx/${result.tx_hash}`}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 px-4 py-2 bg-white rounded-lg hover:bg-gray-50 transition-colors text-sm font-semibold"
          >
            View on Explorer
            <ExternalLink size={16} />
          </a>
        </div>
      </div>

      {/* Transaction Details */}
      <div className="bg-white rounded-xl shadow-lg border-2 border-gray-100 p-6">
        <h3 className="text-lg font-bold text-gray-900 mb-4">Transaction Details</h3>
        
        <div className="grid grid-cols-2 gap-4">
          <DetailRow label="From" value={result.from} />
          <DetailRow label="To" value={result.to} />
          <DetailRow label="Value" value={`${result.value} ${chain.toUpperCase()}`} />
          <DetailRow label="Gas Used" value={result.gas_used} />
          <DetailRow label="Gas Price" value={`${result.gas_price} Gwei`} />
          <DetailRow label="Nonce" value={result.nonce} />
        </div>
      </div>

      {/* Hops (if multi-hop) */}
      {result.hops && result.hops.length > 0 && (
        <div className="bg-white rounded-xl shadow-lg border-2 border-gray-100 p-6">
          <h3 className="text-lg font-bold text-gray-900 mb-4">Transaction Flow</h3>
          
          <div className="space-y-3">
            {result.hops.map((hop, idx) => (
              <div key={idx} className="flex items-center gap-3 p-4 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg border border-blue-200">
                <div className="flex-shrink-0 w-8 h-8 bg-gradient-to-r from-blue-600 to-purple-600 rounded-full flex items-center justify-center text-white font-bold text-sm">
                  {idx + 1}
                </div>
                <div className="flex-1">
                  <p className="text-sm font-mono text-gray-700">{hop.address}</p>
                  <p className="text-xs text-gray-500">{hop.label || 'Unknown'}</p>
                </div>
                <div className="text-right">
                  <p className="text-sm font-bold text-gray-900">{hop.value} {chain.toUpperCase()}</p>
                  <p className="text-xs text-gray-500">{hop.type}</p>
                </div>
                {idx < result.hops.length - 1 && (
                  <ArrowRight size={20} className="text-gray-400" />
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function DetailRow({ label, value }) {
  return (
    <div className="p-3 bg-gray-50 rounded-lg">
      <p className="text-xs text-gray-600 mb-1">{label}</p>
      <p className="text-sm font-mono text-gray-900 truncate">{value}</p>
    </div>
  )
}

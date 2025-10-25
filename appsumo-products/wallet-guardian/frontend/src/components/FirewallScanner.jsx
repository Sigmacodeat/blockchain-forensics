import { useState } from 'react'
import { Shield, AlertTriangle, CheckCircle, Loader2, Zap } from 'lucide-react'
import { motion } from 'framer-motion'

export default function FirewallScanner() {
  const [address, setAddress] = useState('')
  const [scanning, setScanning] = useState(false)
  const [result, setResult] = useState(null)

  const handleScan = async () => {
    if (!address.trim()) return
    
    setScanning(true)
    setResult(null)

    try {
      const response = await fetch('http://localhost:8002/api/scan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ address })
      })

      const data = await response.json()
      setResult(data)
    } catch (error) {
      setResult({ risk: 'error', message: 'Scan failed' })
    } finally {
      setScanning(false)
    }
  }

  return (
    <div className="w-full max-w-2xl mx-auto">
      {/* Input */}
      <div className="bg-white rounded-xl shadow-lg border-2 border-purple-100 p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-12 h-12 bg-gradient-to-r from-purple-600 to-blue-600 rounded-lg flex items-center justify-center text-white">
            <Shield size={24} />
          </div>
          <div>
            <h2 className="text-xl font-bold text-gray-900">Wallet Scanner</h2>
            <p className="text-sm text-gray-600">Real-time security analysis</p>
          </div>
        </div>

        <div className="flex gap-2">
          <input
            type="text"
            value={address}
            onChange={(e) => setAddress(e.target.value)}
            placeholder="Enter wallet address (0x...)"
            className="flex-1 px-4 py-3 border-2 border-gray-200 rounded-lg focus:outline-none focus:border-purple-500 transition-colors"
          />
          <button
            onClick={handleScan}
            disabled={!address.trim() || scanning}
            className="px-6 py-3 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg hover:opacity-90 disabled:opacity-50 transition-opacity font-semibold flex items-center gap-2"
          >
            {scanning ? (
              <>
                <Loader2 size={20} className="animate-spin" />
                Scanning...
              </>
            ) : (
              <>
                <Zap size={20} />
                Scan
              </>
            )}
          </button>
        </div>
      </div>

      {/* Results */}
      {result && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-6"
        >
          <RiskResult result={result} />
        </motion.div>
      )}
    </div>
  )
}

function RiskResult({ result }) {
  const getRiskColor = (risk) => {
    switch (risk) {
      case 'safe': return 'from-green-500 to-green-600'
      case 'low': return 'from-blue-500 to-blue-600'
      case 'medium': return 'from-yellow-500 to-yellow-600'
      case 'high': return 'from-orange-500 to-orange-600'
      case 'critical': return 'from-red-500 to-red-600'
      default: return 'from-gray-500 to-gray-600'
    }
  }

  const getRiskIcon = (risk) => {
    if (risk === 'safe' || risk === 'low') return <CheckCircle size={48} />
    return <AlertTriangle size={48} />
  }

  return (
    <div className="bg-white rounded-xl shadow-lg border-2 border-purple-100 p-6">
      {/* Risk Badge */}
      <div className={`bg-gradient-to-r ${getRiskColor(result.risk)} text-white p-6 rounded-lg mb-6 flex items-center justify-between`}>
        <div>
          <p className="text-sm font-semibold uppercase tracking-wide opacity-90">Risk Level</p>
          <h3 className="text-3xl font-bold capitalize mt-1">{result.risk}</h3>
          <p className="text-sm opacity-90 mt-2">Score: {result.score}/100</p>
        </div>
        <div className="opacity-80">
          {getRiskIcon(result.risk)}
        </div>
      </div>

      {/* Threats */}
      {result.threats && result.threats.length > 0 && (
        <div className="mb-6">
          <h4 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
            <AlertTriangle size={18} className="text-orange-600" />
            Detected Threats
          </h4>
          <div className="space-y-2">
            {result.threats.map((threat, idx) => (
              <div key={idx} className="flex items-center gap-3 p-3 bg-red-50 border border-red-200 rounded-lg">
                <div className="w-2 h-2 bg-red-500 rounded-full"></div>
                <span className="text-sm text-gray-700">{threat}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Security Checks */}
      <div>
        <h4 className="font-semibold text-gray-900 mb-3">Security Checks</h4>
        <div className="grid grid-cols-2 gap-3">
          {result.checks && Object.entries(result.checks).map(([key, value]) => (
            <div key={key} className="flex items-center gap-2 p-3 bg-gray-50 rounded-lg">
              {value ? (
                <CheckCircle size={16} className="text-green-600" />
              ) : (
                <AlertTriangle size={16} className="text-red-600" />
              )}
              <span className="text-sm text-gray-700 capitalize">{key.replace(/_/g, ' ')}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

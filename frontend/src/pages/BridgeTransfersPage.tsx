import { useState, useMemo } from 'react'
import { useBridgeLinks, useBridgeStats } from '@/hooks/useBridge'
import { Download, RefreshCcw, Search, TrendingUp, Users, ArrowLeftRight, AlertCircle, Loader2 } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { motion } from 'framer-motion'
import {
  LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, ResponsiveContainer,
  PieChart, Pie, Cell, Legend
} from 'recharts'

export default function BridgeTransfersPage() {
  const { t } = useTranslation()
  const [address, setAddress] = useState('')
  const [chainFrom, setChainFrom] = useState('')
  const [chainTo, setChainTo] = useState('')
  const [limit, setLimit] = useState(100)

  const { data, isLoading, error, refetch, isFetching } = useBridgeLinks({
    address: address.trim() || undefined,
    chain_from: chainFrom.trim() || undefined,
    chain_to: chainTo.trim() || undefined,
    limit,
  })

  const links = data?.links ?? []

  // Stats for KPIs/Charts
  const { data: stats } = useBridgeStats()
  const chainDistData = useMemo(() => {
    const dist = stats?.chain_distribution || {}
    return Object.entries(dist).map(([chain, count]) => ({ name: chain, value: count as number }))
  }, [stats])
  const topBridgeData = useMemo(() => {
    return (stats?.top_bridges || []).map((b) => ({
      name: `${b.bridge_name} (${b.chain_from}→${b.chain_to})`,
      txs: b.transaction_count,
    }))
  }, [stats])
  const COLORS = ['#6366F1','#10B981','#F59E0B','#EF4444','#06B6D4','#8B5CF6','#22C55E','#F97316']

  const csv = useMemo(() => {
    if (!links.length) return ''
    const header = ['from_address','to_address','chain_from','chain_to','bridge_name','tx_hash','timestamp','value']
    const rows = links.map(l => [
      l.from_address,
      l.to_address,
      l.chain_from,
      l.chain_to,
      l.bridge_name,
      l.tx_hash,
      String(l.timestamp ?? ''),
      l.value != null ? String(l.value) : ''
    ])
    return [header, ...rows].map(r => r.map(v => `"${String(v).replace(/"/g, '""')}` ).join(',')).join('\n')
  }, [links])

  const downloadCsv = () => {
    if (!csv) return
    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'bridge_links.csv'
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-slate-50 dark:from-slate-950 dark:via-slate-900 dark:to-slate-950 py-8" role="main">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <h1 className="text-4xl font-bold tracking-tight bg-gradient-to-r from-primary-600 via-purple-600 to-blue-600 bg-clip-text text-transparent mb-2">
            {t('bridge.title', 'Bridge Transfers')}
          </h1>
          <p className="text-slate-600 dark:text-slate-400 text-lg">
            {t('bridge.subtitle', 'Analysiere Cross-Chain Bridge-Links und Transaktionen')}
          </p>
        </motion.div>

        {/* KPI Cards */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="grid gap-6 md:grid-cols-3 mb-8"
        >
          {/* Total Transactions */}
          <div className="group bg-card p-6 rounded-xl shadow-lg border border-border hover:shadow-xl transition-all duration-300 hover:-translate-y-1">
            <div className="flex items-center justify-between mb-4">
              <div className="p-3 bg-gradient-to-br from-primary-100 to-purple-100 dark:from-primary-900/30 dark:to-purple-900/30 rounded-xl group-hover:scale-110 transition-transform">
                <ArrowLeftRight className="h-6 w-6 text-primary-600 dark:text-primary-400" />
              </div>
              <TrendingUp className="h-5 w-5 text-emerald-500" />
            </div>
            <div className="text-sm font-medium text-slate-600 dark:text-slate-400 mb-1">
              {t('bridge.kpi.total_transactions', 'Gesamt Bridge-Transaktionen')}
            </div>
            <div className="text-3xl font-bold text-slate-900 dark:text-white" aria-live="polite">
              {stats?.total_bridge_transactions?.toLocaleString() ?? '–'}
            </div>
          </div>

          {/* Unique Addresses */}
          <div className="group bg-white dark:bg-slate-800 p-6 rounded-xl shadow-lg border border-slate-200 dark:border-slate-700 hover:shadow-xl transition-all duration-300 hover:-translate-y-1">
            <div className="flex items-center justify-between mb-4">
              <div className="p-3 bg-gradient-to-br from-blue-100 to-cyan-100 dark:from-blue-900/30 dark:to-cyan-900/30 rounded-xl group-hover:scale-110 transition-transform">
                <Users className="h-6 w-6 text-blue-600 dark:text-blue-400" />
              </div>
            </div>
            <div className="text-sm font-medium text-slate-600 dark:text-slate-400 mb-1">
              {t('bridge.kpi.unique_addresses', 'Einzigartige Adressen')}
            </div>
            <div className="text-3xl font-bold text-slate-900 dark:text-white" aria-live="polite">
              {stats?.unique_addresses?.toLocaleString() ?? '–'}
            </div>
          </div>

          {/* Top Bridges */}
          <div className="group bg-white dark:bg-slate-800 p-6 rounded-xl shadow-lg border border-slate-200 dark:border-slate-700 hover:shadow-xl transition-all duration-300 hover:-translate-y-1">
            <div className="flex items-center justify-between mb-4">
              <div className="p-3 bg-gradient-to-br from-emerald-100 to-teal-100 dark:from-emerald-900/30 dark:to-teal-900/30 rounded-xl group-hover:scale-110 transition-transform">
                <TrendingUp className="h-6 w-6 text-emerald-600 dark:text-emerald-400" />
              </div>
            </div>
            <div className="text-sm font-medium text-slate-600 dark:text-slate-400 mb-1">
              {t('bridge.kpi.top_bridges', 'Unterstützte Bridges')}
            </div>
            <div className="text-3xl font-bold text-slate-900 dark:text-white" aria-live="polite">
              {stats?.top_bridges?.length ?? 0}
            </div>
          </div>
        </motion.div>

        {/* Charts */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="grid gap-6 md:grid-cols-2 mb-8"
        >
          {/* Chain Distribution */}
          <div className="bg-card p-6 rounded-xl shadow-lg border border-border" role="figure" aria-label="Verteilung nach Quell-Chain">
            <h3 className="text-base font-semibold mb-4 text-slate-900 dark:text-white">
              {t('bridge.charts.chain_distribution', 'Verteilung nach Quell-Chain')}
            </h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={chainDistData} dataKey="value" nameKey="name" outerRadius={90} label>
                    {chainDistData.map((entry, idx) => (
                      <Cell key={`cell-${idx}`} fill={COLORS[idx % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: 'rgba(15, 23, 42, 0.9)', 
                      border: '1px solid rgba(148, 163, 184, 0.2)',
                      borderRadius: '8px',
                      color: '#fff'
                    }}
                  />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Top Bridges */}
          <div className="bg-card p-6 rounded-xl shadow-lg border border-border" role="figure" aria-label="Top Bridges nach Transaktionen">
            <h3 className="text-base font-semibold mb-4 text-slate-900 dark:text-white">
              {t('bridge.charts.top_bridges', 'Top Bridges nach Transaktionen')}
            </h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={topBridgeData} margin={{ top: 8, right: 16, bottom: 8, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.2)" />
                  <XAxis dataKey="name" hide />
                  <YAxis stroke="rgba(148, 163, 184, 0.5)" />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: 'rgba(15, 23, 42, 0.9)', 
                      border: '1px solid rgba(148, 163, 184, 0.2)',
                      borderRadius: '8px',
                      color: '#fff'
                    }}
                  />
                  <Line type="monotone" dataKey="txs" stroke="#6366F1" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </motion.div>

        {/* Filter Section */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="bg-card p-6 rounded-xl shadow-lg border border-border mb-8"
        >
          <h3 className="text-lg font-semibold mb-4 text-slate-900 dark:text-white">
            {t('bridge.filter.title', 'Filter & Suche')}
          </h3>
          <form className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4" onSubmit={(e) => { e.preventDefault(); void refetch() }}>
            <div>
              <label className="block text-sm font-medium mb-2 text-slate-700 dark:text-slate-300" htmlFor="address">
                {t('bridge.filter.address', 'Adresse')}
              </label>
              <input 
                id="address" 
                value={address} 
                onChange={(e) => setAddress(e.target.value)} 
                placeholder="0x..." 
                className="w-full px-4 py-2.5 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-white placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:ring-2 focus:ring-primary-500 dark:focus:ring-primary-600 focus:border-transparent transition-all" 
                aria-label="Adresse filtern" 
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2 text-slate-700 dark:text-slate-300" htmlFor="chain_from">
                {t('bridge.filter.chain_from', 'Quelle (Chain)')}
              </label>
              <input 
                id="chain_from" 
                value={chainFrom} 
                onChange={(e) => setChainFrom(e.target.value)} 
                placeholder="ethereum, solana..." 
                className="w-full px-4 py-2.5 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-white placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:ring-2 focus:ring-primary-500 dark:focus:ring-primary-600 focus:border-transparent transition-all" 
                aria-label="Quellchain filtern" 
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2 text-slate-700 dark:text-slate-300" htmlFor="chain_to">
                {t('bridge.filter.chain_to', 'Ziel (Chain)')}
              </label>
              <input 
                id="chain_to" 
                value={chainTo} 
                onChange={(e) => setChainTo(e.target.value)} 
                placeholder="polygon, arbitrum..." 
                className="w-full px-4 py-2.5 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-white placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:ring-2 focus:ring-primary-500 dark:focus:ring-primary-600 focus:border-transparent transition-all" 
                aria-label="Zielchain filtern" 
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2 text-slate-700 dark:text-slate-300" htmlFor="limit">
                {t('bridge.filter.limit', 'Limit')}
              </label>
              <input 
                id="limit" 
                type="number" 
                min={1} 
                max={1000} 
                value={limit} 
                onChange={(e) => setLimit(parseInt(e.target.value || '100', 10))} 
                className="w-full px-4 py-2.5 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-white focus:ring-2 focus:ring-primary-500 dark:focus:ring-primary-600 focus:border-transparent transition-all" 
                aria-label="Limit" 
              />
            </div>
            <div className="sm:col-span-2 lg:col-span-4 flex flex-wrap gap-3">
              <button 
                type="submit" 
                className="px-5 py-2.5 rounded-lg bg-gradient-to-r from-primary-600 to-purple-600 hover:from-primary-700 hover:to-purple-700 text-white font-medium flex items-center gap-2 shadow-lg hover:shadow-xl transition-all duration-300" 
                aria-label="Suchen"
              >
                <Search className="w-4 h-4" />
                {t('bridge.filter.search', 'Suchen')}
              </button>
              <button 
                type="button" 
                onClick={() => { setAddress(''); setChainFrom(''); setChainTo(''); setLimit(100); void refetch() }} 
                className="px-5 py-2.5 rounded-lg bg-slate-100 dark:bg-slate-700 hover:bg-slate-200 dark:hover:bg-slate-600 text-slate-700 dark:text-slate-200 font-medium flex items-center gap-2 transition-all" 
                aria-label="Zurücksetzen"
              >
                <RefreshCcw className="w-4 h-4" />
                {t('bridge.filter.reset', 'Zurücksetzen')}
              </button>
              <button 
                type="button" 
                disabled={!links.length} 
                onClick={downloadCsv} 
                className="px-5 py-2.5 rounded-lg bg-emerald-100 dark:bg-emerald-900/30 hover:bg-emerald-200 dark:hover:bg-emerald-900/50 text-emerald-700 dark:text-emerald-400 font-medium flex items-center gap-2 transition-all disabled:opacity-50 disabled:cursor-not-allowed" 
                aria-label="Export CSV"
              >
                <Download className="w-4 h-4" />
                {t('bridge.filter.export', 'CSV Export')}
              </button>
            </div>
          </form>
        </motion.div>

        {/* Loading & Error States */}
        {isLoading || isFetching ? (
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex flex-col items-center justify-center py-16 text-center" 
            role="status" 
            aria-live="polite"
          >
            <Loader2 className="h-12 w-12 text-primary-600 dark:text-primary-400 animate-spin mb-4" />
            <p className="text-slate-600 dark:text-slate-400 text-lg font-medium">
              {t('bridge.loading', 'Lade Bridge-Links...')}
            </p>
          </motion.div>
        ) : error ? (
          <motion.div 
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-8 text-center" 
            role="alert"
          >
            <AlertCircle className="h-12 w-12 text-red-600 dark:text-red-400 mx-auto mb-4" />
            <p className="text-red-700 dark:text-red-400 text-lg font-semibold mb-2">
              {t('bridge.error.title', 'Fehler beim Laden')}
            </p>
            <p className="text-red-600 dark:text-red-500 text-sm">
              {t('bridge.error.message', 'Die Bridge-Links konnten nicht geladen werden. Bitte versuche es erneut.')}
            </p>
          </motion.div>
        ) : null}

        {/* Table */}
        {!isLoading && !isFetching && !error && (
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="bg-card rounded-xl shadow-lg border border-border overflow-hidden"
          >
            <div className="overflow-x-auto">
              <table className="min-w-full">
                <thead className="bg-muted border-b border-border">
                  <tr>
                    <th className="text-left px-4 py-3 text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
                      {t('bridge.table.time', 'Zeit')}
                    </th>
                    <th className="text-left px-4 py-3 text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
                      {t('bridge.table.bridge', 'Bridge')}
                    </th>
                    <th className="text-left px-4 py-3 text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
                      {t('bridge.table.from_address', 'Von (Addr)')}
                    </th>
                    <th className="text-left px-4 py-3 text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
                      {t('bridge.table.to_address', 'Nach (Addr)')}
                    </th>
                    <th className="text-left px-4 py-3 text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
                      {t('bridge.table.chain_from', 'Chain Von')}
                    </th>
                    <th className="text-left px-4 py-3 text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
                      {t('bridge.table.chain_to', 'Chain Nach')}
                    </th>
                    <th className="text-left px-4 py-3 text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
                      {t('bridge.table.tx_hash', 'Tx Hash')}
                    </th>
                    <th className="text-left px-4 py-3 text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
                      {t('bridge.table.value', 'Wert')}
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200 dark:divide-slate-700">
                  {links.map((l, idx) => (
                    <tr key={idx} className="hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors">
                      <td className="px-4 py-3 text-sm text-slate-900 dark:text-slate-100 whitespace-nowrap">
                        {typeof l.timestamp === 'number' ? new Date(l.timestamp * 1000).toLocaleString() : new Date(l.timestamp).toLocaleString()}
                      </td>
                      <td className="px-4 py-3 text-sm text-slate-900 dark:text-slate-100 whitespace-nowrap">
                        <span className="px-2.5 py-1 bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-400 rounded-lg font-medium">
                          {l.bridge_name}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-xs font-mono text-slate-600 dark:text-slate-400 max-w-xs truncate">
                        {l.from_address}
                      </td>
                      <td className="px-4 py-3 text-xs font-mono text-slate-600 dark:text-slate-400 max-w-xs truncate">
                        {l.to_address}
                      </td>
                      <td className="px-4 py-3 text-sm text-slate-900 dark:text-slate-100 whitespace-nowrap">
                        <span className="px-2 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 rounded text-xs font-medium">
                          {l.chain_from}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-sm text-slate-900 dark:text-slate-100 whitespace-nowrap">
                        <span className="px-2 py-1 bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400 rounded text-xs font-medium">
                          {l.chain_to}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-xs font-mono">
                        <a 
                          href={`https://explorer.io/tx/${l.tx_hash}`} 
                          target="_blank" 
                          rel="noreferrer" 
                          className="text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300 hover:underline transition-colors"
                        >
                          {l.tx_hash.slice(0, 10)}...
                        </a>
                      </td>
                      <td className="px-4 py-3 text-sm text-slate-900 dark:text-slate-100 whitespace-nowrap">
                        {l.value ?? '–'}
                      </td>
                    </tr>
                  ))}
                  {!links.length && (
                    <tr>
                      <td colSpan={8} className="px-4 py-12 text-center">
                        <div className="flex flex-col items-center justify-center text-slate-500 dark:text-slate-400">
                          <ArrowLeftRight className="h-12 w-12 mb-3 opacity-30" />
                          <p className="text-lg font-medium mb-1">
                            {t('bridge.table.no_data', 'Keine Daten gefunden')}
                          </p>
                          <p className="text-sm">
                            {t('bridge.table.no_data_hint', 'Versuche es mit anderen Filterkriterien')}
                          </p>
                        </div>
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </motion.div>
        )}
      </div>
    </div>
  )
}

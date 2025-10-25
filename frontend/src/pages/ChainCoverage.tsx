import { useMutation, useQuery } from '@tanstack/react-query'
import api from '@/lib/api'
import LoadingSpinner from '@/components/ui/LoadingSpinner'
import ErrorMessage from '@/components/ui/error-message'
import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'

interface CoverageResponse {
  chains: Array<{
    name: string
    type: string
    status: string
    features: string[]
    native_asset: string
    explorer: string
  }>
  bridges: Array<{ name: string; chains: string[]; status: string }>
  mixers: Array<{ name: string; chains?: string[]; chain?: string; status: string }>
  dexes: Array<{ name: string; chains: string[]; status: string }>
  adapters: Record<string, { module: string; status: string }>
  version: string
}

const statusClass = (s: string) => {
  switch (s) {
    case 'ready':
    case 'paths':
      return 'bg-green-100 text-green-800'
    case 'beta':
    case 'heuristics':
      return 'bg-yellow-100 text-yellow-800'
    case 'planned':
    default:
      return 'bg-gray-100 text-gray-800'
  }
}

function TestUtilities() {
  const { t } = useTranslation()
  const [sig, setSig] = useState<string>('')
  const [sigCanon, setSigCanon] = useState<string>('')
  const [btcHeight, setBtcHeight] = useState<string>('820000')
  const [btcTxid, setBtcTxid] = useState<string>('')
  const [ethHash, setEthHash] = useState<string>('')
  const [labelChain, setLabelChain] = useState<string>('ethereum')
  const [labelAddress, setLabelAddress] = useState<string>('')
  const [labelText, setLabelText] = useState<string>('')
  const [labelCategory, setLabelCategory] = useState<string>('generic')
  const [compChain, setCompChain] = useState<string>('ethereum')
  const [compAddress, setCompAddress] = useState<string>('')
  const [compFilterChain, setCompFilterChain] = useState<string>('')
  const [compFilterAddress, setCompFilterAddress] = useState<string>('')
  const [compWatchPage, setCompWatchPage] = useState<number>(1)
  const [compWatchTotal, setCompWatchTotal] = useState<number>(0)
  const [watchSortKey, setWatchSortKey] = useState<'chain' | 'address' | 'reason' | 'created_at'>('created_at')
  const [watchSortDir, setWatchSortDir] = useState<'asc' | 'desc'>('desc')
  const [metricsText, setMetricsText] = useState<string>('')
  const [btcEdgesMethod, setBtcEdgesMethod] = useState<'proportional' | 'heuristic'>('proportional')
  const [solTransfersPage, setSolTransfersPage] = useState<number>(1)
  const [btcEdgesPage, setBtcEdgesPage] = useState<number>(1)
  const pageSize = 10
  const [toast, setToast] = useState<{ type: 'success' | 'error'; text: string } | null>(null)
  const showToast = (type: 'success' | 'error', text: string) => {
    setToast({ type, text })
    window.setTimeout(() => setToast(null), 3000)
  }

  const exportCsv = (filename: string, headers: string[], rows: (string | number)[][]) => {
    try {
      const csv = [headers.join(','), ...rows.map(r => r.map(v => typeof v === 'string' && v.includes(',') ? `"${v}"` : String(v)).join(','))].join('\n')
      const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
      showToast('success', `CSV exportiert: ${filename}`)
    } catch {
      showToast('error', 'CSV-Export fehlgeschlagen')
    }
  }

  // Note: solBlock removed as unused after cleanup

  

  // Monitoring: fetch /metrics snapshot
  const metricsFetch = useMutation({
    mutationFn: async () => {
      // use raw fetch to preserve text/plain
      const res = await fetch('/metrics')
      const text = await res.text()
      return text
    },
    onSuccess: (text: string) => setMetricsText(text),
    onError: () => showToast('error', 'Metrics laden fehlgeschlagen')
  })

  const solTx = useMutation({
    mutationFn: async (signature: string) => {
      const res = await api.get(`/api/v1/chain/solana/tx`, { params: { signature } })
      return res.data
    },
  })

  const solTxCanonical = useMutation({
    mutationFn: async (signature: string) => {
      const res = await api.get(`/api/v1/chain/solana/tx/canonical`, { params: { signature } })
      return res.data
    },
  })

  const btcBlock = useMutation({
    mutationFn: async (h: number) => {
      const res = await api.get(`/api/v1/chain/bitcoin/block`, { params: { height: h } })
      return res.data
    },
  })

  const btcTx = useMutation({
    mutationFn: async (txid: string) => {
      const res = await api.get(`/api/v1/chain/bitcoin/tx`, { params: { txid } })
      return res.data
    },
  })

  const btcTxNorm = useMutation({
    mutationFn: async (txid: string) => {
      const res = await api.get(`/api/v1/chain/bitcoin/tx/normalized`, { params: { txid } })
      return res.data
    },
  })

  const btcTxEdges = useMutation({
    mutationFn: async ({ txid, method }: { txid: string; method: 'proportional' | 'heuristic' }) => {
      const res = await api.get(`/api/v1/chain/bitcoin/tx/edges`, { params: { txid, method } })
      return res.data
    },
  })

  const ethTx = useMutation({
    mutationFn: async (hash: string) => {
      const res = await api.get(`/api/v1/chain/ethereum/tx`, { params: { hash } })
      return res.data
    },
  })

  const ethTxCanonical = useMutation({
    mutationFn: async (hash: string) => {
      const res = await api.get(`/api/v1/chain/ethereum/tx/canonical`, { params: { hash } })
      return res.data
    },
  })

  // Graph ingestion
  const ingestCanonical = useMutation({
    mutationFn: async (payload: any) => {
      const res = await api.post(`/api/v1/graph/ingest/canonical`, { event: payload })
      return res.data
    },
    onSuccess: () => showToast('success', 'Canonical in Graph ingestiert'),
    onError: () => showToast('error', 'Canonical Ingest fehlgeschlagen')
  })

  const ingestBtcEdges = useMutation({
    mutationFn: async (payload: any) => {
      const res = await api.post(`/api/v1/graph/ingest/bitcoin/edges`, payload)
      return res.data
    },
    onSuccess: () => showToast('success', 'Edges in Graph ingestiert'),
    onError: () => showToast('error', 'Edges Ingest fehlgeschlagen')
  })

  // Helpers
  const copy = (val: string) => navigator.clipboard?.writeText(val).catch(() => {})
  const solAddr = (addr: string) => `https://solscan.io/account/${addr}`
  const solMint = (mint: string) => `https://solscan.io/token/${mint}`
  const btcTxUrl = (txid: string) => `https://mempool.space/tx/${txid}`
  const ethTxUrl = (hash: string) => `https://etherscan.io/tx/${hash}`
  const ethAddrUrl = (addr: string) => `https://etherscan.io/address/${addr}`
  const btcAddrUrl = (addr: string) => `https://mempool.space/address/${addr}`
  const watchAddrUrl = (chain: string, addr: string) => {
    switch ((chain || '').toLowerCase()) {
      case 'ethereum':
        return ethAddrUrl(addr)
      case 'solana':
        return solAddr(addr)
      case 'bitcoin':
        return btcAddrUrl(addr)
      default:
        return ''
    }
  }

  const labelsLookup = useMutation({
    mutationFn: async ({ chain, address }: { chain: string; address: string }) => {
      const res = await api.get(`/api/v1/labels/`, { params: { chain, address } })
      return res.data
    },
  })

  const labelsAdd = useMutation({
    mutationFn: async (payload: { chain: string; address: string; label: string; category: string }) => {
      const res = await api.post(`/api/v1/labels/`, payload)
      return res.data
    },
    onSuccess: () => showToast('success', 'Label gespeichert'),
    onError: () => showToast('error', 'Label speichern fehlgeschlagen')
  })

  const compScreen = useMutation({
    mutationFn: async ({ chain, address }: { chain: string; address: string }) => {
      const res = await api.get(`/api/v1/compliance/screen`, { params: { chain, address } })
      return res.data
    },
    onSuccess: () => showToast('success', 'Compliance Screening fertig'),
    onError: () => showToast('error', 'Compliance Screening fehlgeschlagen')
  })

  const compWatchAdd = useMutation({
    mutationFn: async ({ chain, address, reason }: { chain: string; address: string; reason: string }) => {
      const res = await api.post(`/api/v1/compliance/watchlist`, { chain, address, reason })
      return res.data
    },
    onSuccess: () => showToast('success', 'Zur Watchlist hinzugefügt'),
    onError: () => showToast('error', 'Watchlist-Update fehlgeschlagen')
  })

  const compWatchList = useMutation({
    mutationFn: async (params?: { chain?: string; address?: string; limit?: number; offset?: number }) => {
      const res = await api.get(`/api/v1/compliance/watchlist`, { params })
      return res.data
    },
    onSuccess: (data: any) => {
      setCompWatchTotal(Number(data?.total ?? (data?.items?.length || 0)))
    },
    onError: () => showToast('error', 'Watchlist laden fehlgeschlagen')
  })

  // Reset pagination when filters or data change
  useEffect(() => {
    setCompWatchPage(1)
  }, [compFilterChain, compFilterAddress, compWatchList.data])

  return (
    <div className="space-y-4">
      {toast && (
        <div
          className={`p-2 rounded text-xs ${toast.type === 'success' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}
        >
          {toast.text}
        </div>
      )}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-4 bg-card border border-border rounded-lg">
          <h3 className="font-medium text-gray-900 mb-2">{t('coverage.monitoring.title', 'Monitoring (Snapshot)')}</h3>
          <div className="flex items-center gap-2">
            <button className="btn btn-primary" onClick={() => metricsFetch.mutate()}>
              {t('coverage.monitoring.fetch', 'Fetch Metrics')}
            </button>
          </div>
          {metricsFetch.isPending && <p className="text-xs text-gray-500 mt-2">{t('common.loading', 'Loading...')}</p>}
          {metricsText && (
            <div className="mt-2 text-xs">
              <h4 className="font-semibold mb-1">{t('coverage.monitoring.key_counters', 'Key Counters')}</h4>
              <pre className="bg-card p-2 border border-border rounded overflow-auto max-h-40">
{metricsText
  .split('\n')
  .filter((l) => (
    l.startsWith('chain_requests_total') ||
    l.startsWith('label_requests_total') ||
    l.startsWith('compliance_requests_total')
  ) && !l.startsWith('#'))
  .join('\n')}
              </pre>
            </div>
          )}
        </div>

        <div className="p-4 bg-card border border-border rounded-lg">
          <h3 className="font-medium text-gray-900 mb-2">{t('coverage.solana.title', 'Solana Tx')}</h3>
          <div className="flex items-center gap-2">
            <input
              className="input input-bordered w-full"
              placeholder={t('coverage.solana.signature_ph', 'Signature')}
              value={sig}
              onChange={(e) => setSig(e.target.value)}
            />
            <button
              className="btn btn-primary"
              onClick={() => sig && solTx.mutate(sig)}
              disabled={!sig}
            >
              {t('coverage.actions.fetch', 'Fetch')}
            </button>
          </div>
          {solTx.isPending && <p className="text-xs text-gray-500 mt-2">{t('common.loading', 'Loading...')}</p>}
          {solTx.data && (
            <pre className="mt-2 text-xs overflow-auto max-h-40 bg-card p-2 border border-border rounded">
              {JSON.stringify(solTx.data, null, 2)}
            </pre>
          )}
          {solTx.error && <p className="text-xs text-red-600 mt-2">{t('coverage.solana.error', 'Error fetching transaction')}</p>}
        </div>

        <div className="p-4 bg-card border border-border rounded-lg">
          <h3 className="font-medium text-gray-900 mb-2">{t('coverage.solana.canonical_title', 'Solana Tx (Canonical)')}</h3>
          <div className="flex items-center gap-2">
            <input
              className="input input-bordered w-full"
              placeholder={t('coverage.solana.signature_ph', 'Signature')}
              value={sigCanon}
              onChange={(e) => setSigCanon(e.target.value)}
            />
            <button
              className="btn btn-primary"
              onClick={() => sigCanon && solTxCanonical.mutate(sigCanon)}
              disabled={!sigCanon}
            >
              {t('coverage.actions.fetch', 'Fetch')}
            </button>
          </div>
          {solTxCanonical.isPending && (
            <div className="mt-2 space-y-2">
              <div className="h-4 bg-gray-200 rounded animate-pulse" />
              <div className="h-4 bg-gray-200 rounded animate-pulse" />
              <div className="h-4 bg-gray-200 rounded animate-pulse" />
            </div>
          )}
          {solTxCanonical.data && (
            <>
              <pre className="mt-2 text-xs overflow-auto max-h-40 bg-card p-2 border border-border rounded">
                {JSON.stringify(solTxCanonical.data, null, 2)}
              </pre>
              <div className="mt-2 flex items-center gap-2">
                <button
                  className="btn btn-accent btn-sm"
                  onClick={() =>
                    solTxCanonical.data?.canonical && ingestCanonical.mutate(solTxCanonical.data.canonical)
                  }
                >
                  {t('coverage.solana.ingest_canonical', 'Ingest Canonical → Graph')}
                </button>
                {ingestCanonical.isPending && (
                  <span className="text-xs text-gray-500">{t('coverage.ingest.loading', 'Ingesting...')}</span>
                )}
              </div>
              {/* Transfers Table */}
              {solTxCanonical.data?.canonical?.metadata?.transfers?.length ? (
                <div className="mt-2">
                  <h4 className="text-xs font-semibold text-gray-800 mb-1">{t('coverage.solana.transfers', 'Transfers')}</h4>
                  <div className="overflow-auto border rounded">
                    <table className="min-w-full text-xs">
                      <thead className="bg-muted text-gray-700">
                        <tr>
                          <th className="px-2 py-1 text-left">{t('coverage.table.mint', 'Mint')}</th>
                          <th className="px-2 py-1 text-left">{t('coverage.table.from', 'From')}</th>
                          <th className="px-2 py-1 text-left">{t('coverage.table.to', 'To')}</th>
                          <th className="px-2 py-1 text-right">{t('coverage.table.amount_ui', 'Amount (UI)')}</th>
                          <th className="px-2 py-1 text-right">{t('coverage.table.decimals', 'Decimals')}</th>
                          <th className="px-2 py-1 text-right">{t('coverage.table.actions', 'Actions')}</th>
                        </tr>
                      </thead>
                      <tbody>
                        {solTxCanonical.data.canonical.metadata.transfers
                          .slice((solTransfersPage - 1) * pageSize, solTransfersPage * pageSize)
                          .map((t: any, idx: number) => (
                          <tr key={idx} className="border-t">
                            <td className="px-2 py-1 break-all">
                              <a className="text-primary-600 hover:underline" href={solMint(t.mint)} target="_blank" rel="noreferrer">{t.mint}</a>
                            </td>
                            <td className="px-2 py-1 break-all">
                              <a className="text-primary-600 hover:underline" href={solAddr(t.from)} target="_blank" rel="noreferrer">{t.from}</a>
                            </td>
                            <td className="px-2 py-1 break-all">
                              <a className="text-primary-600 hover:underline" href={solAddr(t.to)} target="_blank" rel="noreferrer">{t.to}</a>
                            </td>
                            <td className="px-2 py-1 text-right">{t.amount_ui}</td>
                            <td className="px-2 py-1 text-right">{t.decimals ?? '-'}</td>
                            <td className="px-2 py-1 text-right">
                              <button className="btn btn-xs" onClick={() => copy(`${t.mint}`)}>{t('coverage.actions.copy_mint', 'Copy Mint')}</button>
                            </td>
                          </tr>
                          ))}
                      </tbody>
                    </table>
                  </div>
                  {/* Export + Totals + Pagination */}
                  <div className="flex items-center justify-between gap-2 mt-2 text-xs text-gray-700">
                    <div className="flex items-center gap-2">
                      <button
                        className="btn btn-xs"
                        onClick={() => {
                          const all = solTxCanonical.data.canonical.metadata.transfers as any[]
                          const page = all.slice((solTransfersPage - 1) * pageSize, solTransfersPage * pageSize)
                          const rows = page.map(t => [t.mint, t.from, t.to, t.amount_ui, t.decimals ?? ''])
                          exportCsv('solana_transfers_page.csv', ['mint','from','to','amount_ui','decimals'], rows)
                        }}
                      >
                        {t('coverage.actions.export_csv_page', 'Export CSV (Page)')}
                      </button>
                      {(() => {
                        const all = solTxCanonical.data.canonical.metadata.transfers as any[]
                        const page = all.slice((solTransfersPage - 1) * pageSize, solTransfersPage * pageSize)
                        const sumAll = all.reduce((a, b) => a + (Number(b.amount_ui) || 0), 0)
                        const sumPage = page.reduce((a, b) => a + (Number(b.amount_ui) || 0), 0)
                        return (
                          <span>
                            {t('coverage.totals.total_amount', 'Total Amount')}: <b>{sumAll}</b> • {t('coverage.totals.page_sum', 'Page Sum')}: <b>{sumPage}</b>
                          </span>
                        )
                      })()}
                    </div>
                    <div className="flex items-center gap-2">
                      <button className="btn btn-xs" disabled={solTransfersPage === 1} onClick={() => setSolTransfersPage((p) => Math.max(1, p - 1))}>{t('common.prev', 'Prev')}</button>
                      <span>
                        {t('common.page', 'Page')} {solTransfersPage} / {Math.max(1, Math.ceil(solTxCanonical.data.canonical.metadata.transfers.length / pageSize))}
                      </span>
                      <button
                        className="btn btn-xs"
                        disabled={solTransfersPage >= Math.ceil(solTxCanonical.data.canonical.metadata.transfers.length / pageSize)}
                        onClick={() => setSolTransfersPage((p) => p + 1)}
                      >
                        {t('common.next', 'Next')}
                      </button>
                    </div>
                  </div>
                  {ingestCanonical.data && (
                    <div className="mt-2 text-xs text-green-700">{t('coverage.ingest.canonical_notice', 'Canonical Event wurde in den Graphen ingestiert.')}</div>
                  )}
                </div>
              ) : null}
            </>
          )}
          {solTxCanonical.error && <p className="text-xs text-red-600 mt-2">{t('coverage.solana.canonical_error', 'Error fetching canonical tx')}</p>}
        </div>

        <div className="p-4 bg-card border border-border rounded-lg">
          <h3 className="font-medium text-gray-900 mb-2">{t('coverage.bitcoin.block_title', 'Bitcoin Block')}</h3>
          <div className="flex items-center gap-2">
            <input
              className="input input-bordered w-full"
              placeholder={t('coverage.bitcoin.height_ph', 'Height')}
              value={btcHeight}
              onChange={(e) => setBtcHeight(e.target.value)}
            />
            <button
              className="btn btn-primary"
              onClick={() => btcBlock.mutate(Number(btcHeight))}
            >
              {t('coverage.actions.fetch', 'Fetch')}
            </button>
          </div>
          {btcBlock.isPending && <p className="text-xs text-gray-500 mt-2">{t('common.loading', 'Loading...')}</p>}
          {btcBlock.data && (
            <pre className="mt-2 text-xs overflow-auto max-h-40 bg-card p-2 border border-border rounded">
              {JSON.stringify(btcBlock.data, null, 2)}
            </pre>
          )}
          {btcBlock.error && (
            <p className="text-xs text-yellow-700 mt-2">{t('coverage.rpc_unavailable', 'RPC nicht konfiguriert oder nicht erreichbar')}</p>
          )}
        </div>

        <div className="p-4 bg-card border border-border rounded-lg">
          <h3 className="font-medium text-gray-900 mb-2">{t('coverage.bitcoin.tx_title', 'Bitcoin Tx')}</h3>
          <div className="flex items-center gap-2">
            <input
              className="input input-bordered w-full"
              placeholder={t('coverage.bitcoin.txid_ph', 'TxID')}
              value={btcTxid}
              onChange={(e) => setBtcTxid(e.target.value)}
            />
            <button
              className="btn btn-secondary"
              onClick={() => btcTxid && btcTx.mutate(btcTxid)}
              disabled={!btcTxid}
            >
              {t('coverage.bitcoin.decoded', 'Decoded')}
            </button>
            <button
              className="btn btn-primary"
              onClick={() => btcTxid && btcTxNorm.mutate(btcTxid)}
              disabled={!btcTxid}
            >
              {t('coverage.bitcoin.normalized', 'Normalized')}
            </button>
          </div>
          {(btcTx.isPending || btcTxNorm.isPending) && (
            <p className="text-xs text-gray-500 mt-2">{t('common.loading', 'Loading...')}</p>
          )}
          {(btcTx.data || btcTxNorm.data) && (
            <pre className="mt-2 text-xs overflow-auto max-h-40 bg-card p-2 border border-border rounded">
              {JSON.stringify(btcTxNorm.data ?? btcTx.data, null, 2)}
            </pre>
          )}
          {(btcTx.error || btcTxNorm.error) && (
            <p className="text-xs text-yellow-700 mt-2">{t('coverage.rpc_unavailable', 'RPC nicht konfiguriert oder nicht erreichbar')}</p>
          )}
        </div>

        <div className="p-4 bg-card border border-border rounded-lg">
          <h3 className="font-medium text-gray-900 mb-2">{t('coverage.bitcoin.edges_title', 'Bitcoin Tx (Edges)')}</h3>
          <div className="flex items-center gap-2">
            <input
              className="input input-bordered w-full"
              placeholder={t('coverage.bitcoin.txid_ph', 'TxID')}
              value={btcTxid}
              onChange={(e) => setBtcTxid(e.target.value)}
            />
            <select
              className="select select-bordered"
              value={btcEdgesMethod}
              onChange={(e) => setBtcEdgesMethod(e.target.value as 'proportional' | 'heuristic')}
            >
              <option value="proportional">{t('coverage.bitcoin.method_proportional', 'proportional')}</option>
              <option value="heuristic">{t('coverage.bitcoin.method_heuristic', 'heuristic')}</option>
            </select>
            <button
              className="btn btn-primary"
              onClick={() => btcTxid && btcTxEdges.mutate({ txid: btcTxid, method: btcEdgesMethod })}
              disabled={!btcTxid}
            >
              {t('coverage.bitcoin.compute', 'Compute')}
            </button>
          </div>
          {btcTxEdges.isPending && (
            <div className="mt-2 space-y-2">
              <div className="h-4 bg-gray-200 rounded animate-pulse" />
              <div className="h-4 bg-gray-200 rounded animate-pulse" />
              <div className="h-4 bg-gray-200 rounded animate-pulse" />
            </div>
          )}
          {btcTxEdges.data && (
            <>
              <div className="mt-2 flex items-center gap-2">
                <button
                  className="btn btn-accent btn-sm"
                  onClick={() => ingestBtcEdges.mutate(btcTxEdges.data)}
                >
                  {t('coverage.bitcoin.ingest_edges', 'Ingest Edges → Graph')}
                </button>
                {ingestBtcEdges.isPending && (
                  <span className="text-xs text-gray-500">{t('coverage.ingest.loading', 'Ingesting...')}</span>
                )}
              </div>
              <div className="mt-2 overflow-auto border rounded">
                <table className="min-w-full text-xs">
                  <thead className="bg-muted text-gray-700">
                    <tr>
                      <th className="px-2 py-1 text-left">{t('coverage.table.from_vout', 'From (txid:vout)')}</th>
                      <th className="px-2 py-1 text-left">{t('coverage.table.to_vout', 'To (txid:vout)')}</th>
                      <th className="px-2 py-1 text-right">{t('coverage.table.value_btc', 'Value (BTC)')}</th>
                      <th className="px-2 py-1 text-right">{t('coverage.table.method', 'Method')}</th>
                      <th className="px-2 py-1 text-right">{t('coverage.table.fee', 'Fee')}</th>
                      <th className="px-2 py-1 text-right">{t('coverage.table.actions', 'Actions')}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {btcTxEdges.data.edges
                      ?.slice((btcEdgesPage - 1) * pageSize, btcEdgesPage * pageSize)
                      .map((e: any, idx: number) => (
                      <tr key={idx} className="border-t">
                        <td className="px-2 py-1 break-all">
                          <a className="text-primary-600 hover:underline" href={btcTxUrl(e.from.txid)} target="_blank" rel="noreferrer">{e.from.txid}</a>:{e.from.vout}
                        </td>
                        <td className="px-2 py-1 break-all">
                          <a className="text-primary-600 hover:underline" href={btcTxUrl(e.to.txid)} target="_blank" rel="noreferrer">{e.to.txid}</a>:{e.to.vout}
                        </td>
                        <td className="px-2 py-1 text-right">{e.value?.toFixed ? e.value.toFixed(8) : e.value}</td>
                        <td className="px-2 py-1 text-right">{btcTxEdges.data.method || '-'}</td>
                        <td className="px-2 py-1 text-right">{btcTxEdges.data.fee ?? '-'}</td>
                        <td className="px-2 py-1 text-right">
                          <button className="btn btn-xs" onClick={() => copy(`${e.from.txid}:${e.from.vout}`)}>{t('coverage.actions.copy_from', 'Copy From')}</button>
                        </td>
                      </tr>
                      ))}
                  </tbody>
                </table>
              </div>
              {/* Export + Totals + Pagination */}
              <div className="flex items-center justify-between gap-2 mt-2 text-xs text-gray-700">
                <div className="flex items-center gap-2">
                  <button
                    className="btn btn-xs"
                    onClick={() => {
                      const all = (btcTxEdges.data.edges || []) as any[]
                      const page = all.slice((btcEdgesPage - 1) * pageSize, btcEdgesPage * pageSize)
                      const rows = page.map(e => [`${e.from.txid}:${e.from.vout}`, `${e.to.txid}:${e.to.vout}`, Number(e.value) || 0, btcTxEdges.data.method || '', btcTxEdges.data.fee ?? ''])
                      exportCsv('bitcoin_edges_page.csv', ['from','to','value_btc','method','fee'], rows)
                    }}
                  >
                    {t('coverage.actions.export_csv_page', 'Export CSV (Page)')}
                  </button>
                  {(() => {
                    const all = (btcTxEdges.data.edges || []) as any[]
                    const page = all.slice((btcEdgesPage - 1) * pageSize, btcEdgesPage * pageSize)
                    const sumAll = all.reduce((a, b) => a + (Number(b.value) || 0), 0)
                    const sumPage = page.reduce((a, b) => a + (Number(b.value) || 0), 0)
                    return (
                      <span>
                        {t('coverage.totals.total_value_btc', 'Total Value')}: <b>{sumAll.toFixed(8)}</b> BTC • {t('coverage.totals.page_sum_btc', 'Page Sum')}: <b>{sumPage.toFixed(8)}</b> BTC
                      </span>
                    )
                  })()}
                </div>
                <div className="flex items-center gap-2">
                  <button className="btn btn-xs" disabled={btcEdgesPage === 1} onClick={() => setBtcEdgesPage((p) => Math.max(1, p - 1))}>{t('common.prev', 'Prev')}</button>
                  <span>
                    {t('common.page', 'Page')} {btcEdgesPage} / {Math.max(1, Math.ceil((btcTxEdges.data.edges?.length || 0) / pageSize))}
                  </span>
                  <button
                    className="btn btn-xs"
                    disabled={btcEdgesPage >= Math.ceil((btcTxEdges.data.edges?.length || 0) / pageSize)}
                    onClick={() => setBtcEdgesPage((p) => p + 1)}
                  >
                    {t('common.next', 'Next')}
                  </button>
                </div>
              </div>
              {ingestBtcEdges.data && (
                <div className="mt-2 text-xs text-green-700">{t('coverage.ingest.edges_notice', 'Edges wurden in den Graphen ingestiert.')}</div>
              )}
            </>
          )}
          {btcTxEdges.error && (
            <p className="text-xs text-yellow-700 mt-2">{t('coverage.rpc_unavailable', 'RPC nicht konfiguriert oder nicht erreichbar')}</p>
          )}
        </div>

        <div className="p-4 bg-card border border-border rounded-lg">
          <h3 className="font-medium text-gray-900 mb-2">{t('coverage.ethereum.tx_title', 'Ethereum Tx')}</h3>
          <div className="flex items-center gap-2">
            <input
              className="input input-bordered w-full"
              placeholder={t('coverage.ethereum.tx_hash_ph', 'Tx Hash')}
              value={ethHash}
              onChange={(e) => setEthHash(e.target.value)}
            />
            <button
              className="btn btn-secondary"
              onClick={() => ethHash && ethTx.mutate(ethHash)}
              disabled={!ethHash}
            >
              {t('coverage.ethereum.decoded', 'Decoded')}
            </button>
            <button
              className="btn btn-primary"
              onClick={() => ethHash && ethTxCanonical.mutate(ethHash)}
              disabled={!ethHash}
            >
              {t('coverage.ethereum.canonical', 'Canonical')}
            </button>
          </div>
          {(ethTx.isPending || ethTxCanonical.isPending) && (
            <p className="text-xs text-gray-500 mt-2">{t('common.loading', 'Loading...')}</p>
          )}
          {(ethTx.data || ethTxCanonical.data) && (
            <>
              <div className="mt-2 text-xs">
                {(() => {
                  const d = (ethTxCanonical.data ?? ethTx.data) as any
                  const h = d?.hash || d?.canonical?.canonical?.tx_hash || ''
                  const from = d?.canonical?.from_address || d?.from
                  const to = d?.canonical?.to_address || d?.to
                  return h ? (
                    <div className="flex items-center gap-2">
                      <a className="text-primary-600 hover:underline" href={ethTxUrl(h)} target="_blank" rel="noreferrer">{t('coverage.ethereum.open_etherscan', 'Open in Etherscan')}</a>
                      <button className="btn btn-xs" onClick={() => copy(h)}>{t('coverage.ethereum.copy_hash', 'Copy Hash')}</button>
                      {from && (
                        <a className="text-primary-600 hover:underline" href={`https://etherscan.io/address/${from}`} target="_blank" rel="noreferrer">{t('coverage.table.from', 'From')}</a>
                      )}
                      {to && (
                        <a className="text-primary-600 hover:underline" href={`https://etherscan.io/address/${to}`} target="_blank" rel="noreferrer">{t('coverage.table.to', 'To')}</a>
                      )}
                      {ethTxCanonical.data?.canonical && (
                        <button
                          className="btn btn-xs"
                          onClick={() => {
                            const c = ethTxCanonical.data.canonical as any
                            const rows = [[c.tx_hash || '', c.from_address || '', c.to_address || '', c.value || '', c.event_type || '']]
                            exportCsv('ethereum_canonical.csv', ['tx_hash','from','to','value','event_type'], rows)
                          }}
                        >
                          {t('coverage.actions.export_csv', 'Export CSV')}
                        </button>
                      )}
                    </div>
                  ) : null
                })()}
              </div>
              <pre className="mt-2 text-xs overflow-auto max-h-40 bg-card p-2 border border-border rounded">
                {JSON.stringify(ethTxCanonical.data ?? ethTx.data, null, 2)}
              </pre>
            </>
          )}
          {(ethTx.error || ethTxCanonical.error) && (
            <p className="text-xs text-red-600 mt-2">{t('coverage.ethereum.error', 'Fehler beim Laden der Transaktion')}</p>
          )}
        </div>

        <div className="p-4 bg-card border border-border rounded-lg">
          <h3 className="font-medium text-gray-900 mb-2">{t('coverage.labels.title', 'Labels (Lookup/Add)')}</h3>
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <input
                className="input input-bordered w-28"
                placeholder={t('coverage.labels.chain_ph', 'Chain')}
                value={labelChain}
                onChange={(e) => setLabelChain(e.target.value)}
              />
              <input
                className="input input-bordered w-full"
                placeholder={t('coverage.labels.address_ph', 'Address')}
                value={labelAddress}
                onChange={(e) => setLabelAddress(e.target.value)}
              />
              <button
                className="btn btn-primary"
                onClick={() => labelAddress && labelsLookup.mutate({ chain: labelChain, address: labelAddress })}
                disabled={!labelAddress}
              >
                {t('coverage.labels.lookup', 'Lookup')}
              </button>
            </div>
            <div className="flex items-center gap-2">
              <input
                className="input input-bordered w-full"
                placeholder={t('coverage.labels.label_ph', 'Label')}
                value={labelText}
                onChange={(e) => setLabelText(e.target.value)}
              />
              <input
                className="input input-bordered w-40"
                placeholder={t('coverage.labels.category_ph', 'Category')}
                value={labelCategory}
                onChange={(e) => setLabelCategory(e.target.value)}
              />
              <button
                className="btn btn-secondary"
                onClick={() => labelAddress && labelText && labelsAdd.mutate({ chain: labelChain, address: labelAddress, label: labelText, category: labelCategory })}
                disabled={!labelAddress || !labelText}
              >
                {t('coverage.labels.add', 'Add')}
              </button>
            </div>
            {(labelsLookup.isPending || labelsAdd.isPending) && (
              <p className="text-xs text-gray-500">{t('common.loading', 'Loading...')}</p>
            )}
            {(labelsLookup.data || labelsAdd.data) && (
              <pre className="mt-2 text-xs overflow-auto max-h-40 bg-card p-2 border border-border rounded">
                {JSON.stringify(labelsAdd.data ?? labelsLookup.data, null, 2)}
              </pre>
            )}
            {(labelsLookup.error || labelsAdd.error) && (
              <p className="text-xs text-red-600">{t('coverage.labels.error', 'Fehler bei Labels-Operation')}</p>
            )}
          </div>
        </div>

        <div className="p-4 bg-card border border-border rounded-lg">
          <h3 className="font-medium text-gray-900 mb-2">{t('coverage.compliance.title', 'Compliance (Screen/Watchlist)')}</h3>
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <input
                className="input input-bordered w-28"
                placeholder={t('coverage.compliance.chain_ph', 'Chain')}
                value={compChain}
                onChange={(e) => setCompChain(e.target.value)}
              />
              <input
                className="input input-bordered w-full"
                placeholder={t('coverage.compliance.address_ph', 'Address')}
                value={compAddress}
                onChange={(e) => setCompAddress(e.target.value)}
              />
              <button
                className="btn btn-primary"
                onClick={() => compAddress && compScreen.mutate({ chain: compChain, address: compAddress })}
                disabled={!compAddress}
              >
                {t('coverage.compliance.screen', 'Screen')}
              </button>
              <button
                className="btn btn-secondary"
                onClick={() => compAddress && compWatchAdd.mutate({ chain: compChain, address: compAddress, reason: 'manual' })}
                disabled={!compAddress}
              >
                {t('coverage.compliance.add_watch', 'Add Watch')}
              </button>
              <input
                className="input input-bordered w-28"
                placeholder={t('coverage.compliance.filter_chain_ph', 'Filter Chain')}
                value={compFilterChain}
                onChange={(e) => setCompFilterChain(e.target.value)}
              />
              <input
                className="input input-bordered w-full"
                placeholder={t('coverage.compliance.filter_address_ph', 'Filter Address')}
                value={compFilterAddress}
                onChange={(e) => setCompFilterAddress(e.target.value)}
              />
              <button className="btn" onClick={() => {
                const nextPage = 1
                setCompWatchPage(nextPage)
                compWatchList.mutate({
                  chain: compFilterChain || undefined,
                  address: compFilterAddress || undefined,
                  limit: pageSize,
                  offset: (nextPage - 1) * pageSize,
                })
              }}>
                {t('coverage.compliance.list_watch', 'List Watch')}
              </button>
            </div>
            {(compScreen.isPending || compWatchAdd.isPending || compWatchList.isPending) && (
              <p className="text-xs text-gray-500">{t('common.loading', 'Loading...')}</p>
            )}
            {(compScreen.data || compWatchAdd.data || compWatchList.data) && (
              <pre className="mt-2 text-xs overflow-auto max-h-40 bg-card p-2 border border-border rounded">
                {JSON.stringify(compScreen.data ?? compWatchAdd.data ?? compWatchList.data, null, 2)}
              </pre>
            )}
            {compWatchList.data?.items?.length ? (
              <div className="mt-2">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="text-xs font-semibold text-gray-800">{t('coverage.compliance.watchlist', 'Watchlist')}</h4>
                  <button
                    className="btn btn-xs"
                    onClick={() => {
                      const items = compWatchList.data.items as any[]
                      const rows = items.map(i => [i.chain, i.address, i.reason ?? '', i.created_at ?? ''])
                      exportCsv('compliance_watchlist.csv', ['chain','address','reason','created_at'], rows)
                    }}
                  >
                    {t('coverage.actions.export_csv', 'Export CSV')}
                  </button>
                </div>
                <div className="overflow-auto border rounded">
                  <table className="min-w-full text-xs">
                    <thead className="bg-muted text-gray-700">
                      <tr>
                        <th className="px-2 py-1 text-left cursor-pointer" onClick={() => { setWatchSortKey('chain'); setWatchSortDir(watchSortKey==='chain' && watchSortDir==='asc' ? 'desc':'asc') }}>
                          {t('coverage.table.chain', 'Chain')} {watchSortKey==='chain' ? (watchSortDir==='asc' ? '▲' : '▼') : ''}
                        </th>
                        <th className="px-2 py-1 text-left cursor-pointer" onClick={() => { setWatchSortKey('address'); setWatchSortDir(watchSortKey==='address' && watchSortDir==='asc' ? 'desc':'asc') }}>
                          {t('coverage.table.address', 'Address')} {watchSortKey==='address' ? (watchSortDir==='asc' ? '▲' : '▼') : ''}
                        </th>
                        <th className="px-2 py-1 text-left cursor-pointer" onClick={() => { setWatchSortKey('reason'); setWatchSortDir(watchSortKey==='reason' && watchSortDir==='asc' ? 'desc':'asc') }}>
                          {t('coverage.table.reason', 'Reason')} {watchSortKey==='reason' ? (watchSortDir==='asc' ? '▲' : '▼') : ''}
                        </th>
                        <th className="px-2 py-1 text-left cursor-pointer" onClick={() => { setWatchSortKey('created_at'); setWatchSortDir(watchSortKey==='created_at' && watchSortDir==='asc' ? 'desc':'asc') }}>
                          {t('coverage.table.created', 'Created')} {watchSortKey==='created_at' ? (watchSortDir==='asc' ? '▲' : '▼') : ''}
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {([...compWatchList.data.items] as any[])
                        .sort((a,b) => {
                          const k = watchSortKey
                          const av = a[k] ?? ''
                          const bv = b[k] ?? ''
                          if (av === bv) return 0
                          if (watchSortDir === 'asc') return av > bv ? 1 : -1
                          return av < bv ? 1 : -1
                        })
                        .map((i: any, idx: number) => (
                        <tr key={idx} className="border-t">
                          <td className="px-2 py-1 capitalize"><span className="px-2 py-0.5 rounded-full bg-gray-100 border text-gray-700">{i.chain}</span></td>
                          <td className="px-2 py-1 break-all">
                            {watchAddrUrl(i.chain, i.address) ? (
                              <a className="text-primary-600 hover:underline" href={watchAddrUrl(i.chain, i.address)} target="_blank" rel="noreferrer">{i.address}</a>
                            ) : (
                              i.address
                            )}
                            <button className="btn btn-ghost btn-xs ml-2" onClick={() => copy(i.address)}>Copy</button>
                          </td>
                          <td className="px-2 py-1">{i.reason ?? ''}</td>
                          <td className="px-2 py-1">{i.created_at ?? ''}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <div className="flex items-center justify-between gap-2 mt-2 text-xs text-gray-700">
                  <div>
                    {t('coverage.compliance.entries', 'Einträge')}: <b>{compWatchTotal}</b>
                  </div>
                  <div className="flex items-center gap-2">
                    <button className="btn btn-xs" disabled={compWatchPage === 1} onClick={() => {
                      const nextPage = Math.max(1, compWatchPage - 1)
                      setCompWatchPage(nextPage)
                      compWatchList.mutate({
                        chain: compFilterChain || undefined,
                        address: compFilterAddress || undefined,
                        limit: pageSize,
                        offset: (nextPage - 1) * pageSize,
                      })
                    }}>{t('common.prev', 'Prev')}</button>
                    <span>
                      {t('common.page', 'Page')} {compWatchPage} / {Math.max(1, Math.ceil((compWatchTotal || 0) / pageSize))}
                    </span>
                    <button className="btn btn-xs"
                      disabled={compWatchPage >= Math.ceil((compWatchTotal || 0) / pageSize)}
                      onClick={() => {
                        const nextPage = compWatchPage + 1
                        setCompWatchPage(nextPage)
                        compWatchList.mutate({
                          chain: compFilterChain || undefined,
                          address: compFilterAddress || undefined,
                          limit: pageSize,
                          offset: (nextPage - 1) * pageSize,
                        })
                      }}
                    >{t('common.next', 'Next')}</button>
                  </div>
                </div>
              </div>
            ) : null}
            {(compScreen.error || compWatchAdd.error || compWatchList.error) && (
              <p className="text-xs text-red-600">{t('coverage.compliance.error', 'Fehler bei Compliance-Operation')}</p>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default function ChainCoverage() {
  const { data, isPending, error } = useQuery<CoverageResponse>({
    queryKey: ['coverage'],
    queryFn: async () => {
      const res = await api.get('/api/v1/coverage/')
      return res.data
    },
    staleTime: 60_000,
  })

  const { data: bridges } = useQuery<{ bridges: any[] }>({
    queryKey: ['coverage-bridges'],
    queryFn: async () => {
      const res = await api.get('/api/v1/coverage/bridges')
      return res.data
    },
    staleTime: 5 * 60_000,
  })

  const { data: mixers } = useQuery<{ mixers: any[] }>({
    queryKey: ['coverage-mixers'],
    queryFn: async () => {
      const res = await api.get('/api/v1/coverage/mixers')
      return res.data
    },
    staleTime: 5 * 60_000,
  })

  const { data: health } = useQuery<{ [k: string]: { status: string; rpc?: boolean; module?: string } }>({
    queryKey: ['coverage-health'],
    queryFn: async () => {
      const res = await api.get('/api/v1/coverage/health')
      return res.data
    },
    staleTime: 30_000,
  })

  if (isPending) {
    return (
      <div className="flex items-center justify-center py-16">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  if (error || !data) {
    return <ErrorMessage message="Coverage konnte nicht geladen werden" />
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Test Utilities */}
      <div className="card p-6 mb-8">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Test Utilities</h2>
        <TestUtilities />
      </div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Chain Coverage</h1>
        <p className="text-gray-600">Version {data.version}</p>
      </div>

      {/* Chains */}
      <div className="card p-6 mb-8">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Chains</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {data.chains.map((c) => (
            <div key={c.name} className="p-4 bg-gray-50 rounded-lg">
              <div className="flex items-center justify-between mb-2">
                <div>
                  <p className="text-sm text-gray-500">{c.type}</p>
                  <h3 className="text-base font-semibold text-gray-900 capitalize">{c.name}</h3>
                </div>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusClass(c.status)}`}>
                  {c.status}
                </span>
              </div>
              <p className="text-sm text-gray-600 mb-2">Native: {c.native_asset}</p>
              <div className="text-xs mb-2">
                <a
                  className="text-primary-600 hover:underline"
                  href={c.explorer}
                  target="_blank"
                  rel="noreferrer"
                >
                  Open Explorer
                </a>
              </div>
              <div className="flex flex-wrap gap-1">
                {c.features.map((f) => (
                  <span key={f} className="px-2 py-1 bg-white border border-gray-200 rounded text-xs text-gray-700">
                    {f}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Bridges & Mixers */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <div className="card p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Bridges</h2>
          <div className="space-y-3">
            {(bridges?.bridges ?? data.bridges).map((b) => (
              <div key={b.name} className="p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center justify-between">
                  <div className="min-w-0">
                    <h3 className="font-medium text-gray-900 truncate" title={b.name}>{b.name}</h3>
                    <p className="text-xs text-gray-600">Chains: {(b.chains || []).join(', ')}</p>
                  </div>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusClass(b.status)}`}>
                    {b.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
        <div className="card p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Mixers</h2>
          <div className="space-y-3">
            {(mixers?.mixers ?? data.mixers).map((m) => (
              <div key={m.name} className="p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center justify-between">
                  <div className="min-w-0">
                    <h3 className="font-medium text-gray-900 truncate" title={m.name}>{m.name}</h3>
                    <p className="text-xs text-gray-600">
                      Chains: {(m.chains ?? (m.chain ? [m.chain] : [])).join(', ') || '—'}
                    </p>
                  </div>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusClass(m.status)}`}>
                    {m.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Adapters */}
      <div className="card p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Adapters</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {Object.entries(data.adapters).map(([k, v]) => (
            <div key={k} className="p-4 bg-gray-50 rounded-lg">
              <div className="flex items-center justify-between mb-2">
                <h3 className="font-medium text-gray-900 capitalize">{k}</h3>
                <span
                  className={`px-2 py-1 rounded-full text-xs font-medium ${statusClass(
                    health?.[k]?.rpc ? 'ready' : v.status
                  )}`}
                  title={`module: ${v.module}${health?.[k]?.rpc ? ' • rpc: connected' : ''}`}
                >
                  {health?.[k]?.rpc ? 'ready' : v.status}
                </span>
              </div>
              <p className="text-xs text-gray-600 break-all">{v.module}</p>
              {health?.[k] && (
                <div className="mt-2 flex items-center gap-2 text-xs">
                  <span
                    className={`inline-flex items-center px-2 py-0.5 rounded-full ${
                      health[k].rpc ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-700'
                    }`}
                  >
                    {health[k].rpc ? 'RPC Connected' : 'RPC Not Configured'}
                  </span>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

import React, { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useNewsCaseStream } from '@/hooks/useNewsCaseStream'
import RiskCopilot from '@/components/RiskCopilot'

function formatTime(ts?: number) {
  if (!ts) return ''
  try { return new Date(ts * 1000).toLocaleString() } catch { return '' }
}

function explorerUrl(chain: string, kind: 'address' | 'tx', value: string): string | null {
  const c = (chain || '').toLowerCase()
  switch (c) {
    case 'ethereum':
    case 'base':
    case 'arbitrum':
    case 'optimism':
    case 'polygon':
    case 'bsc': {
      // Etherscan-Familie / ähnliche
      const map: Record<string, string> = {
        ethereum: 'https://etherscan.io',
        base: 'https://basescan.org',
        arbitrum: 'https://arbiscan.io',
        optimism: 'https://optimistic.etherscan.io',
        polygon: 'https://polygonscan.com',
        bsc: 'https://bscscan.com',
      }
      const root = map[c]
      if (!root) return null
      return `${root}/${kind === 'address' ? 'address' : 'tx'}/${value}`
    }
    case 'gnosis':
      return `https://gnosisscan.io/${kind === 'address' ? 'address' : 'tx'}/${value}`
    case 'bitcoin':
      return `https://www.blockchain.com/explorer/transactions/btc/${value}`
    case 'solana':
      return `https://solscan.io/${kind === 'address' ? 'account' : 'tx'}/${value}`
    case 'tron':
      return `https://tronscan.org/#/${kind === 'address' ? 'address' : 'transaction'}/${value}`
    default:
      return null
  }
}

function Badge({ children, color = 'bg-emerald-600' }: { children: React.ReactNode; color?: string }) {
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium text-white ${color}`}>{children}</span>
  )
}

const levelColor: Record<string, string> = {
  critical: 'bg-red-600',
  high: 'bg-orange-500',
  medium: 'bg-yellow-500',
  low: 'bg-emerald-500',
  safe: 'bg-emerald-400',
}

export default function NewsCasePublicPage() {
  const { slug, lang } = useParams()
  const { connected, error, snapshot, events, connect } = useNewsCaseStream(slug)
  const [wasConnectedOnce, setWasConnectedOnce] = useState(false)

  useEffect(() => {
    if (connected) {
      setWasConnectedOnce(true)
    }
  }, [connected])

  return (
    <div className="min-h-[70vh] py-10">
      <div className="container mx-auto max-w-5xl px-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold">News Case</h1>
            <div className="text-slate-500 mt-1 flex items-center gap-2">
              <span>Slug: <code className="bg-slate-100 px-1 rounded">{slug}</code></span>
              {snapshot?.auto_trace && (
                <Badge color="bg-indigo-600">Auto-Trace aktiv</Badge>
              )}
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Badge color={connected ? 'bg-emerald-600' : 'bg-slate-500'}>
              {connected ? 'live' : 'offline'}
            </Badge>
            {error && <span className="text-sm text-red-600">{error}</span>}
          </div>
        </div>

        {wasConnectedOnce && !connected && (
          <div className="mt-4 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800 dark:border-amber-500/40 dark:bg-amber-500/10 dark:text-amber-200">
            <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
              <div>
                Verbindung unterbrochen. Wir versuchen automatisch, die Verbindung wiederherzustellen.
                {error && <span className="ml-1 font-medium">Letzter Fehler: {error}</span>}
              </div>
              <button
                type="button"
                onClick={() => connect()}
                className="inline-flex items-center justify-center rounded-md border border-amber-300 bg-white px-3 py-1.5 text-sm font-medium text-amber-700 shadow-sm transition hover:bg-amber-100 dark:border-amber-400/40 dark:bg-transparent dark:text-amber-100"
              >
                Jetzt neu verbinden
              </button>
            </div>
          </div>
        )}

        {snapshot && (
          <div className="mt-6 rounded-lg border border-slate-200 dark:border-slate-800 p-4 bg-white dark:bg-slate-900">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-lg font-medium">{snapshot.name}</div>
                {snapshot.description && <div className="text-sm text-slate-600 dark:text-slate-400 mt-0.5">{snapshot.description}</div>}
              </div>
              <div className="text-xs text-slate-500">Stand: {formatTime(snapshot.generated_at)}</div>
            </div>

            <div className="mt-4">
              <div className="text-sm font-medium text-slate-600 dark:text-slate-300 mb-2">Beobachtete Adressen</div>
              <div className="grid md:grid-cols-2 gap-3">
                {snapshot.addresses.map((a) => (
                  <div key={a.chain + ':' + a.address} className="rounded-md border border-slate-200 dark:border-slate-800 p-3 bg-slate-50/50 dark:bg-slate-900/50">
                    <div className="flex items-center justify-between gap-3">
                      <div className="text-sm font-medium">{a.chain}</div>
                      <div className="flex items-center gap-2">
                        <RiskCopilot chain={a.chain} address={a.address} variant="badge" />
                        {typeof a.balance === 'number' && (
                          <div className="text-xs text-slate-500">Balance: {a.balance}</div>
                        )}
                      </div>
                    </div>
                    <div className="mt-1 font-mono text-xs break-all">{a.address}</div>
                    <div className="mt-2 flex items-center gap-3 text-xs">
                      {explorerUrl(a.chain, 'address', a.address) && (
                        <a href={explorerUrl(a.chain, 'address', a.address) as string} target="_blank" rel="noreferrer" className="text-primary-600">Im Explorer öffnen</a>
                      )}
                      <Link to={`/${lang || 'en'}/investigator?address=${encodeURIComponent(a.address)}&chain=${encodeURIComponent(a.chain)}`} className="text-primary-600">Im Investigator öffnen</Link>
                    </div>
                    {a.latest_tx && (
                      <div className="mt-2 text-xs text-slate-600 dark:text-slate-400">
                        <div className="font-medium">Letzte Transaktion</div>
                        <div className="mt-0.5 grid gap-0.5">
                          {'tx_hash' in a.latest_tx && <div>Hash: <span className="font-mono">{a.latest_tx.tx_hash}</span></div>}
                          {'txid' in a.latest_tx && <div>TxID: <span className="font-mono">{a.latest_tx.txid}</span></div>}
                          {'from_address' in a.latest_tx && <div>From: <span className="font-mono">{a.latest_tx.from_address}</span></div>}
                          {'to_address' in a.latest_tx && <div>To: <span className="font-mono">{a.latest_tx.to_address}</span></div>}
                          {'value' in a.latest_tx && <div>Value: {a.latest_tx.value}</div>}
                          {('tx_hash' in a.latest_tx) && explorerUrl(a.chain, 'tx', (a.latest_tx as any).tx_hash) && (
                            <div>
                              <a href={explorerUrl(a.chain, 'tx', (a.latest_tx as any).tx_hash) as string} target="_blank" rel="noreferrer" className="text-primary-600">TX im Explorer</a>
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        <div className="mt-8">
          <div className="flex items-center justify-between">
            <div className="text-sm font-medium text-slate-600 dark:text-slate-300">Live-Events</div>
            <div className="text-xs text-slate-500">Neueste zuerst</div>
          </div>
          <div className="mt-2 space-y-2">
            {events.length === 0 && (
              <div className="text-sm text-slate-500">Noch keine Ereignisse…</div>
            )}
            {events.map((e, idx) => (
              <div key={idx} className="rounded-md border border-slate-200 dark:border-slate-800 p-3 bg-white dark:bg-slate-900">
                {e.type === 'news_case.tx' && (
                  <div className="space-y-1">
                    <div className="flex items-center justify-between">
                      <div className="text-sm font-medium">Neue Transaktion</div>
                      <div className="text-xs text-slate-500">{formatTime(e.timestamp)}</div>
                    </div>
                    <div className="grid md:grid-cols-2 gap-1 text-xs">
                      <div>Chain: <span className="font-mono">{e.chain}</span></div>
                      <div>Adresse: <span className="font-mono break-all">{e.address}</span></div>
                      {'from_address' in e.tx && <div>From: <span className="font-mono break-all">{(e.tx as any).from_address}</span></div>}
                      {'to_address' in e.tx && <div>To: <span className="font-mono break-all">{(e.tx as any).to_address}</span></div>}
                      {'value' in e.tx && <div>Value: {(e.tx as any).value}</div>}
                      {'tx_hash' in e.tx && <div>Hash: <span className="font-mono break-all">{(e.tx as any).tx_hash}</span></div>}
                      {'txid' in e.tx && <div>TxID: <span className="font-mono break-all">{(e.tx as any).txid}</span></div>}
                    </div>
                    {('trace_hint' in e) && (e as any).trace_hint?.source_address && (
                      <div className="pt-1">
                        <Link to={`/${lang || 'en'}/investigator?address=${encodeURIComponent((e as any).trace_hint.source_address)}&chain=${encodeURIComponent((e as any).trace_hint.chain || e.chain)}&auto_trace=true`} className="text-xs text-primary-600">Trace öffnen</Link>
                      </div>
                    )}
                  </div>
                )}

                {e.type === 'news_case.kyt' && (
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <div className={`h-2.5 w-2.5 rounded-full ${levelColor[e.risk_level] || 'bg-slate-400'}`} />
                        <div className="text-sm font-medium">KYT Analyse</div>
                      </div>
                      <div className="text-xs text-slate-500">{formatTime(e.timestamp)}</div>
                    </div>
                    <div className="text-xs text-slate-600 dark:text-slate-400">Risk: {Math.round(e.risk_score * 100)} / 100 ({e.risk_level})</div>
                    <div className="grid md:grid-cols-2 gap-1 text-xs">
                      {('from_labels' in e) && (e as any).from_labels?.length > 0 && (
                        <div>From Labels: {(e as any).from_labels.slice(0,5).join(', ')}{(e as any).from_labels.length > 5 ? '…' : ''}</div>
                      )}
                      {('to_labels' in e) && (e as any).to_labels?.length > 0 && (
                        <div>To Labels: {(e as any).to_labels.slice(0,5).join(', ')}{(e as any).to_labels.length > 5 ? '…' : ''}</div>
                      )}
                    </div>
                    {('trace_hint' in e) && (e as any).trace_hint?.source_address && (
                      <div>
                        <Link to={`/${lang || 'en'}/investigator?address=${encodeURIComponent((e as any).trace_hint.source_address)}&chain=${encodeURIComponent((e as any).trace_hint.chain || 'ethereum')}&auto_trace=true`} className="text-xs text-primary-600">Trace öffnen</Link>
                      </div>
                    )}
                    {e.alerts && e.alerts.length > 0 && (
                      <div className="text-xs">
                        <div className="font-medium">Alerts</div>
                        <ul className="list-disc pl-5 space-y-0.5">
                          {e.alerts.map((a, i) => (
                            <li key={i} className="text-slate-700 dark:text-slate-200">
                              {a.title || a.type}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                )}

                {e.type === 'news_case.status' && (
                  <div className="text-xs text-slate-500">Status-Update empfangen.</div>
                )}

                {e.type === 'error' && (
                  <div className="text-xs text-red-600">Fehler: {e.detail}</div>
                )}
              </div>
            ))}
          </div>
        </div>

        <div className="mt-10 text-xs text-slate-500">
          <Link to={`/${(slug ? '' : '')}`}></Link>
          Hinweis: Dieses öffentliche Dashboard kann per Slug geteilt werden.
        </div>
      </div>
    </div>
  )
}

// Utilities for exporting Universal Screening results
// JSON, CSV and Print-to-PDF (via window.print)

export interface ChainResult {
  risk_score?: number
  risk_level?: string
  is_sanctioned?: boolean
  transaction_count?: number
  total_value_usd?: number
  counterparties?: number
  labels?: any[]
  [k: string]: any
}

export interface UniversalScreeningResult {
  address?: string
  screening_timestamp?: string
  total_chains_checked?: number
  aggregate_risk_score?: number
  aggregate_risk_level?: string
  summary?: {
    total_transactions?: number
    total_value_usd?: number
    unique_counterparties?: number
  }
  chain_results?: Record<string, ChainResult>
  [k: string]: any
}

function safeFilename(base: string, ext: string): string {
  const sanitized = (base || '')
    .replace(/\s+/g, '-')
    .replace(/[^a-zA-Z0-9-_]/g, '')
    .slice(0, 64) || 'report'
  return `${sanitized}.${ext}`
}

export function exportJSON(result: UniversalScreeningResult, filename?: string) {
  const name = filename || safeFilename(`universal-screening-${(result.address || 'address').slice(0, 12)}`, 'json')
  const blob = new Blob([JSON.stringify(result, null, 2)], { type: 'application/json;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = name
  document.body.appendChild(a)
  try {
    a.click()
  } finally {
    URL.revokeObjectURL(url)
    a.remove()
  }
}

export function exportCSV(result: UniversalScreeningResult, opts?: { delimiter?: string; decimal?: string }) {
  try {
    const rows: string[] = []
    const D = opts?.delimiter ?? ','
    const DEC = opts?.decimal ?? '.'
    // Summary header
    rows.push(['address', 'total_chains_checked', 'aggregate_risk_score', 'aggregate_risk_level', 'total_transactions', 'total_value_usd', 'unique_counterparties'].join(D))
    rows.push([
      safe(result.address),
      safe(result.total_chains_checked),
      numberWithDec(result.aggregate_risk_score, DEC),
      safe(result.aggregate_risk_level),
      numberWithDec(result.summary?.total_transactions, DEC),
      numberWithDec(result.summary?.total_value_usd, DEC),
      numberWithDec(result.summary?.unique_counterparties, DEC),
    ].join(D))

    // Blank line
    rows.push('')

    // Chain breakdown header
    rows.push(['chain_id', 'risk_score', 'risk_level', 'is_sanctioned', 'transaction_count', 'total_value_usd', 'counterparties', 'labels_count'].join(D))
    const chainEntries = Object.entries(result?.chain_results || {}) as [string, any][]
    for (const [chainId, chain] of chainEntries) {
      rows.push([
        safe(chainId),
        numberWithDec(chain?.risk_score, DEC),
        safe(chain.risk_level),
        safe(chain?.is_sanctioned),
        numberWithDec(chain?.transaction_count, DEC),
        numberWithDec(chain?.total_value_usd, DEC),
        numberWithDec(chain?.counterparties, DEC),
        numberWithDec((chain?.labels || []).length, DEC),
      ].join(D))
    }

    // Prepend BOM for Excel compatibility
    const BOM = '\uFEFF'
    const blob = new Blob([BOM + rows.join('\n')], { type: 'text/csv;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = safeFilename(`universal-screening-${(result.address || 'address').slice(0, 12)}`, 'csv')
    document.body.appendChild(link)
    link.click()
    link.remove()
    URL.revokeObjectURL(url)
  } catch (e) {
    console.error('exportCSV failed', e)
  }
}

export function exportPrintPDF(result: UniversalScreeningResult) {
  // Open a minimal printable document and trigger print (user can save as PDF)
  const win = window.open('', '_blank')
  if (!win) return
  const styles = `
    body { font-family: ui-sans-serif, system-ui, -apple-system; padding: 24px; }
    h1 { font-size: 20px; margin-bottom: 8px; }
    h2 { font-size: 16px; margin-top: 16px; margin-bottom: 8px; }
    table { border-collapse: collapse; width: 100%; margin-top: 8px; }
    th, td { border: 1px solid #e5e7eb; padding: 6px 8px; text-align: left; font-size: 12px; }
    .muted { color: #6b7280; font-size: 12px; }
    @media print { a { color: inherit; text-decoration: none; } }
  `
  const chainRows = Object.entries(result?.chain_results || {})
    .map(([chainId, chain]: [string, any]) => `
      <tr>
        <td>${escapeHtml(chainId)}</td>
        <td>${escapeHtml((((chain?.risk_score ?? 0) as number) * 100).toFixed(1))}%</td>
        <td>${escapeHtml(chain?.risk_level || '')}</td>
        <td>${chain?.is_sanctioned ? 'Yes' : 'No'}</td>
        <td>${escapeHtml(chain?.transaction_count)}</td>
        <td>${escapeHtml(chain?.total_value_usd)}</td>
        <td>${escapeHtml(chain?.counterparties)}</td>
      </tr>
    `)
    .join('')

  win.document.write(`
    <html>
      <head>
        <title>Universal Screening Report</title>
        <meta charset="utf-8" />
        <style>${styles}</style>
      </head>
      <body>
        <h1>Universal Screening Report</h1>
        <div class="muted">Address: ${escapeHtml(result?.address || '')}</div>
        <div class="muted">Screened: ${escapeHtml(result?.screening_timestamp || '')}</div>
        <h2>Summary</h2>
        <table>
          <tr>
            <th>Total Chains</th><th>Risk Score</th><th>Risk Level</th><th>Transactions</th><th>Total Value (USD)</th><th>Unique Counterparties</th>
          </tr>
          <tr>
            <td>${escapeHtml(result?.total_chains_checked)}</td>
            <td>${escapeHtml((((result?.aggregate_risk_score ?? 0) as number) * 100).toFixed(1))}%</td>
            <td>${escapeHtml(result?.aggregate_risk_level || '')}</td>
            <td>${escapeHtml(result?.summary?.total_transactions)}</td>
            <td>${escapeHtml(result?.summary?.total_value_usd)}</td>
            <td>${escapeHtml(result?.summary?.unique_counterparties)}</td>
          </tr>
        </table>
        <h2>Chains</h2>
        <table>
          <tr>
            <th>Chain</th><th>Risk</th><th>Level</th><th>Sanctioned</th><th>TX</th><th>Value (USD)</th><th>Counterparties</th>
          </tr>
          ${chainRows}
        </table>
        <script>
          window.onload = function(){ setTimeout(() => window.print(), 250); };
          window.onafterprint = function(){ window.close(); };
        </script>
      </body>
    </html>
  `)
  win.document.close()
}

function safe(v: any): string {
  if (v === undefined || v === null) return ''
  if (typeof v === 'string') return '"' + v.replace(/"/g, '""') + '"'
  return String(v)
}

function numberWithDec(v: any, decimal: string): string {
  if (v === undefined || v === null || isNaN(Number(v))) return ''
  const s = String(v)
  if (decimal === ',') {
    // replace dot with comma for decimals if present
    return s.replace('.', ',')
  }
  return s
}

function escapeHtml(v: any): string {
  if (v === undefined || v === null) return ''
  return String(v)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/\"/g, '&quot;')
    .replace(/'/g, '&#039;')
}

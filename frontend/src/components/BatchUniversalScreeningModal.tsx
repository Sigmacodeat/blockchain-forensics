import React, { useState } from 'react'
import axios from 'axios'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { useTranslation } from 'react-i18next'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

interface BatchUniversalScreeningModalProps {
  isOpen: boolean
  onClose: () => void
}

interface BatchResultMap {
  [address: string]: any
}

const placeholder = `Enter one address per line (any chain):\n0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb\nbc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh\n...`

export const BatchUniversalScreeningModal: React.FC<BatchUniversalScreeningModalProps> = ({ isOpen, onClose }) => {
  const { t } = useTranslation()
  const [input, setInput] = useState<string>('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [results, setResults] = useState<BatchResultMap | null>(null)
  const [current, setCurrent] = useState(0)
  const [total, setTotal] = useState(0)
  const [failures, setFailures] = useState<Array<{ address: string; message: string }>>([])

  if (!isOpen) return null

  const parseAddresses = (): string[] => {
    return input
      .split(/\r?\n/) 
      .map(s => s.trim())
      .filter(Boolean)
      .slice(0, 50)
  }

  const onUploadCsv = async (file: File) => {
    try {
      const text = await file.text()
      // naive CSV/line parser: split on newline or comma/semicolon
      const parts = text.split(/\r?\n|,|;/).map(p => p.trim()).filter(Boolean)
      setInput(parts.slice(0, 50).join('\n'))
    } catch (e: any) {
      setError(e?.message || 'Failed to parse CSV')
    }
  }

  const onRun = async () => {
    const addresses = parseAddresses()
    if (addresses.length === 0) {
      setError(t('universal_screening.errors.enter_address', 'Please enter at least one address'))
      return
    }
    setLoading(true)
    setError(null)
    setResults({})
    setFailures([])
    setCurrent(0)
    setTotal(addresses.length)
    try {
      const token = localStorage.getItem('token')
      const headers = { Authorization: token ? `Bearer ${token}` : '' }
      const acc: BatchResultMap = {}
      let processed = 0
      for (const addr of addresses) {
        try {
          const resp = await axios.post(
            `${API_BASE_URL}/api/v1/universal-screening/screen`,
            { address: addr, chains: null, max_concurrent: 10 },
            { headers }
          )
          if (resp.data?.success) {
            acc[addr] = resp.data.data
          } else {
            setFailures(prev => [...prev, { address: addr, message: resp.data?.message || 'Failed' }])
          }
        } catch (e: any) {
          setFailures(prev => [...prev, { address: addr, message: e?.response?.data?.detail || e?.message || 'Failed' }])
        } finally {
          processed += 1
          setCurrent(processed)
          // flush partial results for live updates
          setResults({ ...acc })
        }
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50" role="dialog" aria-modal="true">
      <Card className="w-full max-w-3xl max-h-[90vh] overflow-auto">
        <CardHeader>
          <div className="flex items-center justify-between gap-2">
            <div>
              <CardTitle>{t('universal_screening.batch.title', 'Batch Universal Screening')}</CardTitle>
              <CardDescription>{t('universal_screening.batch.subtitle', 'Screen up to 50 addresses across all supported chains')}</CardDescription>
            </div>
            <Button variant="outline" size="sm" onClick={onClose}>{t('universal_screening.batch.close', 'Close')}</Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <textarea
              className="w-full h-40 p-3 rounded border bg-transparent text-sm"
              placeholder={t('universal_screening.batch.placeholder', placeholder)}
              value={input}
              onChange={(e) => setInput(e.target.value)}
            />
            <div className="mt-2 text-xs text-muted-foreground">{t('universal_screening.batch.hint', 'Max 50 addresses. One per line.')}</div>
            <div className="mt-3 flex items-center gap-2">
              <input
                id="batch-csv"
                type="file"
                accept=".csv,.txt"
                className="text-sm"
                onChange={(e) => {
                  const f = e.target.files?.[0]
                  if (f) onUploadCsv(f)
                }}
              />
              <label htmlFor="batch-csv" className="text-xs text-muted-foreground">
                {t('universal_screening.batch.csv_hint', 'Upload CSV/TXT (addresses separated by newline/comma/semicolon)')}
              </label>
            </div>
          </div>

          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          <div className="flex items-center gap-2">
            <Button onClick={onRun} disabled={loading}>
              {loading ? t('universal_screening.batch.running', 'Screening...') : t('universal_screening.batch.run', 'Run Batch')}
            </Button>
            <Button variant="outline" onClick={() => setInput('')} disabled={loading}>{t('universal_screening.batch.clear', 'Clear')}</Button>
          </div>

          {loading && (
            <div className="space-y-2">
              <Progress value={total ? (current / total) * 100 : 0} className="h-2" />
              <div className="text-xs text-muted-foreground">
                {t('universal_screening.batch.progress', '{{current}} / {{total}} processed', { current, total })}
              </div>
            </div>
          )}

          {results && (
            <div className="space-y-3">
              <div className="text-sm text-muted-foreground">
                {t('universal_screening.batch.summary', '{{success}} / {{total}} screened successfully', { success: Object.keys(results).length, total: parseAddresses().length })}
              </div>
              <div className="space-y-2">
                {Object.entries(results).map(([addr, data]) => (
                  <div key={addr} className="p-2 border rounded">
                    <div className="flex items-center justify-between">
                      <div className="text-xs font-mono truncate max-w-[60%]" title={addr}>{addr}</div>
                      <div className="text-sm font-semibold">{((data?.aggregate_risk_score || 0) * 100).toFixed(1)}%</div>
                    </div>
                    <div className="mt-1 flex flex-wrap gap-1">
                      {(data?.screened_chains || []).slice(0, 6).map((c: string, i: number) => (
                        <Badge key={`${addr}-${c}-${i}`} variant="secondary">{c}</Badge>
                      ))}
                      {((data?.screened_chains || []).length > 6) && (
                        <Badge variant="outline">+{(data?.screened_chains || []).length - 6} more</Badge>
                      )}
                    </div>
                  </div>
                ))}
              </div>

              {failures.length > 0 && (
                <div className="pt-2 border-t mt-2">
                  <div className="text-sm font-medium mb-2">{t('universal_screening.batch.errors_title', 'Errors')}</div>
                  <div className="space-y-1">
                    {failures.slice(-10).map((f, idx) => (
                      <div key={`${f.address}-${idx}`} className="text-xs text-red-600 break-all">
                        {f.address}: {f.message}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

export default BatchUniversalScreeningModal

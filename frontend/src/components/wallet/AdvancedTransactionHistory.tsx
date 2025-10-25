/*
 * Erweiterte Transaktionshistorie-Komponente
 *
 * Zeigt detaillierte Transaktionsanalyse mit KI-Insights.
 */

import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import {
  Activity,
  Search,
  Filter,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  CheckCircle,
  Clock,
  ArrowUpRight,
  ArrowDownLeft,
  Eye,
  Download,
  BarChart3,
  PieChart
} from 'lucide-react'
import { useWallet } from '@/contexts/WalletContext'
import LoadingSpinner from '@/components/ui/LoadingSpinner'
import ErrorMessage from '@/components/ui/error-message'

interface Transaction {
  hash: string
  timestamp: number
  from: string
  to: string
  value: string
  gasPrice?: string
  gasUsed?: string
  status: 'pending' | 'confirmed' | 'failed'
  analysis?: TransactionAnalysis
  chain: string
}

interface TransactionAnalysis {
  risk_score: number
  risk_factors: string[]
  money_flow: 'inflow' | 'outflow' | 'internal'
  flagged_addresses: string[]
  entity_types: string[]
  recommendations: string[]
  // Optional DEX swap enrichment (if backend provided)
  dex_router?: string
  dex_swaps?: Array<{
    pair_or_pool: string
    token0?: string
    token1?: string
    amount0_in?: string | number
    amount1_in?: string | number
    amount0_out?: string | number
    amount1_out?: string | number
  }>
}

interface TransactionSummary {
  total_transactions: number
  total_volume: string
  avg_risk_score: number
  risk_distribution: {
    low: number
    medium: number
    high: number
  }
  money_flow_distribution: {
    inflow: number
    outflow: number
    internal: number
  }
  flagged_transactions: number
}

const AdvancedTransactionHistory: React.FC = () => {
  const { state, getWalletHistory } = useWallet()
  const [transactions, setTransactions] = useState<Transaction[]>([])
  const [filteredTransactions, setFilteredTransactions] = useState<Transaction[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [riskFilter, setRiskFilter] = useState('all')
  const [sortBy, setSortBy] = useState('timestamp')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc')
  const [summary, setSummary] = useState<TransactionSummary | null>(null)

  // Simulierte Transaktionsdaten für Demo
  useEffect(() => {
    const demoTransactions: Transaction[] = [
      {
        hash: '0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef',
        timestamp: Date.now() - 86400000,
        from: '0x742d35Cc6635C0532925a3b844Bc454e4438f44e',
        to: '0xabcdef1234567890abcdef1234567890abcdef12',
        value: '1.5',
        status: 'confirmed',
        chain: 'ethereum',
        analysis: {
          risk_score: 0.2,
          risk_factors: ['normal_transaction'],
          money_flow: 'outflow',
          flagged_addresses: [],
          entity_types: ['user'],
          recommendations: ['monitor']
        }
      },
      {
        hash: '0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890',
        timestamp: Date.now() - 172800000,
        from: '0xabcdef1234567890abcdef1234567890abcdef12',
        to: '0x742d35Cc6635C0532925a3b844Bc454e4438f44e',
        value: '0.8',
        status: 'confirmed',
        chain: 'ethereum',
        analysis: {
          risk_score: 0.1,
          risk_factors: ['regular_transfer'],
          money_flow: 'inflow',
          flagged_addresses: [],
          entity_types: ['exchange'],
          recommendations: ['standard_monitoring']
        }
      },
      {
        hash: '0x7890abcdef1234567890abcdef1234567890abcdef1234567890abcdef123456',
        timestamp: Date.now() - 259200000,
        from: '0x742d35Cc6635C0532925a3b844Bc454e4438f44e',
        to: '0x4567890abcdef1234567890abcdef1234567890ab',
        value: '2.1',
        status: 'confirmed',
        chain: 'ethereum',
        analysis: {
          risk_score: 0.7,
          risk_factors: ['high_value', 'unusual_pattern', 'flagged_address'],
          money_flow: 'outflow',
          flagged_addresses: ['0x4567890abcdef1234567890abcdef1234567890ab'],
          entity_types: ['suspicious'],
          recommendations: ['investigate', 'flag_address', 'enhanced_monitoring']
        }
      }
    ]

    setTimeout(() => {
      setTransactions(demoTransactions)
      setFilteredTransactions(demoTransactions)

      // Berechne Summary
      calculateSummary(demoTransactions)
    }, 1000)
  }, [])

  const calculateSummary = (txs: Transaction[]) => {
    const totalTransactions = txs.length
    const totalVolume = txs.reduce((sum, tx) => sum + parseFloat(tx.value || '0'), 0)
    const avgRiskScore = txs.reduce((sum, tx) => sum + (tx.analysis?.risk_score || 0), 0) / totalTransactions

    const riskDistribution = { low: 0, medium: 0, high: 0 }
    const moneyFlowDistribution = { inflow: 0, outflow: 0, internal: 0 }
    let flaggedTransactions = 0

    txs.forEach(tx => {
      const riskScore = tx.analysis?.risk_score || 0
      if (riskScore < 0.3) riskDistribution.low++
      else if (riskScore < 0.7) riskDistribution.medium++
      else riskDistribution.high++

      const moneyFlow = tx.analysis?.money_flow || 'internal'
      moneyFlowDistribution[moneyFlow as keyof typeof moneyFlowDistribution]++

      if ((tx.analysis?.flagged_addresses?.length ?? 0) > 0) flaggedTransactions++
    })

    setSummary({
      total_transactions: totalTransactions,
      total_volume: totalVolume.toFixed(2),
      avg_risk_score: avgRiskScore,
      risk_distribution: riskDistribution,
      money_flow_distribution: moneyFlowDistribution,
      flagged_transactions: flaggedTransactions
    })
  }

  const applyFilters = () => {
    let filtered = [...transactions]

    // Suchfilter
    if (searchTerm) {
      filtered = filtered.filter(tx =>
        tx.hash.toLowerCase().includes(searchTerm.toLowerCase()) ||
        tx.from.toLowerCase().includes(searchTerm.toLowerCase()) ||
        tx.to.toLowerCase().includes(searchTerm.toLowerCase())
      )
    }

    // Status-Filter
    if (statusFilter !== 'all') {
      filtered = filtered.filter(tx => tx.status === statusFilter)
    }

    // Risiko-Filter
    if (riskFilter !== 'all') {
      filtered = filtered.filter(tx => {
        const riskScore = tx.analysis?.risk_score || 0
        switch (riskFilter) {
          case 'low': return riskScore < 0.3
          case 'medium': return riskScore >= 0.3 && riskScore < 0.7
          case 'high': return riskScore >= 0.7
          default: return true
        }
      })
    }

    // Sortierung
    filtered.sort((a, b) => {
      let aValue, bValue

      switch (sortBy) {
        case 'timestamp':
          aValue = a.timestamp
          bValue = b.timestamp
          break
        case 'value':
          aValue = parseFloat(a.value || '0')
          bValue = parseFloat(b.value || '0')
          break
        case 'risk_score':
          aValue = a.analysis?.risk_score || 0
          bValue = b.analysis?.risk_score || 0
          break
        default:
          aValue = a.timestamp
          bValue = b.timestamp
      }

      return sortOrder === 'asc' ? aValue - bValue : bValue - aValue
    })

    setFilteredTransactions(filtered)
  }

  useEffect(() => {
    applyFilters()
  }, [searchTerm, statusFilter, riskFilter, sortBy, sortOrder, transactions])

  const formatTimestamp = (timestamp: number) => {
    return new Date(timestamp).toLocaleString()
  }

  const getRiskBadgeColor = (score: number) => {
    if (score < 0.3) return 'success'
    if (score < 0.7) return 'warning'
    return 'destructive'
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'confirmed': return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'pending': return <Clock className="h-4 w-4 text-yellow-500" />
      case 'failed': return <AlertTriangle className="h-4 w-4 text-red-500" />
      default: return <Activity className="h-4 w-4 text-gray-500" />
    }
  }

  if (isLoading && transactions.length === 0) {
    return <LoadingSpinner />
  }

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      {summary && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Gesamttransaktionen</CardTitle>
              <Activity className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{summary.total_transactions}</div>
              <p className="text-xs text-muted-foreground">
                {summary.total_volume} ETH Gesamtvolumen
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Durchschnittliches Risiko</CardTitle>
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{(summary.avg_risk_score * 100).toFixed(1)}%</div>
              <p className="text-xs text-muted-foreground">
                KI-basierte Bewertung
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Risikoverteilung</CardTitle>
              <BarChart3 className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="flex gap-2">
                <Badge variant="success">{summary.risk_distribution.low} Niedrig</Badge>
                <Badge variant="warning">{summary.risk_distribution.medium} Mittel</Badge>
                <Badge variant="destructive">{summary.risk_distribution.high} Hoch</Badge>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Geflaggte Transaktionen</CardTitle>
              <AlertTriangle className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{summary.flagged_transactions}</div>
              <p className="text-xs text-muted-foreground">
                Erfordern Aufmerksamkeit
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Filters and Search */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Filter className="h-5 w-5" />
            Filter und Suche
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <div>
              <label className="block text-sm font-medium mb-2">Suche</label>
              <div className="relative">
                <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Hash, Adresse..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-8"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Status</label>
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Alle</SelectItem>
                  <SelectItem value="confirmed">Bestätigt</SelectItem>
                  <SelectItem value="pending">Ausstehend</SelectItem>
                  <SelectItem value="failed">Fehlgeschlagen</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Risiko</label>
              <Select value={riskFilter} onValueChange={setRiskFilter}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Alle</SelectItem>
                  <SelectItem value="low">Niedrig (&lt;30%)</SelectItem>
                  <SelectItem value="medium">Mittel (30-70%)</SelectItem>
                  <SelectItem value="high">Hoch (&gt;70%)</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Sortierung</label>
              <Select value={`${sortBy}_${sortOrder}`} onValueChange={(value) => {
                const [field, order] = value.split('_')
                setSortBy(field)
                setSortOrder(order as 'asc' | 'desc')
              }}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="timestamp_desc">Neueste zuerst</SelectItem>
                  <SelectItem value="timestamp_asc">Älteste zuerst</SelectItem>
                  <SelectItem value="value_desc">Höchster Wert</SelectItem>
                  <SelectItem value="value_asc">Niedrigster Wert</SelectItem>
                  <SelectItem value="risk_score_desc">Höchstes Risiko</SelectItem>
                  <SelectItem value="risk_score_asc">Niedrigstes Risiko</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Transaction List */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>Transaktionshistorie</span>
            <Button variant="outline" size="sm">
              <Download className="h-4 w-4 mr-2" />
              Exportieren
            </Button>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {filteredTransactions.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              Keine Transaktionen gefunden
            </div>
          ) : (
            <div className="space-y-4">
              {filteredTransactions.map(tx => (
                <div key={tx.hash} className="border rounded-lg p-4">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      {getStatusIcon(tx.status)}
                      <Badge variant="outline">{tx.status}</Badge>
                      <Badge variant={getRiskBadgeColor(tx.analysis?.risk_score || 0)}>
                        {(tx.analysis?.risk_score || 0) * 100}%
                      </Badge>
                      {Array.isArray(tx.analysis?.dex_swaps) && tx.analysis!.dex_swaps!.length > 0 && (
                        <Badge variant="secondary">DEX Swap</Badge>
                      )}
                    </div>
                    <span className="text-sm text-muted-foreground">
                      {formatTimestamp(tx.timestamp)}
                    </span>
                  </div>

                  <div className="grid gap-2 md:grid-cols-2">
                    <div>
                      <p className="text-sm font-medium">Von</p>
                      <p className="text-xs font-mono text-muted-foreground">
                        {tx.from}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm font-medium">An</p>
                      <p className="text-xs font-mono text-muted-foreground">
                        {tx.to}
                      </p>
                    </div>
                  </div>

                  <div className="flex justify-between items-center mt-3">
                    <div>
                      <p className="text-sm font-medium">Wert</p>
                      <p className="text-lg font-bold">{tx.value} ETH</p>
                    </div>
                    <div className="flex items-center gap-1">
                      {tx.analysis?.money_flow === 'inflow' && <ArrowDownLeft className="h-4 w-4 text-green-500" />}
                      {tx.analysis?.money_flow === 'outflow' && <ArrowUpRight className="h-4 w-4 text-red-500" />}
                      {tx.analysis?.money_flow === 'internal' && <Activity className="h-4 w-4 text-primary-500" />}
                    </div>
                  </div>

                  {tx.analysis && tx.analysis.risk_factors.length > 0 && (
                    <div className="mt-3">
                      <p className="text-sm font-medium mb-1">Risikofaktoren:</p>
                      <div className="flex flex-wrap gap-1">
                        {tx.analysis.risk_factors.map((factor, index) => (
                          <Badge key={index} variant="outline" className="text-xs">
                            {factor}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}

                  {tx.analysis && Array.isArray(tx.analysis.dex_swaps) && tx.analysis.dex_swaps.length > 0 && (
                    <div className="mt-3">
                      <p className="text-sm font-medium mb-1">DEX Swap Details{tx.analysis.dex_router ? ` (Router: ${tx.analysis.dex_router})` : ''}:</p>
                      <div className="space-y-2">
                        {tx.analysis.dex_swaps.map((s, idx) => (
                          <div key={idx} className="text-xs grid md:grid-cols-3 gap-2 p-2 rounded border">
                            <div>
                              <span className="font-medium">Pool</span>: {s.pair_or_pool}
                            </div>
                            <div>
                              <span className="font-medium">In</span>: {s.amount0_in ?? '-'} / {s.amount1_in ?? '-'}
                            </div>
                            <div>
                              <span className="font-medium">Out</span>: {s.amount0_out ?? '-'} / {s.amount1_out ?? '-'}
                            </div>
                            {(s.token0 || s.token1) && (
                              <div className="md:col-span-3 text-muted-foreground">
                                Tokens: {s.token0 ?? '-'} / {s.token1 ?? '-'}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {tx.analysis && tx.analysis.flagged_addresses?.length > 0 && (
                    <div className="mt-3">
                      <p className="text-sm font-medium mb-1 text-red-600">Geflaggte Adressen:</p>
                      <div className="flex flex-wrap gap-1">
                        {tx.analysis.flagged_addresses.map((addr, index) => (
                          <Badge key={index} variant="destructive" className="text-xs">
                            {addr.slice(0, 10)}...
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

export { AdvancedTransactionHistory }

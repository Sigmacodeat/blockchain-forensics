/*
 * Erweitertes Wallet-Dashboard mit Charts und Metriken
 */

import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  TrendingUp,
  TrendingDown,
  Activity,
  DollarSign,
  AlertTriangle,
  Shield,
  BarChart3,
  PieChart,
  Calendar,
  RefreshCw
} from 'lucide-react'
import { useWallet } from '@/contexts/WalletContext'

interface WalletMetrics {
  totalBalance: string
  totalValue: string
  totalTransactions: number
  avgDailyVolume: string
  riskDistribution: {
    low: number
    medium: number
    high: number
  }
  performanceMetrics: {
    daily_change: number
    weekly_change: number
    monthly_change: number
  }
  topAssets: Array<{
    symbol: string
    balance: string
    value: string
    change_24h: number
  }>
}

const WalletDashboard: React.FC = () => {
  const { state } = useWallet()
  const [selectedWallet, setSelectedWallet] = useState<string | null>(null)
  const [timeRange, setTimeRange] = useState('7d')
  const [isLoading, setIsLoading] = useState(false)
  const [metrics, setMetrics] = useState<WalletMetrics | null>(null)

  // Simulierte Metriken für Demo
  useEffect(() => {
    const demoMetrics: WalletMetrics = {
      totalBalance: '15.67 ETH',
      totalValue: '$28,450.32',
      totalTransactions: 156,
      avgDailyVolume: '$1,234.56',
      riskDistribution: {
        low: 120,
        medium: 28,
        high: 8
      },
      performanceMetrics: {
        daily_change: 2.34,
        weekly_change: -1.23,
        monthly_change: 8.76
      },
      topAssets: [
        { symbol: 'ETH', balance: '15.67', value: '$28,450.32', change_24h: 2.34 },
        { symbol: 'USDC', balance: '1,250.00', value: '$1,250.00', change_24h: 0.01 },
        { symbol: 'UNI', balance: '45.23', value: '$892.15', change_24h: -3.45 }
      ]
    }

    setTimeout(() => {
      setMetrics(demoMetrics)
    }, 1000)
  }, [selectedWallet, timeRange])

  const selectedWalletData = selectedWallet
    ? state.wallets.find(w => w.id === selectedWallet)
    : state.wallets[0]

  const getPerformanceColor = (change: number) => {
    if (change > 0) return 'text-green-600'
    if (change < 0) return 'text-red-600'
    return 'text-gray-600'
  }

  const getPerformanceIcon = (change: number) => {
    if (change > 0) return <TrendingUp className="h-4 w-4" />
    if (change < 0) return <TrendingDown className="h-4 w-4" />
    return <Activity className="h-4 w-4" />
  }

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header Controls */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold">Wallet Analytics Dashboard</h2>
          <p className="text-muted-foreground">
            Umfassende Übersicht über Wallet-Performance und Risiken
          </p>
        </div>
        <div className="flex gap-2">
          <Select value={selectedWallet || ''} onValueChange={setSelectedWallet}>
            <SelectTrigger className="w-[200px]">
              <SelectValue placeholder="Wallet auswählen" />
            </SelectTrigger>
            <SelectContent>
              {state.wallets.map(wallet => (
                <SelectItem key={wallet.id} value={wallet.id}>
                  {wallet.chain} - {wallet.address.slice(0, 10)}...
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select value={timeRange} onValueChange={setTimeRange}>
            <SelectTrigger className="w-[120px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="24h">24h</SelectItem>
              <SelectItem value="7d">7 Tage</SelectItem>
              <SelectItem value="30d">30 Tage</SelectItem>
              <SelectItem value="90d">90 Tage</SelectItem>
            </SelectContent>
          </Select>
          <Button variant="outline" size="sm">
            <RefreshCw className="h-4 w-4 mr-2" />
            Aktualisieren
          </Button>
        </div>
      </div>

      {/* Overview Cards */}
      {metrics && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Gesamtbalance</CardTitle>
              <DollarSign className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{metrics.totalBalance}</div>
              <p className="text-xs text-muted-foreground">
                ≈ {metrics.totalValue} USD
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Transaktionen</CardTitle>
              <Activity className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{metrics.totalTransactions}</div>
              <p className="text-xs text-muted-foreground">
                Ø {metrics.avgDailyVolume} pro Tag
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Performance</CardTitle>
              {getPerformanceIcon(metrics.performanceMetrics.daily_change)}
            </CardHeader>
            <CardContent>
              <div className={`text-2xl font-bold ${getPerformanceColor(metrics.performanceMetrics.daily_change)}`}>
                {metrics.performanceMetrics.daily_change > 0 ? '+' : ''}{metrics.performanceMetrics.daily_change}%
              </div>
              <p className="text-xs text-muted-foreground">
                Veränderung (24h)
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Risikobewertung</CardTitle>
              <Shield className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {metrics.riskDistribution.high > 0 ? 'Erhöht' : 'Normal'}
              </div>
              <p className="text-xs text-muted-foreground">
                {metrics.riskDistribution.high} hohe Risiken
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Main Analytics */}
      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Übersicht</TabsTrigger>
          <TabsTrigger value="assets">Assets</TabsTrigger>
          <TabsTrigger value="performance">Performance</TabsTrigger>
          <TabsTrigger value="risk">Risikoanalyse</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Risikoverteilung</CardTitle>
                <CardDescription>
                  Verteilung der Transaktionen nach Risikostufen
                </CardDescription>
              </CardHeader>
              <CardContent>
                {metrics && (
                  <div className="space-y-3">
                    <div className="flex justify-between items-center">
                      <span className="text-sm">Niedriges Risiko</span>
                      <div className="flex items-center gap-2">
                        <div className="w-16 bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-green-500 h-2 rounded-full"
                            style={{ width: `${(metrics.riskDistribution.low / metrics.totalTransactions) * 100}%` }}
                          ></div>
                        </div>
                        <span className="text-sm font-medium">{metrics.riskDistribution.low}</span>
                      </div>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm">Mittleres Risiko</span>
                      <div className="flex items-center gap-2">
                        <div className="w-16 bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-yellow-500 h-2 rounded-full"
                            style={{ width: `${(metrics.riskDistribution.medium / metrics.totalTransactions) * 100}%` }}
                          ></div>
                        </div>
                        <span className="text-sm font-medium">{metrics.riskDistribution.medium}</span>
                      </div>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm">Hohes Risiko</span>
                      <div className="flex items-center gap-2">
                        <div className="w-16 bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-red-500 h-2 rounded-full"
                            style={{ width: `${(metrics.riskDistribution.high / metrics.totalTransactions) * 100}%` }}
                          ></div>
                        </div>
                        <span className="text-sm font-medium">{metrics.riskDistribution.high}</span>
                      </div>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Performance-Trend</CardTitle>
                <CardDescription>
                  Wertentwicklung über verschiedene Zeiträume
                </CardDescription>
              </CardHeader>
              <CardContent>
                {metrics && (
                  <div className="space-y-3">
                    <div className="flex justify-between items-center">
                      <span className="text-sm">Täglich</span>
                      <div className={`flex items-center gap-1 ${getPerformanceColor(metrics.performanceMetrics.daily_change)}`}>
                        {getPerformanceIcon(metrics.performanceMetrics.daily_change)}
                        <span className="font-medium">
                          {metrics.performanceMetrics.daily_change > 0 ? '+' : ''}{metrics.performanceMetrics.daily_change}%
                        </span>
                      </div>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm">Wöchentlich</span>
                      <div className={`flex items-center gap-1 ${getPerformanceColor(metrics.performanceMetrics.weekly_change)}`}>
                        {getPerformanceIcon(metrics.performanceMetrics.weekly_change)}
                        <span className="font-medium">
                          {metrics.performanceMetrics.weekly_change > 0 ? '+' : ''}{metrics.performanceMetrics.weekly_change}%
                        </span>
                      </div>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm">Monatlich</span>
                      <div className={`flex items-center gap-1 ${getPerformanceColor(metrics.performanceMetrics.monthly_change)}`}>
                        {getPerformanceIcon(metrics.performanceMetrics.monthly_change)}
                        <span className="font-medium">
                          {metrics.performanceMetrics.monthly_change > 0 ? '+' : ''}{metrics.performanceMetrics.monthly_change}%
                        </span>
                      </div>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="assets" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Top Assets</CardTitle>
              <CardDescription>
                Die wichtigsten Assets in dieser Wallet
              </CardDescription>
            </CardHeader>
            <CardContent>
              {metrics && (
                <div className="space-y-4">
                  {metrics.topAssets.map((asset, index) => (
                    <div key={index} className="flex items-center justify-between p-3 border rounded">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center">
                          <span className="text-sm font-bold text-primary-600">{asset.symbol.slice(0, 2)}</span>
                        </div>
                        <div>
                          <p className="font-medium">{asset.symbol}</p>
                          <p className="text-sm text-muted-foreground">{asset.balance} Tokens</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="font-bold">{asset.value}</p>
                        <p className={`text-sm ${getPerformanceColor(asset.change_24h)}`}>
                          {asset.change_24h > 0 ? '+' : ''}{asset.change_24h}% (24h)
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="performance" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Performance-Analyse</CardTitle>
              <CardDescription>
                Detaillierte Performance-Metriken über den Zeitraum
              </CardDescription>
            </CardHeader>
            <CardContent>
              {metrics && (
                <div className="space-y-6">
                  {/* Performance Chart Placeholder */}
                  <div className="h-64 bg-gray-50 rounded-lg flex items-center justify-center">
                    <div className="text-center">
                      <BarChart3 className="h-12 w-12 text-gray-400 mx-auto mb-2" />
                      <p className="text-gray-500">Performance-Chart</p>
                      <p className="text-sm text-gray-400">(würde echte Chart-Daten zeigen)</p>
                    </div>
                  </div>

                  {/* Performance Metrics */}
                  <div className="grid gap-4 md:grid-cols-3">
                    <div className="text-center p-4 border rounded">
                      <p className="text-sm text-muted-foreground">Höchstwert</p>
                      <p className="text-lg font-bold">$32,450.12</p>
                      <p className="text-xs text-green-600">+12.3% vom Tiefpunkt</p>
                    </div>
                    <div className="text-center p-4 border rounded">
                      <p className="text-sm text-muted-foreground">Tiefstwert</p>
                      <p className="text-lg font-bold">$24,120.87</p>
                      <p className="text-xs text-red-600">-8.7% vom Höchstwert</p>
                    </div>
                    <div className="text-center p-4 border rounded">
                      <p className="text-sm text-muted-foreground">Volatilität</p>
                      <p className="text-lg font-bold">23.4%</p>
                      <p className="text-xs text-muted-foreground">Standardabweichung</p>
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="risk" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Risiko-Analyse</CardTitle>
              <CardDescription>
                KI-gestützte Bewertung von Risikofaktoren und Mustern
              </CardDescription>
            </CardHeader>
            <CardContent>
              {metrics && (
                <div className="space-y-6">
                  {/* Risk Factors */}
                  <div>
                    <h4 className="font-semibold mb-3">Identifizierte Risikofaktoren</h4>
                    <div className="space-y-2">
                      <div className="flex justify-between items-center p-3 bg-red-50 border border-red-200 rounded">
                        <span className="font-medium">Hohe Transaktionsvolumina</span>
                        <Badge variant="destructive">8 Transaktionen</Badge>
                      </div>
                      <div className="flex justify-between items-center p-3 bg-yellow-50 border border-yellow-200 rounded">
                        <span className="font-medium">Ungewöhnliche Zeitmuster</span>
                        <Badge variant="warning">12 Fälle</Badge>
                      </div>
                      <div className="flex justify-between items-center p-3 bg-green-50 border border-green-200 rounded">
                        <span className="font-medium">Bekannte Exchange-Adressen</span>
                        <Badge variant="success">45 Interaktionen</Badge>
                      </div>
                    </div>
                  </div>

                  {/* Risk Score Timeline */}
                  <div>
                    <h4 className="font-semibold mb-3">Risikoscore-Verlauf</h4>
                    <div className="h-32 bg-gray-50 rounded-lg flex items-end justify-center">
                      <div className="text-center text-gray-500">
                        <PieChart className="h-8 w-8 mx-auto mb-1" />
                        <p className="text-sm">Risikoscore-Chart</p>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

export { WalletDashboard }

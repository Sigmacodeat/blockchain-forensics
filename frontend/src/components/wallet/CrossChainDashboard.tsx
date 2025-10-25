/*
 * Cross-Chain-Swap-Dashboard für Multi-Chain-Wallets
 */

import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  ArrowRightLeft,
  TrendingUp,
  TrendingDown,
  Clock,
  Zap,
  AlertTriangle,
  CheckCircle,
  BarChart3,
  Coins,
  RefreshCw,
  ExternalLink,
  DollarSign,
  Percent
} from 'lucide-react'
import { useWallet } from '@/contexts/WalletContext'
import LoadingSpinner from '@/components/ui/LoadingSpinner'

interface SwapQuote {
  from_token: string
  to_token: string
  from_chain: string
  to_chain: string
  from_amount: string
  to_amount: string
  exchange_rate: number
  fee: number
  slippage: number
  estimated_gas: string
  provider: string
}

interface Bridge {
  bridge_id: string
  from_chain: string
  to_chain: string
  protocol: string
  fee: number
  min_amount: number
  max_amount: number
  estimated_time: number
  supported_tokens: string[]
  is_active: boolean
}

interface ArbitrageOpportunity {
  from_chain: string
  to_chain: string
  token: string
  price_from: number
  price_to: number
  difference_percent: number
  potential_profit: number
  recommended_bridge: string
}

const CrossChainDashboard: React.FC = () => {
  const { state } = useWallet()
  const [selectedWallet, setSelectedWallet] = useState<string | null>(null)
  const [swapQuote, setSwapQuote] = useState<SwapQuote | null>(null)
  const [bridges, setBridges] = useState<Bridge[]>([])
  const [arbitrageOpportunities, setArbitrageOpportunities] = useState<ArbitrageOpportunity[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [fromToken, setFromToken] = useState('ETH')
  const [toToken, setToToken] = useState('USDC')
  const [fromChain, setFromChain] = useState('ethereum')
  const [toChain, setToChain] = useState('polygon')
  const [amount, setAmount] = useState('1.0')

  const selectedWalletData = selectedWallet
    ? state.wallets.find(w => w.id === selectedWallet)
    : state.wallets[0]

  // Demo-Daten laden
  useEffect(() => {
    if (selectedWalletData) {
      const demoBridges: Bridge[] = [
        {
          bridge_id: 'polygon_bridge_1',
          from_chain: 'ethereum',
          to_chain: 'polygon',
          protocol: 'polygon_bridge',
          fee: 0.1,
          min_amount: 10,
          max_amount: 10000,
          estimated_time: 15,
          supported_tokens: ['USDC', 'USDT', 'DAI', 'WETH'],
          is_active: true
        },
        {
          bridge_id: 'hop_bridge_1',
          from_chain: 'ethereum',
          to_chain: 'polygon',
          protocol: 'hop',
          fee: 0.05,
          min_amount: 1,
          max_amount: 50000,
          estimated_time: 10,
          supported_tokens: ['USDC', 'USDT', 'DAI'],
          is_active: true
        }
      ]

      const demoArbitrage: ArbitrageOpportunity[] = [
        {
          from_chain: 'ethereum',
          to_chain: 'polygon',
          token: 'ETH',
          price_from: 2500,
          price_to: 2495,
          difference_percent: -0.2,
          potential_profit: 4.5,
          recommended_bridge: 'hop_bridge_1'
        },
        {
          from_chain: 'polygon',
          to_chain: 'ethereum',
          token: 'ETH',
          price_from: 2495,
          price_to: 2500,
          difference_percent: 0.2,
          potential_profit: 4.5,
          recommended_bridge: 'polygon_bridge_1'
        }
      ]

      setTimeout(() => {
        setBridges(demoBridges)
        setArbitrageOpportunities(demoArbitrage)
      }, 1000)
    }
  }, [selectedWalletData])

  // Swap-Quote aktualisieren
  useEffect(() => {
    const fetchQuote = async () => {
      if (amount && parseFloat(amount) > 0) {
        setIsLoading(true)
        try {
          // Simuliertes Quote
          const demoQuote: SwapQuote = {
            from_token: fromToken,
            to_token: toToken,
            from_chain: fromChain,
            to_chain: toChain,
            from_amount: amount,
            to_amount: (parseFloat(amount) * (fromChain === 'ethereum' && toChain === 'polygon' ? 0.995 : 1)).toString(),
            exchange_rate: fromChain === 'ethereum' && toChain === 'polygon' ? 0.995 : 1,
            fee: 0.1,
            slippage: 0.5,
            estimated_gas: '0.01',
            provider: '1inch'
          }

          setTimeout(() => {
            setSwapQuote(demoQuote)
            setIsLoading(false)
          }, 1000)
        } catch (error) {
          console.error('Fehler beim Laden des Quotes:', error)
          setIsLoading(false)
        }
      }
    }

    fetchQuote()
  }, [fromToken, toToken, fromChain, toChain, amount])

  const formatCurrency = (value: string | number) => {
    const num = typeof value === 'string' ? parseFloat(value) : value
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(num)
  }

  const formatPercent = (value: number) => {
    return `${value > 0 ? '+' : ''}${value.toFixed(2)}%`
  }

  const getChainIcon = (chain: string) => {
    const icons: { [key: string]: string } = {
      ethereum: '⟠',
      polygon: '⬡',
      bsc: '⬟',
      avalanche: '🏔️'
    }
    return icons[chain.toLowerCase()] || '⛓️'
  }

  if (!selectedWalletData) {
    return (
      <div className="text-center py-8">
        <p className="text-muted-foreground">Wählen Sie eine Wallet aus, um Cross-Chain-Daten anzuzeigen</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold">Cross-Chain Swaps</h2>
          <p className="text-muted-foreground">
            Swappen Sie Assets zwischen verschiedenen Blockchains
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
        </div>
      </div>

      {/* Overview Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Verfügbare Bridges</CardTitle>
            <ArrowRightLeft className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{bridges.length}</div>
            <p className="text-xs text-muted-foreground">
              {bridges.filter(b => b.is_active).length} aktiv
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Arbitrage Opportunities</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{arbitrageOpportunities.length}</div>
            <p className="text-xs text-muted-foreground">
              Preis-Differenzen gefunden
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Durchschnittliche Bridge-Zeit</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">15min</div>
            <p className="text-xs text-muted-foreground">
              Von Ethereum zu Polygon
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Gesamtvolumen 24h</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">$1.25M</div>
            <p className="text-xs text-muted-foreground">
              Cross-Chain-Transfers
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Main Content */}
      <Tabs defaultValue="swap" className="space-y-4">
        <TabsList>
          <TabsTrigger value="swap">Swap</TabsTrigger>
          <TabsTrigger value="bridges">Bridges</TabsTrigger>
          <TabsTrigger value="arbitrage">Arbitrage</TabsTrigger>
        </TabsList>

        <TabsContent value="swap" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Cross-Chain Swap</CardTitle>
              <CardDescription>
                Swappen Sie Assets zwischen verschiedenen Blockchains
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                {/* Swap Form */}
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Von</label>
                    <div className="flex gap-2">
                      <Select value={fromToken} onValueChange={setFromToken}>
                        <SelectTrigger className="flex-1">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="ETH">ETH</SelectItem>
                          <SelectItem value="USDC">USDC</SelectItem>
                          <SelectItem value="USDT">USDT</SelectItem>
                          <SelectItem value="DAI">DAI</SelectItem>
                        </SelectContent>
                      </Select>
                      <Select value={fromChain} onValueChange={setFromChain}>
                        <SelectTrigger className="w-[120px]">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="ethereum">Ethereum {getChainIcon('ethereum')}</SelectItem>
                          <SelectItem value="polygon">Polygon {getChainIcon('polygon')}</SelectItem>
                          <SelectItem value="bsc">BSC {getChainIcon('bsc')}</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium">Nach</label>
                    <div className="flex gap-2">
                      <Select value={toToken} onValueChange={setToToken}>
                        <SelectTrigger className="flex-1">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="USDC">USDC</SelectItem>
                          <SelectItem value="USDT">USDT</SelectItem>
                          <SelectItem value="DAI">DAI</SelectItem>
                          <SelectItem value="ETH">ETH</SelectItem>
                        </SelectContent>
                      </Select>
                      <Select value={toChain} onValueChange={setToChain}>
                        <SelectTrigger className="w-[120px]">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="polygon">Polygon {getChainIcon('polygon')}</SelectItem>
                          <SelectItem value="ethereum">Ethereum {getChainIcon('ethereum')}</SelectItem>
                          <SelectItem value="bsc">BSC {getChainIcon('bsc')}</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">Betrag</label>
                  <Input
                    type="number"
                    value={amount}
                    onChange={(e) => setAmount(e.target.value)}
                    placeholder="0.0"
                  />
                </div>

                {/* Swap Quote */}
                {isLoading && (
                  <div className="flex items-center justify-center py-8">
                    <LoadingSpinner />
                    <span className="ml-2">Quote wird geladen...</span>
                  </div>
                )}

                {swapQuote && !isLoading && (
                  <Card className="border-primary/20 bg-primary/5">
                    <CardHeader>
                      <CardTitle className="text-lg flex items-center gap-2">
                        <CheckCircle className="h-5 w-5 text-green-500" />
                        Swap-Quote verfügbar
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="grid gap-4 md:grid-cols-2">
                        <div className="space-y-2">
                          <div className="flex justify-between">
                            <span className="text-sm text-muted-foreground">Sie erhalten</span>
                            <span className="font-semibold">
                              {parseFloat(swapQuote.to_amount).toFixed(6)} {swapQuote.to_token}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-sm text-muted-foreground">Wechselkurs</span>
                            <span className="font-semibold">
                              1 {swapQuote.from_token} = {swapQuote.exchange_rate.toFixed(6)} {swapQuote.to_token}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-sm text-muted-foreground">Bridge-Provider</span>
                            <Badge variant="outline">{swapQuote.provider}</Badge>
                          </div>
                        </div>

                        <div className="space-y-2">
                          <div className="flex justify-between">
                            <span className="text-sm text-muted-foreground">Bridge-Fee</span>
                            <span className="font-semibold">{swapQuote.fee}%</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-sm text-muted-foreground">Slippage</span>
                            <span className="font-semibold">{swapQuote.slippage}%</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-sm text-muted-foreground">Geschätzte Zeit</span>
                            <span className="font-semibold">
                              {fromChain !== toChain ? '15 Minuten' : '< 1 Minute'}
                            </span>
                          </div>
                        </div>
                      </div>

                      <div className="mt-4 pt-4 border-t">
                        <Button className="w-full">
                          <ArrowRightLeft className="h-4 w-4 mr-2" />
                          Swap bestätigen
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="bridges" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Verfügbare Bridges</CardTitle>
              <CardDescription>
                Übersicht aller verfügbaren Cross-Chain-Bridges
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {bridges.map(bridge => (
                  <div key={bridge.bridge_id} className="border rounded-lg p-4">
                    <div className="flex justify-between items-center mb-3">
                      <div className="flex items-center gap-2">
                        <Badge variant="outline">{bridge.protocol}</Badge>
                        <span className="font-medium">
                          {getChainIcon(bridge.from_chain)} {bridge.from_chain} → {getChainIcon(bridge.to_chain)} {bridge.to_chain}
                        </span>
                      </div>
                      <Badge variant={bridge.is_active ? "success" : "secondary"}>
                        {bridge.is_active ? "Aktiv" : "Inaktiv"}
                      </Badge>
                    </div>

                    <div className="grid gap-2 md:grid-cols-4">
                      <div>
                        <p className="text-sm text-muted-foreground">Fee</p>
                        <p className="font-medium">{bridge.fee}%</p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">Min Betrag</p>
                        <p className="font-medium">${bridge.min_amount}</p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">Max Betrag</p>
                        <p className="font-medium">${bridge.max_amount}</p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">Geschätzte Zeit</p>
                        <p className="font-medium">{bridge.estimated_time}min</p>
                      </div>
                    </div>

                    <div className="mt-3">
                      <p className="text-sm text-muted-foreground mb-1">Unterstützte Token</p>
                      <div className="flex flex-wrap gap-1">
                        {bridge.supported_tokens.slice(0, 4).map(token => (
                          <Badge key={token} variant="outline" className="text-xs">
                            {token}
                          </Badge>
                        ))}
                        {bridge.supported_tokens.length > 4 && (
                          <Badge variant="outline" className="text-xs">
                            +{bridge.supported_tokens.length - 4} mehr
                          </Badge>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="arbitrage" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Arbitrage Opportunities</CardTitle>
              <CardDescription>
                Preis-Differenzen zwischen Chains für profitable Trades
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {arbitrageOpportunities.map((opportunity, index) => (
                  <div key={index} className="border rounded-lg p-4">
                    <div className="flex justify-between items-center mb-3">
                      <div className="flex items-center gap-2">
                        <span className="font-medium">
                          {opportunity.token}: {getChainIcon(opportunity.from_chain)} {opportunity.from_chain}
                        </span>
                        <ArrowRightLeft className="h-4 w-4" />
                        <span className="font-medium">
                          {getChainIcon(opportunity.to_chain)} {opportunity.to_chain}
                        </span>
                      </div>
                      <div className="text-right">
                        <Badge variant={opportunity.difference_percent > 0 ? "success" : "destructive"}>
                          {formatPercent(opportunity.difference_percent)}
                        </Badge>
                      </div>
                    </div>

                    <div className="grid gap-2 md:grid-cols-3">
                      <div>
                        <p className="text-sm text-muted-foreground">Preis {opportunity.from_chain}</p>
                        <p className="font-medium">${opportunity.price_from}</p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">Preis {opportunity.to_chain}</p>
                        <p className="font-medium">${opportunity.price_to}</p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">Potenzieller Gewinn</p>
                        <p className="font-medium text-green-600">${opportunity.potential_profit}</p>
                      </div>
                    </div>

                    <div className="mt-3 pt-3 border-t">
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-muted-foreground">
                          Empfohlene Bridge: {opportunity.recommended_bridge}
                        </span>
                        <Button size="sm">
                          <Zap className="h-4 w-4 mr-2" />
                          Arbitrage ausführen
                        </Button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

export { CrossChainDashboard }

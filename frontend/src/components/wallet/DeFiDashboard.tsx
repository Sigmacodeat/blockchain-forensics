/*
 * DeFi-Dashboard für Liquidity Pools und Staking
 */

import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  TrendingUp,
  TrendingDown,
  DollarSign,
  Coins,
  Lock,
  Zap,
  AlertTriangle,
  CheckCircle,
  BarChart3,
  PieChart,
  Plus,
  ArrowUpRight,
  ArrowDownLeft
} from 'lucide-react'
import { useWallet } from '@/contexts/WalletContext'
import LoadingSpinner from '@/components/ui/LoadingSpinner'

interface LiquidityPool {
  address: string
  protocol: string
  token0?: { symbol: string; address: string }
  token1?: { symbol: string; address: string }
  tvl: number
  volume_24h: number
  apy: number
  fee: number
}

interface StakingPosition {
  pool_address: string
  protocol: string
  staked_amount: string
  rewards_earned: string
  apy: number
  lock_period: number
}

interface YieldOpportunity {
  pool_address: string
  protocol: string
  token0?: { symbol: string }
  token1?: { symbol: string }
  tvl: number
  apy: number
  estimated_earnings: number
  risk_level: string
  recommendation: string
}

const DeFiDashboard: React.FC = () => {
  const { state } = useWallet()
  const [selectedWallet, setSelectedWallet] = useState<string | null>(null)
  const [pools, setPools] = useState<LiquidityPool[]>([])
  const [stakingPositions, setStakingPositions] = useState<StakingPosition[]>([])
  const [yieldOpportunities, setYieldOpportunities] = useState<YieldOpportunity[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [selectedProtocol, setSelectedProtocol] = useState('uniswap')

  const selectedWalletData = selectedWallet
    ? state.wallets.find(w => w.id === selectedWallet)
    : state.wallets[0]

  // Simulierte DeFi-Daten für Demo
  useEffect(() => {
    if (selectedWalletData) {
      const demoPools: LiquidityPool[] = [
        {
          address: '0x88e6A0c2dDD26FEEb64F039a2c41296FcB3f5640',
          protocol: 'uniswap',
          token0: { symbol: 'USDC', address: '0xA0b86a33E6444c2a6a6dB3b3b4b0f5c4a5' },
          token1: { symbol: 'WETH', address: '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2' },
          tvl: 1500000,
          volume_24h: 250000,
          apy: 15.5,
          fee: 0.3
        },
        {
          address: '0x8ad599c3A0ff1De082011EFDDc58f1908eb6e6D8',
          protocol: 'uniswap',
          token0: { symbol: 'USDT', address: '0xdAC17F958D2ee523a2206206994597C13D831ec7' },
          token1: { symbol: 'WETH', address: '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2' },
          tvl: 800000,
          volume_24h: 180000,
          apy: 12.3,
          fee: 0.3
        }
      ]

      const demoStaking: StakingPosition[] = [
        {
          pool_address: '0xae7ab96520DE3A18E5e111B5EaAb095312D7fE84',
          protocol: 'lido',
          staked_amount: '32',
          rewards_earned: '1.2',
          apy: 4.5,
          lock_period: 0
        }
      ]

      const demoYield: YieldOpportunity[] = [
        {
          pool_address: '0x88e6A0c2dDD26FEEb64F039a2c41296FcB3f5640',
          protocol: 'uniswap',
          token0: { symbol: 'USDC' },
          token1: { symbol: 'WETH' },
          tvl: 1500000,
          apy: 15.5,
          estimated_earnings: 23.45,
          risk_level: 'medium',
          recommendation: 'Empfohlen: Hohe Rendite bei geringem Risiko'
        }
      ]

      setTimeout(() => {
        setPools(demoPools)
        setStakingPositions(demoStaking)
        setYieldOpportunities(demoYield)
      }, 1000)
    }
  }, [selectedWalletData])

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value)
  }

  const formatAPY = (apy: number) => {
    return `${apy.toFixed(1)}%`
  }

  const getRiskBadge = (riskLevel: string) => {
    switch (riskLevel) {
      case 'low': return <Badge variant="success">Niedriges Risiko</Badge>
      case 'medium': return <Badge variant="warning">Mittleres Risiko</Badge>
      case 'high': return <Badge variant="destructive">Hohes Risiko</Badge>
      default: return <Badge variant="secondary">Unbekannt</Badge>
    }
  }

  if (!selectedWalletData) {
    return (
      <div className="text-center py-8">
        <p className="text-muted-foreground">Wählen Sie eine Wallet aus, um DeFi-Daten anzuzeigen</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold">DeFi Dashboard</h2>
          <p className="text-muted-foreground">
            Liquidity Pools und Staking für {selectedWalletData.address.slice(0, 10)}...
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
          <Select value={selectedProtocol} onValueChange={setSelectedProtocol}>
            <SelectTrigger className="w-[150px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="uniswap">Uniswap</SelectItem>
              <SelectItem value="sushiswap">SushiSwap</SelectItem>
              <SelectItem value="pancakeswap">PancakeSwap</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Overview Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Liquidity Pools</CardTitle>
            <Coins className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{pools.length}</div>
            <p className="text-xs text-muted-foreground">
              {formatCurrency(pools.reduce((sum, pool) => sum + pool.tvl, 0))} TVL
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Staking Positionen</CardTitle>
            <Lock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stakingPositions.length}</div>
            <p className="text-xs text-muted-foreground">
              {stakingPositions.reduce((sum, pos) => sum + parseFloat(pos.staked_amount || '0'), 0).toFixed(2)} ETH gestaked
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Yield Farming</CardTitle>
            <Zap className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{yieldOpportunities.length}</div>
            <p className="text-xs text-muted-foreground">
              Aktive Opportunities
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Gesamt APY</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {formatAPY(
                pools.reduce((sum, pool) => sum + (pool.apy || 0), 0) / pools.length || 0
              )}
            </div>
            <p className="text-xs text-muted-foreground">
              Durchschnittliche Rendite
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Main Content */}
      <Tabs defaultValue="pools" className="space-y-4">
        <TabsList>
          <TabsTrigger value="pools">Liquidity Pools</TabsTrigger>
          <TabsTrigger value="staking">Staking</TabsTrigger>
          <TabsTrigger value="yield">Yield Farming</TabsTrigger>
        </TabsList>

        <TabsContent value="pools" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Aktive Liquidity Pools</CardTitle>
              <CardDescription>
                Ihre Liquidity Provider Positionen
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {pools.map(pool => (
                  <div key={pool.address} className="border rounded-lg p-4">
                    <div className="flex justify-between items-center mb-3">
                      <div className="flex items-center gap-2">
                        <Badge variant="outline">{pool.protocol}</Badge>
                        <span className="font-medium">
                          {pool.token0?.symbol}/{pool.token1?.symbol}
                        </span>
                      </div>
                      <div className="text-right">
                        <p className="font-semibold">{formatAPY(pool.apy)}</p>
                        <p className="text-sm text-muted-foreground">APY</p>
                      </div>
                    </div>

                    <div className="grid gap-2 md:grid-cols-3">
                      <div>
                        <p className="text-sm text-muted-foreground">TVL</p>
                        <p className="font-medium">{formatCurrency(pool.tvl)}</p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">24h Volume</p>
                        <p className="font-medium">{formatCurrency(pool.volume_24h)}</p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">Fee</p>
                        <p className="font-medium">{pool.fee}%</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="staking" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Staking Positionen</CardTitle>
              <CardDescription>
                Ihre gestakten Assets und verdiente Rewards
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {stakingPositions.map(position => (
                  <div key={position.pool_address} className="border rounded-lg p-4">
                    <div className="flex justify-between items-center mb-3">
                      <div className="flex items-center gap-2">
                        <Badge variant="outline">{position.protocol}</Badge>
                        <span className="font-medium">Staking Pool</span>
                      </div>
                      <div className="text-right">
                        <p className="font-semibold">{formatAPY(position.apy)}</p>
                        <p className="text-sm text-muted-foreground">APY</p>
                      </div>
                    </div>

                    <div className="grid gap-2 md:grid-cols-3">
                      <div>
                        <p className="text-sm text-muted-foreground">Gestaked</p>
                        <p className="font-medium">{position.staked_amount} ETH</p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">Rewards</p>
                        <p className="font-medium">{position.rewards_earned} ETH</p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">Lock Period</p>
                        <p className="font-medium">
                          {position.lock_period === 0 ? 'Kein Lock' : `${position.lock_period} Tage`}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="yield" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Yield Farming Opportunities</CardTitle>
              <CardDescription>
                Empfohlene Liquidity Mining Möglichkeiten
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {yieldOpportunities.map(opportunity => (
                  <div key={opportunity.pool_address} className="border rounded-lg p-4">
                    <div className="flex justify-between items-center mb-3">
                      <div className="flex items-center gap-2">
                        <Badge variant="outline">{opportunity.protocol}</Badge>
                        <span className="font-medium">
                          {opportunity.token0?.symbol}/{opportunity.token1?.symbol}
                        </span>
                        {getRiskBadge(opportunity.risk_level)}
                      </div>
                      <div className="text-right">
                        <p className="font-semibold">{formatAPY(opportunity.apy)}</p>
                        <p className="text-sm text-muted-foreground">APY</p>
                      </div>
                    </div>

                    <div className="grid gap-2 md:grid-cols-3 mb-3">
                      <div>
                        <p className="text-sm text-muted-foreground">TVL</p>
                        <p className="font-medium">{formatCurrency(opportunity.tvl)}</p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">Geschätzte Einnahmen</p>
                        <p className="font-medium">{formatCurrency(opportunity.estimated_earnings)}/Tag</p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">Risiko</p>
                        <p className="font-medium">{opportunity.risk_level}</p>
                      </div>
                    </div>

                    <div className="flex justify-between items-center">
                      <p className="text-sm text-muted-foreground">
                        {opportunity.recommendation}
                      </p>
                      <Button size="sm">
                        <Plus className="h-4 w-4 mr-2" />
                        Investieren
                      </Button>
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

export { DeFiDashboard }

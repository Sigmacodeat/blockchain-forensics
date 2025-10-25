import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { useToast } from '@/components/ui/toast'
import { Loader2, Wallet, TrendingUp, Users, DollarSign, RefreshCw, Copy, ExternalLink } from 'lucide-react'
import { api } from '@/lib/api'

interface WalletInfo {
  address: string
  balance: number
  created_at: string
}

interface DashboardOverview {
  total_revenue_usd: number
  active_subscriptions: number
  recent_payments_30d: number
  btc_wallet: WalletInfo | null
}

interface RevenueData {
  date: string
  revenue: number
}

interface SubscriptionBreakdown {
  plan: string
  count: number
  total_revenue: number
}

interface PaymentRecord {
  id: number
  user_id: number
  plan_name: string
  price_amount: number
  pay_currency: string
  payment_status: string
  created_at: string
  user_email?: string
}

const CryptoPaymentsDashboard: React.FC = () => {
  const [overview, setOverview] = useState<DashboardOverview | null>(null)
  const [revenueData, setRevenueData] = useState<RevenueData[]>([])
  const [subscriptionBreakdown, setSubscriptionBreakdown] = useState<SubscriptionBreakdown[]>([])
  const [recentPayments, setRecentPayments] = useState<PaymentRecord[]>([])
  const [btcTransactions, setBtcTransactions] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const { showToast } = useToast()

  useEffect(() => {
    loadDashboardData()
  }, [])

  const loadDashboardData = async () => {
    try {
      setLoading(true)

      // Load all dashboard data in parallel
      const [
        overviewRes,
        revenueRes,
        breakdownRes,
        paymentsRes,
        transactionsRes
      ] = await Promise.all([
        api.get('/admin/crypto-payments/dashboard/overview'),
        api.get('/admin/crypto-payments/dashboard/revenue-chart'),
        api.get('/admin/crypto-payments/dashboard/subscription-breakdown'),
        api.get('/admin/crypto-payments/list?limit=20'),
        api.get('/crypto-payments/admin/wallet/transactions')
      ])

      setOverview(overviewRes.data)
      setRevenueData(revenueRes.data.data || [])
      setSubscriptionBreakdown(breakdownRes.data.breakdown || [])
      setRecentPayments(paymentsRes.data.payments || [])
      setBtcTransactions(transactionsRes.data || [])

    } catch (error) {
      console.error('Failed to load dashboard data:', error)
      showToast({
        type: 'error',
        title: 'Error',
        message: 'Failed to load dashboard data'
      })
    } finally {
      setLoading(false)
    }
  }

  const handleRefresh = async () => {
    try {
      setRefreshing(true)
      await api.post('/crypto-payments/admin/wallet/refresh-balance')
      await loadDashboardData()
      showToast({
        type: 'success',
        title: 'Success',
        message: 'Wallet balance refreshed'
      })
    } catch (error) {
      showToast({
        type: 'error',
        title: 'Error',
        message: 'Failed to refresh balance'
      })
    } finally {
      setRefreshing(false)
    }
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
    showToast({
      type: 'success',
      title: 'Copied',
      message: 'Address copied to clipboard'
    })
  }

  const openBlockExplorer = (address: string) => {
    window.open(`https://blockchain.com/btc/address/${address}`, '_blank')
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Crypto Payments Dashboard</h1>
        <Button onClick={handleRefresh} disabled={refreshing}>
          <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Revenue</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">${overview?.total_revenue_usd.toFixed(2) || '0.00'}</div>
            <p className="text-xs text-muted-foreground">All time</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Subscriptions</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{overview?.active_subscriptions || 0}</div>
            <p className="text-xs text-muted-foreground">Currently active</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Recent Payments</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{overview?.recent_payments_30d || 0}</div>
            <p className="text-xs text-muted-foreground">Last 30 days</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">BTC Balance</CardTitle>
            <Wallet className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{overview?.btc_wallet?.balance.toFixed(8) || '0.00000000'}</div>
            <p className="text-xs text-muted-foreground">BTC</p>
          </CardContent>
        </Card>
      </div>

      {/* BTC Wallet Section */}
      {overview?.btc_wallet && (
        <Card>
          <CardHeader>
            <CardTitle>BTC Wallet</CardTitle>
            <CardDescription>Platform wallet for receiving payments</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center space-x-2">
              <code className="flex-1 p-2 bg-muted rounded text-sm">{overview.btc_wallet.address}</code>
              <Button variant="outline" size="sm" onClick={() => copyToClipboard(overview.btc_wallet!.address)}>
                <Copy className="h-4 w-4" />
              </Button>
              <Button variant="outline" size="sm" onClick={() => openBlockExplorer(overview.btc_wallet!.address)}>
                <ExternalLink className="h-4 w-4" />
              </Button>
            </div>
            <p className="text-sm text-muted-foreground">
              Created: {new Date(overview.btc_wallet.created_at).toLocaleDateString()}
            </p>

            {btcTransactions.length > 0 && (
              <div>
                <h4 className="text-sm font-medium mb-2">Recent Transactions</h4>
                <div className="space-y-2 max-h-40 overflow-y-auto">
                  {btcTransactions.slice(0, 5).map((tx, index) => (
                    <div key={index} className="flex justify-between items-center p-2 bg-muted rounded">
                      <div>
                        <p className="text-sm font-mono">{tx.hash.substring(0, 16)}...</p>
                        <p className="text-xs text-muted-foreground">
                          {new Date(tx.time * 1000).toLocaleString()}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className={`text-sm font-medium ${tx.value > 0 ? 'text-green-600' : 'text-red-600'}`}>
                          {tx.value > 0 ? '+' : ''}{tx.value.toFixed(8)} BTC
                        </p>
                        <p className="text-xs text-muted-foreground">{tx.confirmations} conf</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Revenue Chart Placeholder */}
      <Card>
        <CardHeader>
          <CardTitle>Revenue Trend (Last 30 Days)</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-64 flex items-center justify-center text-muted-foreground">
            Chart visualization would go here
            {/* TODO: Add Chart.js or Recharts for revenue visualization */}
          </div>
          <div className="mt-4 space-y-2">
            {revenueData.slice(-7).map((day) => (
              <div key={day.date} className="flex justify-between">
                <span>{new Date(day.date).toLocaleDateString()}</span>
                <span>${day.revenue.toFixed(2)}</span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Subscription Breakdown */}
      <Card>
        <CardHeader>
          <CardTitle>Active Subscriptions by Plan</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {subscriptionBreakdown.map((item) => (
              <div key={item.plan} className="flex justify-between items-center">
                <div>
                  <p className="font-medium capitalize">{item.plan}</p>
                  <p className="text-sm text-muted-foreground">{item.count} subscribers</p>
                </div>
                <div className="text-right">
                  <p className="font-medium">${item.total_revenue.toFixed(2)}/month</p>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Recent Payments */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Payments</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>User</TableHead>
                <TableHead>Plan</TableHead>
                <TableHead>Amount</TableHead>
                <TableHead>Currency</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Date</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {recentPayments.map((payment) => (
                <TableRow key={payment.id}>
                  <TableCell>{payment.user_email || `User ${payment.user_id}`}</TableCell>
                  <TableCell>
                    <Badge variant="outline" className="capitalize">{payment.plan_name}</Badge>
                  </TableCell>
                  <TableCell>${payment.price_amount}</TableCell>
                  <TableCell className="uppercase">{payment.pay_currency}</TableCell>
                  <TableCell>
                    <Badge
                      variant={payment.payment_status === 'finished' ? 'default' :
                              payment.payment_status === 'pending' ? 'secondary' : 'destructive'}
                    >
                      {payment.payment_status}
                    </Badge>
                  </TableCell>
                  <TableCell>{new Date(payment.created_at).toLocaleDateString()}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  )
}

export default CryptoPaymentsDashboard

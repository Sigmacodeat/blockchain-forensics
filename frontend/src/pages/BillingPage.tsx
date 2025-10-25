import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { CreditCard, Download, ExternalLink, CheckCircle, XCircle, Clock, AlertTriangle, Crown, TrendingUp, Bitcoin, Wallet, FileText, BarChart3, Zap, ArrowUpRight } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import { useLocalePath } from '@/hooks/useLocalePath';
import { format } from 'date-fns';
import CryptoPaymentModal from '@/components/CryptoPaymentModal';
import Web3PaymentButton from '@/components/chat/Web3PaymentButton';

// ============================================================================
// TypeScript Interfaces
// ============================================================================

interface UnifiedSubscription {
  id: string;
  plan: string;
  status: 'active' | 'canceled' | 'past_due' | 'trialing';
  payment_type: 'stripe' | 'crypto';
  current_period_start: string;
  current_period_end: string;
  cancel_at_period_end: boolean;
  amount: number;
  currency: string;
  interval: 'month' | 'year' | 'monthly' | 'yearly';
}

interface UnifiedPaymentMethod {
  id: string;
  type: 'card' | 'crypto';
  display_name: string;
  details: {
    brand?: string;
    last4?: string;
    exp_month?: number;
    exp_year?: number;
    currency?: string;
    last_used?: string;
  };
  is_default: boolean;
}

interface UnifiedInvoice {
  id: string;
  number: string;
  amount_paid: number;
  amount_due?: number;
  currency: string;
  status: 'paid' | 'open' | 'void' | 'uncollectible';
  payment_type: 'stripe' | 'crypto';
  created: string;
  pdf_url?: string;
  tx_hash?: string;
}

interface UsageStats {
  traces_used: number;
  traces_limit: number;
  cases_used: number;
  cases_limit: number;
  api_calls_used: number;
  api_calls_limit: number;
  period_start: string;
  period_end: string;
}

interface CryptoPayment {
  payment_id: number;
  order_id: string;
  plan_name: string;
  payment_status: string;
  pay_amount: number;
  pay_currency: string;
  pay_address: string;
  pay_in_hash?: string;
  created_at: string;
  invoice_url?: string;
}

export default function BillingPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const localePath = useLocalePath();
  const qc = useQueryClient();
  const [upgradePlan, setUpgradePlan] = useState<string | null>(null);

  // State
  const [cryptoModalOpen, setCryptoModalOpen] = useState(false);
  const [selectedPlan, setSelectedPlan] = useState<string | null>(null);
  const [web3Open, setWeb3Open] = useState(false);
  const [web3Currency, setWeb3Currency] = useState<'eth'|'bnb'|'matic'|'trx'>('matic');
  const [web3Loading, setWeb3Loading] = useState(false);
  const [web3Error, setWeb3Error] = useState<string | null>(null);
  const [web3Payment, setWeb3Payment] = useState<null | {
    payment_id: number;
    pay_amount: number;
    pay_currency: 'eth'|'bnb'|'matic'|'trx';
    pay_address: string;
    plan_name: string;
  }>(null);

  // Fetch subscription
  const { data: subscription, isLoading: subLoading } = useQuery<UnifiedSubscription | null>({
    queryKey: ['subscription'],
    queryFn: async () => {
      const res = await api.get('/api/v1/billing/subscription');
      return res.data;
    },
  });

  // Fetch payment methods
  const { data: paymentMethods, isLoading: pmLoading } = useQuery<UnifiedPaymentMethod[]>({
    queryKey: ['paymentMethods'],
    queryFn: async () => {
      const res = await api.get('/api/v1/billing/payment-methods');
      return res.data.data || [];
    },
  });

  // Fetch invoices
  const { data: invoices, isLoading: invLoading } = useQuery<UnifiedInvoice[]>({
    queryKey: ['invoices'],
    queryFn: async () => {
      const res = await api.get('/api/v1/billing/invoices');
      return res.data.data || [];
    },
  });

  // Fetch crypto payment history
  const { data: cryptoPayments } = useQuery<CryptoPayment[]>({
    queryKey: ['cryptoPayments'],
    queryFn: async () => {
      const res = await api.get('/api/v1/crypto-payments/history');
      return res.data.payments || [];
    },
  });

  // Fetch usage stats
  const { data: usage } = useQuery<UsageStats>({
    queryKey: ['usage'],
    queryFn: async () => {
      const res = await api.get('/api/v1/billing/usage');
      return res.data;
    },
  });

  // Create checkout session
  const checkoutMutation = useMutation({
    mutationFn: async (plan: string) => {
      const billingPath = localePath('/billing');
      const res = await api.post('/api/v1/billing/checkout-session', {
        plan,
        success_url: `${window.location.origin}${billingPath}?success=true`,
        cancel_url: `${window.location.origin}${billingPath}?canceled=true`,
      });
      return res.data;
    },
    onSuccess: (data) => {
      if (data.url) {
        window.location.href = data.url;
      }
    },
  });

  // Cancel subscription
  const cancelMutation = useMutation({
    mutationFn: async () => {
      const res = await api.post('/api/v1/billing/cancel');
      return res.data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['subscription'] });
    },
  });

  // Customer portal
  const portalMutation = useMutation({
    mutationFn: async () => {
      const res = await api.post('/api/v1/billing/portal-session');
      return res.data;
    },
    onSuccess: (data) => {
      if (data.url) {
        window.location.href = data.url;
      }
    },
  });

  const getStatusBadge = (status: string) => {
    const variants: Record<string, { variant: any; icon: any; label: string }> = {
      active: { variant: 'default', icon: CheckCircle, label: 'Aktiv' },
      trialing: { variant: 'secondary', icon: Clock, label: 'Testphase' },
      canceled: { variant: 'destructive', icon: XCircle, label: 'Gekündigt' },
      past_due: { variant: 'destructive', icon: AlertTriangle, label: 'Überfällig' },
    };
    const config = variants[status] || variants.active;
    const Icon = config.icon;
    return (
      <Badge variant={config.variant} className="flex items-center gap-1">
        <Icon className="w-3 h-3" />
        {config.label}
      </Badge>
    );
  };

  const getUsagePercentage = (used: number, limit: number) => {
    if (limit === -1) return 0; // Unlimited
    return Math.min(100, (used / limit) * 100);
  };

  const getUsageColor = (percentage: number) => {
    if (percentage >= 90) return 'text-red-600 bg-red-100';
    if (percentage >= 75) return 'text-amber-600 bg-amber-100';
    return 'text-green-600 bg-green-100';
  };

  const plans = [
    { id: 'community', name: 'Community', price: 0, features: ['Basic Tracing', 'Cases', '10 Traces/Monat'] },
    { id: 'starter', name: 'Starter', price: 49, features: ['Enhanced Tracing', '50 Traces/Monat', 'Webhooks'] },
    { id: 'pro', name: 'Pro', price: 199, features: ['Graph Explorer', 'Correlation', 'Unlimited Traces', 'API Access'] },
    { id: 'business', name: 'Business', price: 499, features: ['Automation', 'SSO', 'Policies', 'Priority Support'] },
    { id: 'plus', name: 'Plus', price: 999, features: ['AI Agent', 'Travel Rule', 'All Sanctions Lists', 'White Glove Support'] },
  ];

  if (subLoading || pmLoading || invLoading) {
    return (
      <div className="space-y-6">
        <h1 className="text-3xl font-bold">Billing & Subscription</h1>
        <div className="grid gap-6">
          {[1, 2, 3].map((i) => (
            <Card key={i}>
              <CardHeader>
                <div className="animate-pulse space-y-2">
                  <div className="h-5 bg-gray-200 rounded w-1/3" />
                  <div className="h-4 bg-gray-100 rounded w-2/3" />
                </div>
              </CardHeader>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Wallet className="w-8 h-8 text-primary" /> Billing & Subscription
          </h1>
          <p className="text-muted-foreground mt-1">Verwalte deine Abonnements, Zahlungen und Nutzung</p>
        </div>
        <div className="flex gap-2">
          <Button onClick={() => navigate(localePath('/pricing'))}>
            <TrendingUp className="w-4 h-4 mr-2" />
            Plan upgraden
          </Button>
        </div>
      </div>

      {/* Success/Cancel Alerts */}
      {new URLSearchParams(window.location.search).get('success') && (
        <Alert className="bg-green-50 border-green-200">
          <CheckCircle className="h-4 w-4 text-green-600" />
          <AlertDescription className="text-green-800">
            Zahlung erfolgreich! Dein Plan wird in Kürze aktiviert.
          </AlertDescription>
        </Alert>
      )}
      {new URLSearchParams(window.location.search).get('canceled') && (
        <Alert>
          <XCircle className="h-4 w-4" />
          <AlertDescription>
            Zahlung abgebrochen. Du kannst es jederzeit erneut versuchen.
          </AlertDescription>
        </Alert>
      )}

      {/* Main Tabs */}
      <Tabs defaultValue="overview" className="space-y-6">
        <TabsList className="grid w-full grid-cols-4 lg:w-auto">
          <TabsTrigger value="overview" className="flex items-center gap-2">
            <BarChart3 className="w-4 h-4" />
            Übersicht
          </TabsTrigger>
          <TabsTrigger value="payments" className="flex items-center gap-2">
            <CreditCard className="w-4 h-4" />
            Zahlungen
          </TabsTrigger>
          <TabsTrigger value="invoices" className="flex items-center gap-2">
            <FileText className="w-4 h-4" />
            Rechnungen
          </TabsTrigger>
          <TabsTrigger value="usage" className="flex items-center gap-2">
            <Zap className="w-4 h-4" />
            Nutzung
          </TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6">

      {/* Current Subscription */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>Aktueller Plan</span>
            {subscription && getStatusBadge(subscription.status)}
          </CardTitle>
          <CardDescription>Verwalte dein Abonnement und Zahlungsmethoden</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {subscription ? (
            <>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-2xl font-bold capitalize">{subscription.plan}</p>
                  <p className="text-sm text-muted-foreground">
                    {(
                      subscription.payment_type === 'stripe'
                        ? subscription.amount / 100
                        : subscription.amount
                    ).toFixed(2)} {subscription.currency.toUpperCase()} / {subscription.interval === 'month' || subscription.interval === 'monthly' ? 'Monat' : 'Jahr'}
                  </p>
                </div>
                <Crown className="w-12 h-12 text-primary" />
              </div>

              {subscription.status === 'active' && (
                <div className="space-y-1">
                  <p className="text-sm text-muted-foreground">
                    Nächste Abrechnung: {format(new Date(subscription.current_period_end), 'dd.MM.yyyy')}
                  </p>
                  {subscription.cancel_at_period_end && (
                    <Alert>
                      <AlertTriangle className="h-4 w-4" />
                      <AlertDescription>
                        Dein Abonnement wird am {format(new Date(subscription.current_period_end), 'dd.MM.yyyy')} gekündigt
                      </AlertDescription>
                    </Alert>
                  )}
                </div>
              )}

              <div className="flex gap-2">
                {!subscription.cancel_at_period_end && subscription.status === 'active' && (
                  <Button variant="outline" onClick={() => cancelMutation.mutate()} disabled={cancelMutation.isPending}>
                    <XCircle className="w-4 h-4 mr-2" />
                    Abonnement kündigen
                  </Button>
                )}
                <Button onClick={() => navigate(localePath('/pricing'))}>
                  <TrendingUp className="w-4 h-4 mr-2" />
                  Plan upgraden
                </Button>
                <Button variant="secondary" onClick={() => setWeb3Open((v) => !v)}>
                  <Wallet className="w-4 h-4 mr-2" />
                  Mit Wallet bezahlen
                </Button>
              </div>

              {web3Open && (
                <div className="mt-4 p-4 border rounded-lg bg-white dark:bg-slate-800">
                  <div className="flex items-center justify-between mb-3">
                    <div>
                      <p className="font-medium">Web3 One-Click Payment</p>
                      <p className="text-xs text-muted-foreground">Sichere Wallet-Verbindung • Keine privaten Schlüssel • Gebühren transparent</p>
                    </div>
                    <div className="flex items-center gap-2">
                      <label htmlFor="web3-currency" className="text-xs text-muted-foreground">Währung</label>
                      <select
                        id="web3-currency"
                        className="text-sm border rounded px-2 py-1 bg-transparent"
                        value={web3Currency}
                        onChange={(e) => setWeb3Currency(e.target.value as any)}
                      >
                        <option value="eth">ETH</option>
                        <option value="matic">MATIC (empfohlen)</option>
                        <option value="bnb">BNB</option>
                        <option value="trx">TRX</option>
                      </select>
                    </div>
                  </div>

                  {!web3Payment ? (
                    <div className="flex items-center gap-2">
                      <Button
                        onClick={async () => {
                          try {
                            setWeb3Loading(true);
                            setWeb3Error(null);
                            // Erstelle Krypto-Zahlung auf Basis des aktuellen Plans
                            const planName = subscription.plan;
                            const res = await api.post('/api/v1/crypto-payments/create', {
                              plan: planName,
                              currency: web3Currency,
                            });
                            const p = res?.data;
                            if (!p) throw new Error('Keine Zahlungsdaten erhalten');
                            setWeb3Payment({
                              payment_id: p.payment_id,
                              pay_amount: parseFloat(p.pay_amount),
                              pay_currency: p.pay_currency.toLowerCase(),
                              pay_address: p.pay_address,
                              plan_name: planName,
                            });
                          } catch (e: any) {
                            setWeb3Error(e?.message || 'Erstellung fehlgeschlagen');
                          } finally {
                            setWeb3Loading(false);
                          }
                        }}
                        disabled={web3Loading}
                      >
                        {web3Loading ? 'Erstelle…' : 'Zahlung erstellen'}
                      </Button>
                      {web3Error && <span className="text-xs text-red-600">{web3Error}</span>}
                      <span className="text-xs text-muted-foreground ml-auto">Erwartete Bestätigungszeit: ~{web3Currency==='matic'?'2–5 Min': web3Currency==='bnb'?'3–5 Min': web3Currency==='trx'?'1–3 Min':'5–15 Min'}</span>
                    </div>
                  ) : (
                    <div className="mt-3">
                      <Web3PaymentButton
                        amount={web3Payment.pay_amount}
                        currency={web3Payment.pay_currency}
                        paymentAddress={web3Payment.pay_address}
                        plan={web3Payment.plan_name}
                        onSuccess={() => {
                          // Optional: Refresh Crypto-Historie
                          qc.invalidateQueries({ queryKey: ['cryptoPayments'] });
                        }}
                      />
                    </div>
                  )}
                </div>
              )}
            </>
          ) : (
            <div className="text-center py-8">
              <p className="text-muted-foreground mb-4">Du hast derzeit kein aktives Abonnement</p>
              <Button onClick={() => navigate(localePath('/pricing'))}>Plan auswählen</Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Usage Stats */}
      {usage && (
        <Card>
          <CardHeader>
            <CardTitle>Nutzungsstatistik</CardTitle>
            <CardDescription>Deine aktuelle Nutzung im laufenden Abrechnungszeitraum</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-3">
              {/* Traces */}
              <div>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm font-medium">Transaction Traces</span>
                  <span className="text-sm text-muted-foreground">
                    {usage.traces_used} / {usage.traces_limit === -1 ? '∞' : usage.traces_limit}
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full ${getUsageColor(getUsagePercentage(usage.traces_used, usage.traces_limit))}`}
                    style={{ width: `${usage.traces_limit === -1 ? 0 : getUsagePercentage(usage.traces_used, usage.traces_limit)}%` }}
                  />
                </div>
              </div>

              {/* Cases */}
              <div>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm font-medium">Active Cases</span>
                  <span className="text-sm text-muted-foreground">
                    {usage.cases_used} / {usage.cases_limit === -1 ? '∞' : usage.cases_limit}
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full ${getUsageColor(getUsagePercentage(usage.cases_used, usage.cases_limit))}`}
                    style={{ width: `${usage.cases_limit === -1 ? 0 : getUsagePercentage(usage.cases_used, usage.cases_limit)}%` }}
                  />
                </div>
              </div>

              {/* API Calls */}
              <div>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm font-medium">API Calls</span>
                  <span className="text-sm text-muted-foreground">
                    {usage.api_calls_used} / {usage.api_calls_limit === -1 ? '∞' : usage.api_calls_limit}
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full ${getUsageColor(getUsagePercentage(usage.api_calls_used, usage.api_calls_limit))}`}
                    style={{ width: `${usage.api_calls_limit === -1 ? 0 : getUsagePercentage(usage.api_calls_used, usage.api_calls_limit)}%` }}
                  />
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Payment Methods */}
      <Card>
        <CardHeader>
          <CardTitle>Zahlungsmethoden</CardTitle>
          <CardDescription>Verwalte deine Kreditkarten und Zahlungsmethoden</CardDescription>
        </CardHeader>
        <CardContent>
          {paymentMethods && paymentMethods.length > 0 ? (
            <div className="space-y-3">
              {paymentMethods.map((pm) => (
                <div key={pm.id} className="flex items-center justify-between p-3 border rounded-lg">
                  <div className="flex items-center gap-3">
                    {pm.type === 'card' ? (
                      <CreditCard className="w-5 h-5 text-muted-foreground" />
                    ) : (
                      <Bitcoin className="w-5 h-5 text-orange-500" />
                    )}
                    <div>
                      <p className="font-medium">{pm.display_name}</p>
                      <p className="text-sm text-muted-foreground">
                        {pm.type === 'card' && pm.details.exp_month && pm.details.exp_year
                          ? `Läuft ab ${pm.details.exp_month}/${pm.details.exp_year}`
                          : pm.details.last_used
                          ? `Zuletzt genutzt: ${format(new Date(pm.details.last_used), 'dd.MM.yyyy')}`
                          : 'Kryptowährung'}
                      </p>
                    </div>
                  </div>
                  {pm.is_default && <Badge>Standard</Badge>}
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8">
              <p className="text-muted-foreground mb-4">Keine Zahlungsmethoden hinterlegt</p>
              <Button variant="outline" onClick={() => portalMutation.mutate()}>
                Zahlungsmethode hinzufügen
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

        </TabsContent>

        {/* Payments Tab */}
        <TabsContent value="payments" className="space-y-6">
          {/* Payment Methods Card (from overview) */}
          <Card>
            <CardHeader>
              <CardTitle>Zahlungsmethoden</CardTitle>
              <CardDescription>Verwalte deine Kreditkarten und Kryptowährungen</CardDescription>
            </CardHeader>
            <CardContent>
              {paymentMethods && paymentMethods.length > 0 ? (
                <div className="space-y-3">
                  {paymentMethods.map((pm) => (
                    <div key={pm.id} className="flex items-center justify-between p-4 border rounded-lg hover:border-primary/50 transition-colors">
                      <div className="flex items-center gap-3">
                        {pm.type === 'card' ? (
                          <div className="p-2 bg-blue-100 rounded-lg">
                            <CreditCard className="w-5 h-5 text-blue-600" />
                          </div>
                        ) : (
                          <div className="p-2 bg-orange-100 rounded-lg">
                            <Bitcoin className="w-5 h-5 text-orange-600" />
                          </div>
                        )}
                        <div>
                          <p className="font-semibold">{pm.display_name}</p>
                          <p className="text-sm text-muted-foreground">
                            {pm.type === 'card' && pm.details.exp_month && pm.details.exp_year
                              ? `Läuft ab ${pm.details.exp_month}/${pm.details.exp_year}`
                              : pm.details.last_used
                              ? `Zuletzt: ${format(new Date(pm.details.last_used), 'dd.MM.yyyy')}`
                              : pm.details.currency || 'Kryptowährung'}
                          </p>
                        </div>
                      </div>
                      {pm.is_default && <Badge className="bg-green-100 text-green-800">Standard</Badge>}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12">
                  <Wallet className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                  <p className="text-muted-foreground mb-4">Keine Zahlungsmethoden hinterlegt</p>
                  <Button onClick={() => navigate(localePath('/pricing'))}>
                    Jetzt hinzufügen
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Invoices Tab */}
        <TabsContent value="invoices" className="space-y-6">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Rechnungen & Belege</CardTitle>
                  <CardDescription>Alle deine Zahlungen (Karte & Krypto)</CardDescription>
                </div>
                <Button variant="outline" size="sm" onClick={async () => {
                  try {
                    const resp = await fetch('/api/v1/billing/invoices/export?format=csv', { credentials: 'include' });
                    if (!resp.ok) throw new Error('Export fehlgeschlagen');
                    const blob = await resp.blob();
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `invoices_export_${Date.now()}.csv`;
                    document.body.appendChild(a);
                    a.click();
                    a.remove();
                    window.URL.revokeObjectURL(url);
                  } catch {}
                }}>
                  <Download className="w-4 h-4 mr-2" />
                  Alle exportieren
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {invoices && invoices.length > 0 ? (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Rechnungsnummer</TableHead>
                      <TableHead>Datum</TableHead>
                      <TableHead>Betrag</TableHead>
                      <TableHead>Zahlungsart</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead className="text-right">Aktionen</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {invoices.map((invoice) => (
                      <TableRow key={invoice.id}>
                        <TableCell className="font-mono text-sm">{invoice.number}</TableCell>
                        <TableCell>{format(new Date(invoice.created), 'dd.MM.yyyy')}</TableCell>
                        <TableCell className="font-semibold">
                          {invoice.amount_paid.toFixed(2)} {invoice.currency.toUpperCase()}
                        </TableCell>
                        <TableCell>
                          <Badge variant={invoice.payment_type === 'crypto' ? 'secondary' : 'outline'} className="flex items-center gap-1 w-fit">
                            {invoice.payment_type === 'crypto' ? (
                              <><Bitcoin className="w-3 h-3" /> Krypto</>
                            ) : (
                              <><CreditCard className="w-3 h-3" /> Karte</>
                            )}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <Badge variant={invoice.status === 'paid' ? 'default' : 'secondary'} className="flex items-center gap-1 w-fit">
                            {invoice.status === 'paid' ? (
                              <><CheckCircle className="w-3 h-3" /> Bezahlt</>
                            ) : invoice.status}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-right">
                          <div className="flex items-center justify-end gap-2">
                            {invoice.tx_hash && (
                              <a href={(function(){
                                const cur = (invoice.currency || '').toLowerCase();
                                const hash = invoice.tx_hash as string;
                                const map: Record<string, (h:string)=>string> = {
                                  btc: (h)=>`https://mempool.space/tx/${h}`,
                                  ltc: (h)=>`https://blockchair.com/litecoin/transaction/${h}`,
                                  bch: (h)=>`https://blockchair.com/bitcoin-cash/transaction/${h}`,
                                  eth: (h)=>`https://etherscan.io/tx/${h}`,
                                  usdt: (h)=>`https://etherscan.io/tx/${h}`,
                                  usdc: (h)=>`https://etherscan.io/tx/${h}`,
                                  bnb: (h)=>`https://bscscan.com/tx/${h}`,
                                  matic: (h)=>`https://polygonscan.com/tx/${h}`,
                                  sol: (h)=>`https://solscan.io/tx/${h}`,
                                  trx: (h)=>`https://tronscan.org/#/transaction/${h}`,
                                };
                                const fn = map[cur] || map['eth'];
                                return fn(hash);
                              })()} target="_blank" rel="noopener noreferrer">
                                <Button variant="ghost" size="sm">
                                  <ArrowUpRight className="w-4 h-4" />
                                </Button>
                              </a>
                            )}
                            {invoice.pdf_url && (
                              <a href={invoice.pdf_url} target="_blank" rel="noopener noreferrer">
                                <Button variant="ghost" size="sm">
                                  <Download className="w-4 h-4" />
                                </Button>
                              </a>
                            )}
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              ) : (
                <div className="text-center py-12">
                  <FileText className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                  <p className="text-muted-foreground">Keine Rechnungen vorhanden</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Usage Tab */}
        <TabsContent value="usage" className="space-y-6">
          {usage && (
            <Card>
              <CardHeader>
                <CardTitle>Nutzungsstatistik</CardTitle>
                <CardDescription>
                  Zeitraum: {format(new Date(usage.period_start), 'dd.MM.yyyy')} - {format(new Date(usage.period_end), 'dd.MM.yyyy')}
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Traces */}
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">Transaction Traces</span>
                    <span className="text-sm text-muted-foreground font-mono">
                      {usage.traces_used} / {usage.traces_limit === -1 ? '∞' : usage.traces_limit}
                    </span>
                  </div>
                  <Progress value={getUsagePercentage(usage.traces_used, usage.traces_limit)} className="h-2" />
                  {getUsagePercentage(usage.traces_used, usage.traces_limit) >= 80 && (
                    <p className="text-xs text-orange-600">⚠️ Sie erreichen bald Ihr Limit</p>
                  )}
                </div>

                {/* Cases */}
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">Active Cases</span>
                    <span className="text-sm text-muted-foreground font-mono">
                      {usage.cases_used} / {usage.cases_limit === -1 ? '∞' : usage.cases_limit}
                    </span>
                  </div>
                  <Progress value={getUsagePercentage(usage.cases_used, usage.cases_limit)} className="h-2" />
                </div>

                {/* API Calls */}
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">API Calls</span>
                    <span className="text-sm text-muted-foreground font-mono">
                      {usage.api_calls_used} / {usage.api_calls_limit === -1 ? '∞' : usage.api_calls_limit}
                    </span>
                  </div>
                  <Progress value={getUsagePercentage(usage.api_calls_used, usage.api_calls_limit)} className="h-2" />
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}

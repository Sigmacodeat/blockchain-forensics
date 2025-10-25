import React, { useEffect, useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { usePageMeta } from '@/hooks/usePageMeta'
import { useEnhancedSEO } from '@/hooks/useEnhancedSEO'
import { Link } from 'react-router-dom'
import LinkLocalized from '@/components/LinkLocalized'
import plans from '@/config/plans.json'
import type { PricingConfig, Plan } from '@/features/pricing/types'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { useAuth } from '@/contexts/AuthContext'
import { getCurrencyForLanguage, LOCALE_MAP, useI18n } from '@/contexts/I18nContext'
import { CheckCircle2, ArrowRight, Zap, Shield, Users, TrendingUp, Crown, CreditCard, Bitcoin, ChevronDown, ChevronUp, Sparkles } from 'lucide-react'
import CryptoPaymentModal from '@/components/CryptoPaymentModal'
import { motion, AnimatePresence } from 'framer-motion'
import { fadeUp, fadeIn, staggerContainer, staggerItem, scaleUp, defaultViewport, cardHoverEffect } from '@/utils/animations'
import { convertFromUSD, getTaxHint } from '@/utils/currencyConverter'

const asConfig = plans as unknown as PricingConfig

function yearlyPrice(plan: Plan, discountPct: number) {
  if (plan.monthly_price_usd === undefined) return 'Individuell'
  const yearly = Math.round(plan.monthly_price_usd * 12 * (1 - discountPct / 100))
  return `$${yearly.toLocaleString('en-US')}`
}

function getYearlySavings(plan: Plan, discountPct: number) {
  if (plan.monthly_price_usd === undefined) return null
  const savings = Math.round(plan.monthly_price_usd * 12 * (discountPct / 100))
  return savings
}

export default function PricingPage() {
  const { t, i18n } = useTranslation()
  const { currentLanguage } = useI18n()
  const lang = currentLanguage || i18n.language || 'en'
  
  // Automatische Währungserkennung basierend auf Sprache
  const locale = LOCALE_MAP[lang] || LOCALE_MAP[i18n.language] || 'en-US'
  const currency = getCurrencyForLanguage(lang)
  const currencyFmt = new Intl.NumberFormat(locale, { style: 'currency', currency, maximumFractionDigits: 0 })
  const numberFmt = new Intl.NumberFormat(locale)

  const formatPriceLocalized = (p?: number) => {
    if (p === undefined) return 'Custom'
    if (p === 0) return 'Free'
    // USD-Preis in lokale Währung konvertieren
    const converted = convertFromUSD(p, currency)
    return currencyFmt.format(converted)
  }
  
  // Tax hint für aktuelle Währung
  const taxHint = getTaxHint(currency, locale)
  usePageMeta(
    t('pricing.seo.title', 'Pricing | SIGMACODE Blockchain Forensics'),
    t('pricing.seo.description', 'Transparente Preise: Von Community bis Enterprise. Flexible Pläne für Teams, Unternehmen und Regulatoren.')
  )
  
  // Enhanced SEO for better social sharing
  useEnhancedSEO({
    title: t('pricing.seo.title', 'Pricing | SIGMACODE Blockchain Forensics'),
    description: t('pricing.seo.description', 'Transparente Preise für professionelle Blockchain-Forensik. Von Community bis Enterprise. 100+ blockchains, AI agents, court-ready evidence.'),
    keywords: ['blockchain forensics pricing', 'crypto investigation cost', 'AML compliance pricing'],
    og_image: '/og-images/pricing.png',
    og_image_width: 1200,
    og_image_height: 630,
    twitter_card: 'summary_large_image',
    og_type: 'website'
  })
  const config = asConfig
  const { plans: planList, annual_discount_percent } = config
  const [tenantPlan, setTenantPlan] = useState<string>('')
  const [saving, setSaving] = useState<string>('')
  const [isAnnual, setIsAnnual] = useState(true)
  const [cryptoModalOpen, setCryptoModalOpen] = useState(false)
  const [selectedPlan, setSelectedPlan] = useState<Plan | null>(null)
  const [expandedFeatures, setExpandedFeatures] = useState<Record<string, boolean>>({})

  const toggleFeatures = (planId: string) => {
    setExpandedFeatures(prev => ({ ...prev, [planId]: !prev[planId] }))
  }
  const { user } = useAuth()
  const role = String(user?.role || '').toUpperCase()
  const isLoggedIn = !!user
  const API_BASE = import.meta.env.VITE_API_URL || ''
  const ENABLE_BILLING = String(import.meta.env.VITE_ENABLE_BILLING || '').toLowerCase() === 'true'

  useEffect(() => {
    let ignore = false
    async function load() {
      // only attempt when billing is enabled and user is logged in
      if (!ENABLE_BILLING || !isLoggedIn) { if (!ignore) setTenantPlan(''); return }
      try {
        const url = `${API_BASE}/api/v1/billing/tenant/plan`
        const r = await fetch(url)
        if (!r.ok) { if (!ignore) setTenantPlan(''); return }
        const j = await r.json()
        if (!ignore) setTenantPlan(j.plan_id || '')
      } catch {
        if (!ignore) setTenantPlan('')
      }
    }
    load()
    return () => { ignore = true }
  }, [API_BASE, isLoggedIn, ENABLE_BILLING])

  async function setAsTenantPlan(planId: string) {
    try {
      setSaving(planId)
      if (!ENABLE_BILLING || !isLoggedIn) return
      const r = await fetch(`${API_BASE}/api/v1/billing/tenant/plan`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ plan_id: planId }) })
      if (!r.ok) throw new Error(await r.text())
      setTenantPlan(planId)
    } catch {
      // noop; in echter App: toast error
    } finally {
      setSaving('')
    }
  }

  async function startCheckout(planId: string) {
    try {
      if (!ENABLE_BILLING || !isLoggedIn) return
      const res = await fetch(`${API_BASE}/api/v1/billing/checkout`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ plan_id: planId }),
      })
      if (!res.ok) throw new Error(await res.text())
      const j = await res.json()
      const url: string | undefined = j?.url
      if (url) {
        window.location.href = url
      }
    } catch (e) {
      // noop; in echter App: toast error
    }
  }

  async function startCryptoPayment(plan: Plan) {
    try {
      // Use new invoice API instead of old crypto payment modal
      const response = await fetch('/api/v1/invoice', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          plan_name: plan.id,
          amount_btc: plan.monthly_price_usd ? plan.monthly_price_usd / 45000 : 0.001, // Rough BTC conversion
          expires_hours: 24
        })
      });

      if (!response.ok) {
        throw new Error('Failed to create invoice');
      }

      const invoice = await response.json();
      // Redirect to new checkout page
      window.location.href = `/checkout/${invoice.order_id}`;
    } catch (error) {
      console.error('Invoice creation failed:', error);
      // Fallback to old modal if new API fails
      setSelectedPlan(plan);
      setCryptoModalOpen(true);
    }
  }

  function handleCryptoPaymentSuccess() {
    setCryptoModalOpen(false)
    // Refresh page or show success message
    window.location.reload()
  }

  const ordered = useMemo(() => {
    const order = ['community', 'starter', 'pro', 'business', 'plus', 'enterprise']
    return [...planList].sort((a, b) => order.indexOf(a.id) - order.indexOf(b.id))
  }, [planList])

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <div className="border-b bg-gradient-to-b from-background to-muted/20">
        <div className="container mx-auto max-w-6xl px-4 sm:px-6 py-16">
          <motion.div 
            className="max-w-4xl mx-auto text-center"
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, ease: 'easeOut' }}
          >
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.5, delay: 0.2 }}
            >
              <Badge className="mb-3" variant="scan-border">{t('pricing.header.badge', 'Flexible Preise')}</Badge>
            </motion.div>
            <motion.h1 
              className="text-4xl sm:text-5xl lg:text-6xl font-bold mb-4 bg-gradient-to-r from-foreground via-foreground to-primary/80 bg-clip-text text-transparent"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.3 }}
            >
              {t('pricing.header.title', 'Der richtige Plan für jedes Team')}
            </motion.h1>
            <motion.p 
              className="text-sm text-muted-foreground mb-2"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.6, delay: 0.4 }}
            >
              SIGMACODE · Blockchain Forensics
            </motion.p>
            <motion.p 
              className="text-base sm:text-lg lg:text-xl text-muted-foreground mb-8 max-w-3xl mx-auto"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.6, delay: 0.5 }}
            >
              {t('pricing.header.subtitle', 'Von kostenlosen Community-Tools bis Enterprise mit White-Label. Starte heute und skaliere, wenn du wächst.')}
            </motion.p>
            
            {/* Billing Toggle */}
            <motion.div 
              className="flex items-center justify-center gap-4 mb-8"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.6 }}
            >
              <span className={`text-sm ${!isAnnual ? 'text-foreground font-medium' : 'text-muted-foreground'}`}>
                {t('pricing.toggle.monthly', 'Monatlich')}
              </span>
              <button
                onClick={() => setIsAnnual(!isAnnual)}
                className="relative inline-flex h-6 w-11 items-center rounded-full bg-primary transition"
              >
                <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition ${isAnnual ? 'translate-x-6' : 'translate-x-1'}`} />
              </button>
              <span className={`text-sm ${isAnnual ? 'text-foreground font-medium' : 'text-muted-foreground'}`}>
                {t('pricing.toggle.annual', 'Jährlich')}
              </span>
              <Badge variant="secondary" className="ml-2">
                {t('pricing.toggle.save', 'Spare {{pct}}%',{ pct: annual_discount_percent })}
              </Badge>
            </motion.div>

            {tenantPlan && user && (
              <motion.div 
                className="inline-flex items-center gap-2 px-4 py-2 bg-primary/10 rounded-full text-sm"
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.5, delay: 0.7 }}
              >
                <CheckCircle2 className="h-4 w-4 text-primary" />
                <span>{t('pricing.current_plan', 'Aktueller Plan')}: <strong>{tenantPlan}</strong></span>
              </motion.div>
            )}
          </motion.div>
        </div>
      </div>

      {/* Pricing Cards: All Plans */}
      <div className="container mx-auto max-w-7xl px-4 sm:px-6 py-16">
        <div className="max-w-7xl mx-auto">
          <motion.div 
            className="text-center mb-8"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={defaultViewport}
            transition={{ duration: 0.6 }}
          >
            <h2 className="text-3xl font-bold">{t('pricing.all.title', 'Alle Pläne')}</h2>
            <p className="text-muted-foreground">{t('pricing.all.subtitle', 'Community bis Enterprise – alles auf einen Blick')}</p>
          </motion.div>
          <motion.div 
            className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 lg:gap-8"
            variants={staggerContainer}
            initial="initial"
            whileInView="whileInView"
            viewport={defaultViewport}
          >
            {ordered.map((p) => {
              const isPopular = p.id === 'pro'
              const savings = getYearlySavings(p, annual_discount_percent)
              const savingsId = isAnnual && savings ? `savings-${p.id}` : undefined
              return (
                <motion.div
                  key={p.id}
                  variants={staggerItem}
                  whileHover={cardHoverEffect}
                  data-testid={`plan-card-${p.id}`}
                >
                  <Card
                    tabIndex={0}
                    className={`flex flex-col relative border transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-primary/50 h-full ${
                      isPopular ? 'border-primary/50 dark:border-primary/40 shadow-md bg-gradient-to-b from-background to-muted/20' : 'border-border bg-card'
                    } hover:shadow-xl hover:border-primary/30`}
                  >
                  {isPopular && (
                    <Badge
                      className="absolute left-1/2 -translate-x-1/2 -top-0 -translate-y-1/2 rounded-full text-sm font-semibold flex items-center gap-1.5 bg-gradient-to-r from-primary/10 to-blue-500/10 text-primary border border-primary/30 px-3 py-1 shadow-sm"
                      aria-label={t('pricing.card.popular_label', 'Beliebteste')}
                    >
                      <Crown className="h-4 w-4" />
                      {t('pricing.card.popular', 'Beliebteste')}
                    </Badge>
                  )}
                  <CardHeader className="pb-4">
                    <CardTitle className="flex flex-col">
                      <span className="text-sm font-bold tracking-tight uppercase text-muted-foreground mb-3">{p.name}</span>
                      <div className="mb-2">
                        <div
                          className="text-3xl sm:text-4xl font-bold tracking-tight mb-1"
                          aria-describedby={savingsId}
                          data-testid={`plan-price-${p.id}`}
                        >
                          {p.pricing === 'custom' ? (
                            <span className="bg-gradient-to-r from-primary to-blue-600 bg-clip-text text-transparent">
                              {t('pricing.card.custom', 'Custom')}
                            </span>
                          ) : (
                            formatPriceLocalized(isAnnual ? Math.round((p.monthly_price_usd || 0) * (1 - annual_discount_percent / 100)) : p.monthly_price_usd)
                          )}
                        </div>
                        {p.pricing !== 'custom' && (
                          <>
                            <div className="text-sm text-muted-foreground font-medium mb-2">
                              {t('pricing.card.per_month', 'pro Monat')}
                            </div>
                            {isAnnual && savings && (
                              <Badge
                                variant="secondary"
                                id={savingsId}
                                className="text-xs font-semibold bg-green-50 text-green-700 border border-green-200 dark:bg-green-900/20 dark:text-green-300 dark:border-green-800"
                              >
                                💰 {t('pricing.card.save_year', 'Spare ${{amount}}/Jahr', { amount: numberFmt.format(savings) })}
                              </Badge>
                            )}
                          </>
                        )}
                      </div>
                    </CardTitle>
                    <p className="text-sm text-muted-foreground leading-relaxed mt-2">
                      {p.id === 'community' && t('pricing.card.desc_community', 'Für Hobbyisten und Open Source')}
                      {p.id === 'starter' && t('pricing.card.desc_starter', 'Für kleine Teams')}
                      {p.id === 'pro' && t('pricing.card.desc_pro', 'Für wachsende Unternehmen')}
                      {p.id === 'business' && t('pricing.card.desc_business', 'Für größere Teams')}
                      {p.id === 'plus' && t('pricing.card.desc_plus', 'Für Finanzinstitute & Compliance-Teams')}
                      {p.id === 'enterprise' && t('pricing.card.desc_enterprise', 'Für Enterprises & Regulatoren')}
                    </p>
                  </CardHeader>
                  <CardContent className="flex-1 flex flex-col pt-3">
                    <div className="space-y-2.5 mb-5">
                      <div className="flex items-center gap-2 text-sm">
                        <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-primary/10 dark:bg-primary/20 flex items-center justify-center">
                          <span className="text-sm font-bold text-primary">{String(p.quotas.chains)}</span>
                        </div>
                        <span className="font-medium text-foreground">{t('pricing.features.blockchains', 'Blockchains')}</span>
                      </div>
                      {p.quotas.traces_monthly && (
                        <div className="flex items-center gap-2 text-sm">
                          <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-blue-50 dark:bg-blue-900/20 flex items-center justify-center">
                            <Zap className="h-4 w-4 text-blue-600 dark:text-blue-400" />
                          </div>
                          <span className="font-medium text-foreground">
                            <strong className="text-foreground">{String(p.quotas.traces_monthly)}</strong>
                            <span className="text-muted-foreground ml-1">Traces/mo</span>
                          </span>
                        </div>
                      )}
                      <div className="flex items-center gap-2 text-sm">
                        <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-purple-50 dark:bg-purple-900/20 flex items-center justify-center">
                          <Users className="h-4 w-4 text-purple-600 dark:text-purple-400" />
                        </div>
                        <span className="font-medium text-foreground">
                          <strong className="text-foreground">{String(p.quotas.seats)}</strong>
                          <span className="text-muted-foreground ml-1">{t('pricing.features.users', 'Users')}</span>
                        </span>
                      </div>
                      {typeof p.quotas.cases !== 'undefined' && (
                        <div className="flex items-center gap-2 text-sm">
                          <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-green-50 dark:bg-green-900/20 flex items-center justify-center">
                            <Shield className="h-4 w-4 text-green-600 dark:text-green-400" />
                          </div>
                          <span className="font-medium text-foreground">
                            <strong className="text-foreground">{String(p.quotas.cases)}</strong>
                            <span className="text-muted-foreground ml-1">{t('pricing.features.cases', 'Cases')}</span>
                          </span>
                        </div>
                      )}
                    </div>

                    <div className="border-t pt-3 mb-4">
                      <div className="text-[11px] font-bold uppercase tracking-wide text-muted-foreground mb-3 flex items-center gap-2">
                        <Sparkles className="h-3.5 w-3.5 text-primary" />
                        {t('pricing.top_features', 'TOP FEATURES')}
                      </div>
                      <div className="space-y-2">
                        {/* Immer sichtbare Features (erste 4) */}
                        {Object.entries(p.features).slice(0, 4).map(([k, v]) => (
                          <div key={k} className="flex items-start gap-2 text-xs">
                            <CheckCircle2 className="h-3 w-3 text-primary mt-0.5 flex-shrink-0" />
                            <div className="flex-1 leading-relaxed">
                              <span className="font-semibold text-foreground">{k}</span>
                              {typeof v === 'string' && <span className="text-muted-foreground ml-1">{v}</span>}
                            </div>
                          </div>
                        ))}
                        
                        {/* Ausklappbare Features (rest) */}
                        <AnimatePresence>
                          {expandedFeatures[p.id] && Object.entries(p.features).slice(4).map(([k, v]) => (
                            <motion.div
                              key={k}
                              initial={{ opacity: 0, height: 0 }}
                              animate={{ opacity: 1, height: 'auto' }}
                              exit={{ opacity: 0, height: 0 }}
                              transition={{ duration: 0.2 }}
                              className="flex items-start gap-2 text-xs overflow-hidden"
                            >
                              <CheckCircle2 className="h-3 w-3 text-primary mt-0.5 flex-shrink-0" />
                              <div className="flex-1 leading-relaxed">
                                <span className="font-semibold text-foreground">{k}</span>
                                {typeof v === 'string' && <span className="text-muted-foreground ml-1">{v}</span>}
                              </div>
                            </motion.div>
                          ))}
                        </AnimatePresence>

                        {/* Toggle Button */}
                        {Object.keys(p.features).length > 4 && (
                          <button
                            onClick={() => toggleFeatures(p.id)}
                            className="flex items-center gap-1.5 text-xs text-primary hover:text-primary/80 transition-colors font-semibold mt-2 group"
                          >
                            {expandedFeatures[p.id] ? (
                              <>
                                <ChevronUp className="h-3.5 w-3.5 group-hover:-translate-y-0.5 transition-transform" />
                                <span>{t('pricing.show_less', 'Weniger anzeigen')}</span>
                              </>
                            ) : (
                              <>
                                <ChevronDown className="h-3.5 w-3.5 group-hover:translate-y-0.5 transition-transform" />
                                <span>+{Object.keys(p.features).length - 4} {t('pricing.more', 'weitere Features')}</span>
                              </>
                            )}
                          </button>
                        )}
                      </div>
                    </div>

                    <div className="mt-auto space-y-3 pt-4 border-t">
                      {isLoggedIn ? (
                        <>
                          <Button
                            size="lg"
                            className="w-full h-12 text-base font-semibold shadow-lg hover:shadow-xl transition-shadow" 
                            variant={isPopular ? 'gradient' : 'default'}
                            disabled={p.pricing === 'custom'}
                            onClick={() => startCheckout(p.id)}
                            data-testid={`checkout-${p.id}`}
                          >
                            <CreditCard className="mr-2 h-5 w-5" />
                            {p.pricing === 'custom' ? t('pricing.cta.contact_sales', 'Kontakt Vertrieb') : t('pricing.cta.pay_card', 'Mit Karte zahlen')}
                          </Button>
                          {p.pricing !== 'custom' && (
                            <Button 
                              variant="warning"
                              size="lg"
                              className="w-full h-12 text-base font-semibold shadow-md hover:shadow-lg transition-shadow" 
                              onClick={() => startCryptoPayment(p)}
                            >
                              <Bitcoin className="mr-2 h-5 w-5" />
                              {t('pricing.cta.pay_crypto', 'Mit Krypto zahlen')}
                            </Button>
                          )}
                        </>
                      ) : (
                        <LinkLocalized to="/register">
                          <Button 
                            size="lg" 
                            className="w-full h-12 text-base font-semibold shadow-lg hover:shadow-xl transition-all" 
                            variant={isPopular ? 'gradient' : 'outline'} 
                            disabled={p.pricing === 'custom'}
                          >
                            {p.pricing === 'custom' ? t('pricing.cta.contact_sales', 'Kontakt Vertrieb') : t('pricing.cta.start_now', 'Jetzt starten')}
                            {p.pricing !== 'custom' && <ArrowRight className="ml-2 h-5 w-5" />}
                          </Button>
                        </LinkLocalized>
                      )}
                      {role === 'ADMIN' && (
                        <Button 
                          variant="ghost" 
                          size="sm"
                          className="w-full text-xs"
                          onClick={() => setAsTenantPlan(p.id)} 
                          disabled={saving === p.id || tenantPlan === p.id}
                        >
                          {saving === p.id ? t('pricing.cta.saving', 'Speichere…') : (tenantPlan === p.id ? t('pricing.cta.active_plan', '✓ Aktiver Plan') : t('pricing.cta.set_tenant_plan', 'Als Tenant-Plan'))}
                        </Button>
                      )}
                    </div>
                  </CardContent>
                </Card>
                </motion.div>
              )
            })}
          </motion.div>
        </div>
      </div>

      {/* Features Comparison */}
      <div className="border-t py-16 bg-muted/30">
        <div className="container mx-auto max-w-6xl px-4 sm:px-6">
          <div className="max-w-6xl mx-auto">
            <div className="text-center mb-12">
              <Badge className="mb-4" variant="scan-border">{t('pricing.included.badge', 'Was ist enthalten?')}</Badge>
              <h2 className="text-3xl font-bold mb-4">{t('pricing.included.title', 'Alle Features im Überblick')}</h2>
            </div>

            <div className="grid md:grid-cols-4 gap-6">
              <FeatureHighlight
                icon={<Shield className="h-8 w-8" />}
                title={t('pricing.included.security.title', 'Security & Compliance')}
                items={[t('pricing.included.security.i1','RBAC'), t('pricing.included.security.i2','SSO/SAML'), t('pricing.included.security.i3','Audit Logs'), t('pricing.included.security.i4','GDPR-konform')]}
              />
              <FeatureHighlight
                icon={<Zap className="h-8 w-8" />}
                title={t('pricing.included.performance.title', 'Performance')}
                items={[t('pricing.included.performance.i1','Real-Time Alerts'), t('pricing.included.performance.i2','API Access'), t('pricing.included.performance.i3','Priority Queue'), t('pricing.included.performance.i4','99.9% Uptime')]}
              />
              <FeatureHighlight
                icon={<Users className="h-8 w-8" />}
                title={t('pricing.included.team.title', 'Team Features')}
                items={[t('pricing.included.team.i1','Multi-User'), t('pricing.included.team.i2','Case Management'), t('pricing.included.team.i3','Evidence Chain'), t('pricing.included.team.i4','Collaboration')]}
              />
              <FeatureHighlight
                icon={<TrendingUp className="h-8 w-8" />}
                title={t('pricing.included.analytics.title', 'Advanced Analytics')}
                items={[t('pricing.included.analytics.i1','AI Agents'), t('pricing.included.analytics.i2','Graph Analytics'), t('pricing.included.analytics.i3','Risk Scoring'), t('pricing.included.analytics.i4','ML Models')]}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Add-ons & Overage */}
      <div className="border-t py-16">
        <div className="container mx-auto max-w-6xl px-4 sm:px-6">
          <div className="max-w-4xl mx-auto">
            <div className="text-center mb-12">
              <Badge className="mb-4" variant="scan-border">{t('pricing.addons.badge', 'Flexible Erweiterungen')}</Badge>
              <h2 className="text-3xl font-bold mb-4">{t('pricing.addons.title', 'Add-ons & Overage')}</h2>
              <p className="text-muted-foreground">
                {t('pricing.addons.subtitle', 'Erweitere deinen Plan nach Bedarf')}
              </p>
            </div>

            <div className="grid md:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle>{t('pricing.addons.overage.title', 'Overage Pricing')}</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-sm text-muted-foreground">{t('pricing.addons.overage.extra_credits', 'Extra Credits')}</span>
                    <span className="font-semibold">{currencyFmt.format(convertFromUSD(config.overage.price_per_1000_credits_usd, currency))}/{numberFmt.format(1000)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-muted-foreground">{t('pricing.addons.overage.monthly_cap', 'Monatlicher Cap')}</span>
                    <span className="font-semibold">Konfigurierbar</span>
                  </div>
                  <p className="text-xs text-muted-foreground pt-2">
                    {t('pricing.addons.overage.note', 'Nutze mehr als dein Kontingent? Kein Problem - Overage wird automatisch berechnet.')}
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>{t('pricing.addons.available.title', 'Verfügbare Add-ons')}</CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2 text-sm">
                    <li className="flex items-center gap-2">
                      <CheckCircle2 className="h-4 w-4 text-green-500" />
                      <span>{t('pricing.addons.available.i1', 'Zusätzliche Blockchains')}</span>
                    </li>
                    <li className="flex items-center gap-2">
                      <CheckCircle2 className="h-4 w-4 text-green-500" />
                      <span>{t('pricing.addons.available.i2', 'Extra User Seats')}</span>
                    </li>
                    <li className="flex items-center gap-2">
                      <CheckCircle2 className="h-4 w-4 text-green-500" />
                      <span>{t('pricing.addons.available.i3', 'Sanctions Premium (erweiterte Listen)')}</span>
                    </li>
                    <li className="flex items-center gap-2">
                      <CheckCircle2 className="h-4 w-4 text-green-500" />
                      <span>{t('pricing.addons.available.i4', 'Advanced Export-Formate')}</span>
                    </li>
                    <li className="flex items-center gap-2">
                      <CheckCircle2 className="h-4 w-4 text-green-500" />
                      <span>{t('pricing.addons.available.i5', 'Priority Support')}</span>
                    </li>
                    <li className="flex items-center gap-2">
                      <CheckCircle2 className="h-4 w-4 text-green-500" />
                      <span>{t('pricing.addons.available.i6', 'White-Label (Enterprise)')}</span>
                    </li>
                  </ul>
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      </div>

      {/* FAQ Preview */}
      <div className="border-t py-16 bg-muted/30">
        <div className="container mx-auto max-w-6xl px-4 sm:px-6">
          <div className="max-w-3xl mx-auto text-center">
            <h2 className="text-3xl font-bold mb-4">{t('pricing.faq.title', 'Noch Fragen?')}</h2>
            <p className="text-muted-foreground mb-8">
              {t('pricing.faq.subtitle', 'Kontaktiere unser Sales-Team für eine persönliche Demo')}
            </p>
            <div className="flex gap-4 justify-center">
              <LinkLocalized to="/register">
                <Button size="xl" variant="gradient">
                  {t('pricing.cta.demo', 'Demo anfragen')}
                  <ArrowRight className="ml-2 h-5 w-5" />
                </Button>
              </LinkLocalized>
              <LinkLocalized to="/about">
                <Button size="xl" variant="outline">
                  {t('pricing.cta.more_about', 'Mehr über uns')}
                </Button>
              </LinkLocalized>
            </div>
          </div>
        </div>
      </div>

      {/* Crypto Payment Modal */}
      {selectedPlan && (
        <CryptoPaymentModal
          isOpen={cryptoModalOpen}
          onClose={() => setCryptoModalOpen(false)}
          planName={selectedPlan.id}
          priceUSD={selectedPlan.monthly_price_usd || 0}
          onSuccess={handleCryptoPaymentSuccess}
        />
      )}
    </div>
  )
}

interface FeatureHighlightProps {
  icon: React.ReactNode
  title: string
  items: string[]
}

function FeatureHighlight({ icon, title, items }: FeatureHighlightProps) {
  return (
    <Card>
      <CardContent className="pt-6">
        <div className="text-primary mb-4">{icon}</div>
        <h3 className="font-semibold mb-3">{title}</h3>
        <ul className="space-y-2 text-sm text-muted-foreground">
          {items.map((item, i) => (
            <li key={i} className="flex items-center gap-2">
              <CheckCircle2 className="h-3 w-3 text-green-500 flex-shrink-0" />
              <span>{item}</span>
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  )
}

import React from 'react'
import { useTranslation } from 'react-i18next'
import { usePageMeta } from '@/hooks/usePageMeta'
import { useJsonLd } from '@/hooks/useJsonLd'
import { motion, useScroll, useTransform } from 'framer-motion'
import { Link } from 'react-router-dom'
import LinkLocalized from '@/components/LinkLocalized'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import plansConfig from '@/config/plans.json'
import { 
  Shield, 
  Search, 
  Network, 
  Bell, 
  Brain, 
  Lock, 
  TrendingUp, 
  Users, 
  CheckCircle2, 
  ArrowRight, 
  Zap,
  Globe,
  BarChart3,
  FileText,
  AlertTriangle,
  Eye,
  Target,
  Layers,
  Database,
  Sparkles,
  Crown
} from 'lucide-react'

export default function LandingPage() {
  const { t, i18n } = useTranslation()
  const lang = i18n.language || 'en'
  usePageMeta(
    t('landing.seo.title', 'SIGMACODE | Enterprise Blockchain Intelligence'),
    t('landing.seo.description', 'AI‑getriebene Compliance, Ermittlungen und Risk Monitoring – in Echtzeit und Enterprise‑Grade. SIGMACODE Blockchain Forensics.')
  )
  useJsonLd('org-jsonld', {
    '@context': 'https://schema.org',
    '@type': 'Organization',
    name: 'SIGMACODE Blockchain Forensics',
    url: 'https://sigmacode.io',
    logo: 'https://sigmacode.io/logo.png',
    sameAs: [
      'https://twitter.com/sigmacode_io',
      'https://www.linkedin.com/company/sigmacode',
      'https://github.com/sigmacode-io'
    ]
  })
  function formatPrice(p?: number) {
    if (p === undefined) return 'Custom'
    if (p === 0) return 'Free'
    return `$${p.toLocaleString('en-US', { maximumFractionDigits: 0 })}`
  }

  const allPlans: any[] = (plansConfig as any).plans || []
  const preferredOrder = ['starter', 'pro', 'enterprise']
  const highlightPlans = allPlans.filter((p: any) => p.highlight_on_landing)
  const orderedHighlights = highlightPlans.sort((a: any, b: any) => preferredOrder.indexOf(a.id) - preferredOrder.indexOf(b.id))
  const previewPlans = orderedHighlights.slice(0, 3).map((p: any) => {
      const isCustom = p.pricing === 'custom'
      const price = isCustom ? 'Custom' : formatPrice(p.monthly_price_usd)
      const period = isCustom ? '' : '/Monat'
      const features: string[] = [
        `${String(p.quotas?.chains ?? '—')} Blockchains`,
        `${String(p.quotas?.seats ?? '—')} Benutzer`,
        `${String(p.quotas?.credits_monthly ?? '—')} Credits/Monat`,
        `${String(p.quotas?.alerts ?? '—')} Alerts`,
      ]
      const savingsPercent = (plansConfig as any).annual_discount_percent
      return { name: p.name, price, period, description: '', features, popular: p.id === 'pro', savingsPercent: isCustom ? undefined : savingsPercent }
    })
  const { scrollYProgress } = useScroll()
  const heroParallaxY = useTransform(scrollYProgress, [0, 1], ['0%', '20%'])

  const fadeUp = {
    initial: { opacity: 0, y: 24 },
    whileInView: { opacity: 1, y: 0, transition: { duration: 0.6, ease: 'easeOut' } },
  }

  const fadeIn = {
    initial: { opacity: 0 },
    whileInView: { opacity: 1, transition: { duration: 0.6, ease: 'easeOut' } },
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-background to-muted/20">
      <motion.div
        className="fixed left-0 top-0 h-1 bg-primary z-[70] origin-left pointer-events-none"
        style={{ scaleX: scrollYProgress, width: '100%' }}
      />

      {/* Hero Section */}
      <motion.section
        className="pt-16 sm:pt-20 md:pt-24 pb-10 sm:pb-12 md:pb-14 px-4 sm:px-6"
        initial="initial"
        whileInView="whileInView"
        viewport={{ once: true, amount: 0.3 }}
        variants={fadeUp}
      >
        <div className="container mx-auto max-w-6xl">
          <motion.div className="text-center mb-10 sm:mb-12" variants={fadeIn}>
            <Badge className="mb-4" variant="scan-border">
              <Sparkles className="h-3 w-3 mr-1" />
              {t('landing.hero.badge', 'sigmacode.io · Blockchain Forensics')}
            </Badge>
            <h1 className="text-4xl md:text-5xl font-extrabold mb-4 sm:mb-6 tracking-tight leading-[1.15] pb-1 bg-clip-text text-transparent bg-gradient-to-b from-slate-900 to-slate-600 dark:from-white dark:to-slate-400 max-w-[20ch] sm:max-w-none mx-auto text-balance hyphens-auto">
              {t('landing.hero.title', 'Enterprise Blockchain Intelligence')}
            </h1>
            <p className="text-base sm:text-xl text-muted-foreground max-w-2xl sm:max-w-3xl mx-auto mb-8">
              {t('landing.hero.subtitle', 'AI‑driven Compliance, Ermittlungen und Risk Monitoring – in Echtzeit und Enterprise‑Grade.')}
            </p>
            <div className="flex flex-col sm:flex-row gap-3 sm:gap-4 justify-center mb-8 sm:mb-10">
              <Link to={`/${lang}/demo/live`}>
                <Button size="lg" className="text-lg px-8 font-semibold shadow-md hover:shadow-lg bg-gradient-to-r from-primary to-purple-600">
                  <Zap className="mr-2 h-5 w-5" />
                  {t('landing.cta.live_demo', '30-Min Live-Demo')}
                  <ArrowRight className="ml-2 h-5 w-5" />
                </Button>
              </Link>
              <Link to={`/${lang}/demo/sandbox`}>
                <Button size="lg" variant="outline" className="text-lg px-8 font-medium border-gray-300 dark:border-slate-600 hover:bg-gray-100 dark:hover:bg-slate-700">
                  <Eye className="mr-2 h-5 w-5" />
                  {t('landing.cta.sandbox', 'Sandbox ansehen')}
                </Button>
              </Link>
              <Link to={`/${lang}/pricing`}>
                <Button size="lg" variant="ghost" className="text-lg px-8 font-medium">
                  {t('landing.cta.pricing', 'Pricing')}
                </Button>
              </Link>
            </div>
            <div className="flex flex-wrap items-center justify-center gap-3 sm:gap-6 text-xs sm:text-sm text-muted-foreground px-2">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-green-500" />
                <span>{t('landing.hero.point1', '100+ Blockchains')}</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-green-500" />
                <span>{t('landing.hero.point2', 'OFAC/UN/EU Sanctions')}</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-green-500" />
                <span>{t('landing.hero.point3', 'Real-Time Monitoring')}</span>
              </div>
            </div>
          </motion.div>

          {/* Hero Visual */}
          <div className="relative">
            <motion.div className="absolute inset-0 bg-gradient-to-r from-primary/20 to-blue-600/20 blur-3xl" style={{ y: heroParallaxY }} />
            <motion.div className="relative bg-card dark:bg-slate-900 border border-border rounded-2xl shadow-2xl p-4 sm:p-5 md:p-6" initial={{ opacity: 0, y: 24 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ duration: 0.6 }}>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 sm:gap-6">
                <div className="md:col-span-2 space-y-3 sm:space-y-4">
                  <div className="flex items-center gap-3 p-3 sm:p-4 bg-background rounded-lg border border-border">
                    <Search className="h-5 w-5 sm:h-6 sm:w-6 text-primary" />
                    <div className="flex-1">
                      <div className="text-sm font-medium">Transaction Trace</div>
                      <div className="text-[11px] sm:text-xs text-muted-foreground break-all">0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D</div>
                    </div>
                    <Badge variant="destructive" className="text-[10px] sm:text-xs">HIGH RISK</Badge>
                  </div>
                  <div className="flex items-center gap-3 p-3 sm:p-4 bg-background rounded-lg border border-border">
                    <AlertTriangle className="h-5 w-5 sm:h-6 sm:w-6 text-orange-500" />
                    <div className="flex-1">
                      <div className="text-sm font-medium">Mixing Service Detected</div>
                      <div className="text-[11px] sm:text-xs text-muted-foreground">Tornado Cash interaction found</div>
                    </div>
                    <Badge className="text-[10px] sm:text-xs">Alert</Badge>
                  </div>
                  <div className="flex items-center gap-3 p-3 sm:p-4 bg-background rounded-lg border border-border">
                    <Shield className="h-5 w-5 sm:h-6 sm:w-6 text-green-500" />
                    <div className="flex-1">
                      <div className="text-sm font-medium">OFAC Sanction Check</div>
                      <div className="text-[11px] sm:text-xs text-muted-foreground">3 matches found in downstream flow</div>
                    </div>
                    <Badge variant="destructive" className="text-[10px] sm:text-xs">BLOCKED</Badge>
                  </div>
                </div>
                <div className="space-y-3 sm:space-y-4">
                  <motion.div className="p-3 sm:p-4 bg-background rounded-lg border border-border" initial={{ opacity: 0, y: 12 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: 0.05 }}>
                    <div className="text-[11px] sm:text-xs text-muted-foreground mb-2">Risk Score</div>
                    <div className="text-2xl sm:text-3xl font-bold text-red-500">94/100</div>
                  </motion.div>
                  <motion.div className="p-3 sm:p-4 bg-background rounded-lg border border-border" initial={{ opacity: 0, y: 12 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: 0.1 }}>
                    <div className="text-[11px] sm:text-xs text-muted-foreground mb-2">Chains</div>
                    <div className="text-xl sm:text-2xl font-bold">5 Chains</div>
                  </motion.div>
                  <motion.div className="p-3 sm:p-4 bg-background rounded-lg border border-border" initial={{ opacity: 0, y: 12 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: 0.15 }}>
                    <div className="text-[11px] sm:text-xs text-muted-foreground mb-2">Hops</div>
                    <div className="text-xl sm:text-2xl font-bold">12 Hops</div>
                  </motion.div>
                </div>
              </div>
            </motion.div>
          </div>
        </div>
      </motion.section>

      {/* Stats Section */}
      <motion.section className="py-12 sm:py-16 bg-muted/30" initial="initial" whileInView="whileInView" viewport={{ once: true, amount: 0.3 }} variants={fadeUp}>
        <div className="container mx-auto max-w-6xl px-4 sm:px-6">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-6 sm:gap-8 text-center">
            <motion.div whileHover={{ scale: 1.02 }}>
              <div className="text-4xl font-bold text-primary mb-2">$12.6B+</div>
              <div className="text-sm text-muted-foreground">Recovered Assets</div>
            </motion.div>
            <motion.div whileHover={{ scale: 1.02 }}>
              <div className="text-4xl font-bold text-primary mb-2">100+</div>
              <div className="text-sm text-muted-foreground">Blockchains</div>
            </motion.div>
            <motion.div whileHover={{ scale: 1.02 }}>
              <div className="text-4xl font-bold text-primary mb-2">500+</div>
              <div className="text-sm text-muted-foreground">Enterprise Kunden</div>
            </motion.div>
            <motion.div whileHover={{ scale: 1.02 }}>
              <div className="text-4xl font-bold text-primary mb-2">99.9%</div>
              <div className="text-sm text-muted-foreground">Uptime SLA</div>
            </motion.div>
          </div>
        </div>
      </motion.section>

      {/* Features Section */}
      <motion.section id="features" className="py-16 sm:py-20 px-4 sm:px-6" initial="initial" whileInView="whileInView" viewport={{ once: true, amount: 0.2 }} variants={fadeUp}>
        <div className="container mx-auto max-w-6xl">
          <motion.div className="text-center mb-12 sm:mb-16" variants={fadeIn}>
            <Badge className="mb-4" variant="scan-border">{t('landing.features.badge', 'Features')}</Badge>
            <h2 className="text-3xl sm:text-4xl font-bold mb-3 sm:mb-4 text-balance hyphens-auto">
              {t('landing.features.title', 'Alles, was du für Blockchain-Forensik brauchst')}
            </h2>
            <p className="text-base sm:text-xl text-muted-foreground max-w-2xl mx-auto">
              {t('landing.features.subtitle', 'Enterprise-Grade-Werkzeuge für Compliance, Ermittlungen und Risikomanagement')}
            </p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 sm:gap-8">
            {/* Feature Cards */}
            <FeatureCard
              icon={<Search className="h-8 w-8" />}
              title="Transaction Tracing"
              description="Multi-Chain-Tracing über 100+ Blockchains. Recursive Forward/Backward-Tracing mit Bridge-Detection und Privacy-Coin-Demixing."
              highlights={['Cross-Chain', 'Bridge Detection', 'Tornado Cash']}
            />
            <FeatureCard
              icon={<Bell className="h-8 w-8" />}
              title="Real-Time Alerts"
              description="15+ konfigurierbare Alert-Regeln. Sanktionslisten (OFAC/UN/EU), Mixing Services, High-Value-Transfers und Anomaly Detection."
              highlights={['OFAC Sanctions', 'Mixing Detection', 'ML-based']}
            />
            <FeatureCard
              icon={<Network className="h-8 w-8" />}
              title="Graph Analytics"
              description="Neo4j-basierte Entity Relationship Analysis. Wallet-Clustering, Community Detection und Visual Investigation Workspace."
              highlights={['Entity Resolution', 'Clustering', 'Visual UI']}
            />
            <FeatureCard
              icon={<Brain className="h-8 w-8" />}
              title="AI-Powered Analysis"
              description="Machine Learning für Anomaly Detection, Risk Scoring und Pattern Recognition. Autonome AI-Agents für 24/7 Investigations."
              highlights={['ML Models', 'AI Agents', 'Auto-Analysis']}
            />
            <FeatureCard
              icon={<FileText className="h-8 w-8" />}
              title="Case Management"
              description="Vollständiges Investigation Management mit Evidence Chain-of-Custody, eIDAS-Signaturen und Court-Admissible Reports."
              highlights={['Evidence Chain', 'eIDAS', 'Export PDF']}
            />
            <FeatureCard
              icon={<Globe className="h-8 w-8" />}
              title="100+ Chains"
              description="Umfassende Chain-Coverage: EVM (L1/L2), Solana, Bitcoin, Privacy Coins, NFTs, DeFi-Protokolle und Cross-Chain-Bridges."
              highlights={['EVM/UTXO', 'DeFi/NFT', 'Privacy Coins']}
            />
            <FeatureCard
              icon={<Shield className="h-8 w-8" />}
              title="Sanctions Screening"
              description="Multi-List-Screening (OFAC/UN/EU/UK) mit automatischen Updates. Indirect Exposure Detection und VASP Travel Rule."
              highlights={['OFAC/UN/EU', 'VASP Screening', 'Travel Rule']}
            />
            <FeatureCard
              icon={<Lock className="h-8 w-8" />}
              title="Enterprise Security"
              description="RBAC, JWT Auth, SSO/SAML, Rate Limiting, Audit Logs, GDPR-Compliance und SOC2/ISO27001-ready Infrastructure."
              highlights={['RBAC', 'SSO/SAML', 'Audit Logs']}
            />
            <FeatureCard
              icon={<TrendingUp className="h-8 w-8" />}
              title="Advanced Analytics"
              description="Dashboards für Risk, Performance und Compliance. Export zu Grafana, Custom Reports und API für Integrationen."
              highlights={['Dashboards', 'Custom Reports', 'API']}
            />
          </div>
        </div>
      </motion.section>

      {/* Use Cases Section */}
      <motion.section id="use-cases" className="py-16 sm:py-20 px-4 sm:px-6 bg-muted/30" initial="initial" whileInView="whileInView" viewport={{ once: true, amount: 0.2 }} variants={fadeUp}>
        <div className="container mx-auto max-w-6xl">
          <motion.div className="text-center mb-12 sm:mb-16" variants={fadeIn}>
            <Badge className="mb-4" variant="scan-border">{t('landing.use_cases.badge', 'Use Cases')}</Badge>
            <h2 className="text-3xl sm:text-4xl font-bold mb-3 sm:mb-4 text-balance hyphens-auto">
              {t('landing.use_cases.title', 'Für jeden Anwendungsfall die richtige Lösung')}
            </h2>
            <p className="text-base sm:text-xl text-muted-foreground">
              {t('landing.use_cases.subtitle', 'Von Law Enforcement bis FinTech')}
            </p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 sm:gap-8">
            <UseCaseCard
              icon={<Target className="h-10 w-10" />}
              title="Law Enforcement"
              description="Ermittlungen bei Ransomware, Fraud, Terrorfinanzierung und Darknet Markets"
              features={[
                'Asset Recovery ($12.6B+ erfolgreich)',
                'Court-Admissible Evidence',
                'Cross-Border Collaboration',
                'Darknet Intelligence'
              ]}
            />
            <UseCaseCard
              icon={<Users className="h-10 w-10" />}
              title="Crypto Exchanges & VASPs"
              description="AML-Compliance, Transaction Monitoring und Travel Rule für regulierte VASPs"
              features={[
                'KYT (Know Your Transaction)',
                'VASP Screening',
                'Travel Rule Automation',
                'Real-Time Risk Scoring'
              ]}
            />
            <UseCaseCard
              icon={<BarChart3 className="h-10 w-10" />}
              title="Financial Institutions"
              description="On-Chain-Risk-Assessment für Crypto-Exposure und Custody Services"
              features={[
                'Portfolio Risk Analysis',
                'Counterparty Due Diligence',
                'Custody Compliance',
                'Regulatory Reporting'
              ]}
            />
            <UseCaseCard
              icon={<Eye className="h-10 w-10" />}
              title="Regulators & Auditors"
              description="Oversight für Crypto-Markets, VASP-Aufsicht und Systemüberwachung"
              features={[
                'Market Surveillance',
                'VASP Oversight',
                'Sanctions Enforcement',
                'AML/CFT Compliance'
              ]}
            />
          </div>
        </div>
      </motion.section>

      {/* Technology Section */}
      <motion.section id="technology" className="py-16 sm:py-20 px-4 sm:px-6" initial="initial" whileInView="whileInView" viewport={{ once: true, amount: 0.2 }} variants={fadeUp}>
        <div className="container mx-auto max-w-6xl">
          <motion.div className="text-center mb-12 sm:mb-16" variants={fadeIn}>
            <Badge className="mb-4" variant="scan-border">{t('landing.tech.badge', 'Technologie')}</Badge>
            <h2 className="text-3xl sm:text-4xl font-bold mb-3 sm:mb-4 text-balance hyphens-auto">
              {t('landing.tech.title', 'State-of-the-Art Tech Stack')}
            </h2>
            <p className="text-base sm:text-xl text-muted-foreground">
              {t('landing.tech.subtitle', 'Enterprise-Grade Infrastructure für maximale Performance und Sicherheit')}
            </p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 sm:gap-8">
            <TechCard
              icon={<Layers className="h-8 w-8" />}
              title="Multi-Chain Support"
              items={[
                'EVM: Ethereum, Polygon, BSC, Arbitrum, Optimism',
                'UTXO: Bitcoin, Litecoin, Dogecoin',
                'Alt-L1: Solana, Cosmos, Polkadot',
                'Privacy: Monero, Zcash, Tornado Cash'
              ]}
            />
            <TechCard
              icon={<Database className="h-8 w-8" />}
              title="Data Architecture"
              items={[
                'Neo4j: Graph Database für Entity Relations',
                'PostgreSQL: Core Relational Data',
                'Redis: Caching & Rate Limiting',
                'Qdrant: Vector DB für AI/ML'
              ]}
            />
            <TechCard
              icon={<Zap className="h-8 w-8" />}
              title="Performance & Scale"
              items={[
                'Kafka: Real-Time Event Streaming',
                'Kubernetes: Auto-Scaling',
                'Prometheus: Monitoring & Alerts',
                '99.9% Uptime SLA'
              ]}
            />
          </div>
        </div>
      </motion.section>

      {/* Pricing Preview */}
      <motion.section id="pricing" className="py-16 sm:py-20 px-4 sm:px-6 bg-muted/30" initial="initial" whileInView="whileInView" viewport={{ once: true, amount: 0.2 }} variants={fadeUp}>
        <div className="container mx-auto max-w-6xl">
          <motion.div className="text-center mb-12 sm:mb-16" variants={fadeIn}>
            <Badge className="mb-4" variant="scan-border">{t('landing.pricing.badge', 'Pricing')}</Badge>
            <h2 className="text-3xl sm:text-4xl font-bold mb-3 sm:mb-4 text-balance hyphens-auto">
              {t('landing.pricing.title', 'Flexible Pakete für jede Unternehmensgröße')}
            </h2>
            <p className="text-base sm:text-xl text-muted-foreground mb-6 sm:mb-8">
              {t('landing.pricing.subtitle', 'Von kostenlos bis Enterprise - jetzt starten')}
            </p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5 sm:gap-6 mb-6 sm:mb-8" aria-label="Preise Vorschau">
            {previewPlans.map((p: any) => (
              <PricingCard
                key={p.name}
                name={p.name}
                price={p.price}
                period={p.period}
                description={p.description || (p.name === 'Enterprise' ? 'Für große Organisationen' : p.name === 'Pro' ? 'Für wachsende Unternehmen' : 'Für kleine Teams und Startups')}
                features={p.features}
                popular={p.popular}
                savingsPercent={p.savingsPercent}
              />
            ))}
          </div>

          <div className="text-center">
            <Link to={`/${lang}/pricing`}>
              <Button size="lg" className="hover:shadow-lg" aria-label={t('landing.pricing.view_all', 'Alle Preise ansehen')}>
                {t('landing.pricing.view_all', 'Alle Preise ansehen')}
                <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
            </Link>
          </div>
        </div>
      </motion.section>

      {/* CTA Section */}
      <motion.section className="py-16 sm:py-20 px-4 sm:px-6" initial="initial" whileInView="whileInView" viewport={{ once: true, amount: 0.3 }} variants={fadeUp}>
        <div className="container mx-auto max-w-4xl">
          <motion.div className="bg-gradient-to-r from-primary to-blue-600 rounded-2xl p-8 sm:p-12 text-center text-white" whileHover={{ scale: 1.01 }} transition={{ type: 'spring', stiffness: 200, damping: 20 }}>
            <h2 className="text-3xl sm:text-4xl font-bold mb-3 sm:mb-4 text-balance hyphens-auto">
              {t('landing.cta2.title', 'Bereit für Enterprise Blockchain Intelligence?')}
            </h2>
            <p className="text-base sm:text-xl mb-6 sm:mb-8 opacity-90">
              {t('landing.cta2.subtitle', 'Starte jetzt mit einer kostenlosen Demo und erlebe die Zukunft der Blockchain-Forensik')}
            </p>
            <div className="flex flex-col sm:flex-row gap-3 sm:gap-4 justify-center">
              <Link to={`/${lang}/register`}>
                <Button size="lg" variant="secondary" className="text-base sm:text-lg px-6 sm:px-8">
                  {t('landing.cta2.demo', 'Kostenlose Demo anfragen')}
                </Button>
              </Link>
              <Link to={`/${lang}/pricing`}>
                <Button size="lg" variant="outline" className="text-base sm:text-lg px-6 sm:px-8 bg-white/10 hover:bg-white/20 text-white dark:bg-white/5 dark:hover:bg-white/10 border border-border">
                  {t('landing.cta2.pricing', 'Pricing ansehen')}
                </Button>
              </Link>
            </div>
          </motion.div>
        </div>
      </motion.section>

    </div>
  )
}

// Helper Components
interface FeatureCardProps {
  icon: React.ReactNode
  title: string
  description: string
  highlights: string[]
}

function FeatureCard({ icon, title, description, highlights }: FeatureCardProps) {
  return (
    <motion.div
      tabIndex={0}
      className="bg-card border border-border rounded-xl p-5 sm:p-6 hover:shadow-lg transition-shadow focus:outline-none focus-visible:ring-2 focus-visible:ring-primary/50"
      initial={{ opacity: 0, y: 16 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, amount: 0.3 }}
      whileHover={{ y: -4 }}
      transition={{ duration: 0.5, ease: 'easeOut' }}
    >
      <div className="text-primary mb-3 sm:mb-4">{icon}</div>
      <h3 className="text-lg sm:text-xl font-semibold mb-1.5 sm:mb-2">{title}</h3>
      <p className="text-muted-foreground mb-3 sm:mb-4 text-sm sm:text-base">{description}</p>
      <div className="flex flex-wrap gap-1.5 sm:gap-2">
        {highlights.map((h, i) => (
          <Badge key={i} variant="secondary" className="text-[10px] sm:text-xs">
            {h}
          </Badge>
        ))}
      </div>
    </motion.div>
  )
}

interface UseCaseCardProps {
  icon: React.ReactNode
  title: string
  description: string
  features: string[]
}

function UseCaseCard({ icon, title, description, features }: UseCaseCardProps) {
  return (
    <motion.div
      tabIndex={0}
      className="bg-card border border-border rounded-xl p-6 sm:p-8 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary/50"
      initial={{ opacity: 0, y: 16 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, amount: 0.3 }}
      whileHover={{ y: -4 }}
      transition={{ duration: 0.5, ease: 'easeOut' }}
    >
      <div className="text-primary mb-3 sm:mb-4">{icon}</div>
      <h3 className="text-xl sm:text-2xl font-semibold mb-1.5 sm:mb-2">{title}</h3>
      <p className="text-sm sm:text-base text-muted-foreground mb-5 sm:mb-6">{description}</p>
      <ul className="space-y-3">
        {features.map((f, i) => (
          <li key={i} className="flex items-start gap-3">
            <CheckCircle2 className="h-4 w-4 sm:h-5 sm:w-5 text-green-500 mt-0.5 flex-shrink-0" />
            <span className="text-sm sm:text-base">{f}</span>
          </li>
        ))}
      </ul>
    </motion.div>
  )
}

interface TechCardProps {
  icon: React.ReactNode
  title: string
  items: string[]
}

function TechCard({ icon, title, items }: TechCardProps) {
  return (
    <motion.div
      tabIndex={0}
      className="bg-card border border-border rounded-xl p-5 sm:p-6 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary/50"
      initial={{ opacity: 0, y: 16 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, amount: 0.3 }}
      whileHover={{ y: -4 }}
      transition={{ duration: 0.5, ease: 'easeOut' }}
    >
      <div className="text-primary mb-3 sm:mb-4">{icon}</div>
      <h3 className="text-lg sm:text-xl font-semibold mb-3 sm:mb-4">{title}</h3>
      <ul className="space-y-1.5 sm:space-y-2">
        {items.map((item, i) => (
          <li key={i} className="text-sm sm:text-base text-muted-foreground flex items-start gap-2">
            <span className="text-primary mt-1">•</span>
            <span>{item}</span>
          </li>
        ))}
      </ul>
    </motion.div>
  )
}

interface PricingCardProps {
  name: string
  price: string
  period: string
  description: string
  features: string[]
  popular: boolean
  savingsPercent?: number
}

function PricingCard({ name, price, period, description, features, popular, savingsPercent }: PricingCardProps) {
  return (
    <motion.div
      tabIndex={0}
      className={`rounded-xl p-5 sm:p-6 relative border transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-primary/50 ${
        popular ? 'border-primary/50 dark:border-primary/40 shadow-md bg-gradient-to-b from-background to-muted/20' : 'border-border bg-card'
      } hover:shadow-xl hover:border-primary/30`}
      initial={{ opacity: 0, y: 16 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, amount: 0.3 }}
      whileHover={{ y: -4, scale: 1.02 }}
      transition={{ duration: 0.5, ease: 'easeOut' }}
    >
      {popular && (
        <Badge className="absolute left-1/2 -translate-x-1/2 -top-0 -translate-y-1/2 rounded-full text-sm font-semibold flex items-center gap-1.5 bg-gradient-to-r from-primary/10 to-blue-500/10 text-primary border border-primary/30 px-3 py-1 shadow-sm" aria-label="Beliebteste">
          <Crown className="h-4 w-4" />
          Beliebteste
        </Badge>
      )}
      <div className="text-center mb-3 sm:mb-4">
        <h3 className="text-base sm:text-lg font-bold tracking-tight uppercase text-muted-foreground mb-1.5">{name}</h3>
        <div className="mb-1">
          <span className="text-2xl sm:text-2xl font-bold tracking-tight">{price}</span>
          <span className="text-muted-foreground text-xs font-medium ml-1">{period}</span>
        </div>
        {savingsPercent && period && (
          <div className="mt-1">
            <Badge variant="secondary" className="text-[10px] font-semibold bg-green-50 text-green-700 border border-green-200 dark:bg-green-900/20 dark:text-green-300 dark:border-green-800">
              Spare {savingsPercent}% jährlich
            </Badge>
          </div>
        )}
        <p className="text-xs text-muted-foreground leading-tight mt-0.5">{description}</p>
      </div>
      <ul className="space-y-2 mb-4 sm:mb-5">
        {features.map((f, i) => (
          <li key={i} className="flex items-center gap-2">
            <CheckCircle2 className="h-3.5 w-3.5 text-green-500 flex-shrink-0" />
            <span className="text-xs leading-relaxed">{f}</span>
          </li>
        ))}
      </ul>
      <LinkLocalized to="/register" className="block">
        <Button className="w-full hover:shadow-lg" variant={popular ? 'default' : 'outline'} aria-label={`Jetzt starten: ${name} Plan`}>
          Jetzt starten
        </Button>
      </LinkLocalized>
    </motion.div>
  )
}

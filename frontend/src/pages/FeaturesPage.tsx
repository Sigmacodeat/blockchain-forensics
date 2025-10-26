import React, { useEffect, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { usePageMeta } from '@/hooks/usePageMeta'
import { Link } from 'react-router-dom'
import LinkLocalized from '@/components/LinkLocalized'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { motion, useInView, useSpring, useTransform } from 'framer-motion'
import {
  Search,
  Bell,
  Network,
  Brain,
  FileText,
  Globe,
  Shield,
  Lock,
  TrendingUp,
  Zap,
  Database,
  GitBranch,
  Activity,
  Code,
  Server,
  CheckCircle2,
  ArrowRight
} from 'lucide-react'

// Custom Hook für Counter-Animation
function useCountUp(end: number, duration: number = 2, suffix: string = '') {
  const [count, setCount] = useState(0)
  const nodeRef = useRef<HTMLDivElement>(null)
  const isInView = useInView(nodeRef, { once: true, margin: '-100px' })

  useEffect(() => {
    if (!isInView) return
    
    let startTime: number | null = null
    const startValue = 0
    
    const animate = (currentTime: number) => {
      if (!startTime) startTime = currentTime
      const progress = Math.min((currentTime - startTime) / (duration * 1000), 1)
      
      // Easing function für smooth animation
      const easeOutQuart = 1 - Math.pow(1 - progress, 4)
      const currentCount = Math.floor(easeOutQuart * end)
      
      setCount(currentCount)
      
      if (progress < 1) {
        requestAnimationFrame(animate)
      } else {
        setCount(end)
      }
    }
    
    requestAnimationFrame(animate)
  }, [isInView, end, duration])

  return { count, nodeRef }
}

export default function FeaturesPage() {
  const { t } = useTranslation()
  usePageMeta(
    t('features.seo.title', 'Features | SIGMACODE Blockchain Forensics'),
    t('features.seo.description', 'Die komplette Blockchain-Forensik-Suite: Tracing, Alerts, Graph Analytics, AI/ML, Case Management und Security.')
  )
  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <div className="border-b">
        <div className="container mx-auto max-w-6xl px-4 sm:px-6 py-16">
          <motion.div 
            className="max-w-4xl mx-auto text-center"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, ease: 'easeOut' }}
          >
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.5, delay: 0.2 }}
            >
              <Badge className="mb-3" variant="scan-border">{t('features.header.badge', 'Vollständige Features')}</Badge>
            </motion.div>
            <motion.h1 
              className="text-4xl md:text-5xl font-bold mb-4"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.3 }}
            >
              {t('features.header.title', 'Die komplette Blockchain-Forensik-Suite')}
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
              className="text-lg text-muted-foreground mb-6"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.6, delay: 0.5 }}
            >
              {t('features.header.subtitle', 'Von Transaction Tracing bis AI-Powered Analysis – alle Werkzeuge für professionelle Ermittlungen')}
            </motion.p>
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.6 }}
            >
              <LinkLocalized to="/register">
                <Button size="xl" variant="gradient">
                  {t('features.header.cta_try', 'Kostenlos testen')}
                  <ArrowRight className="ml-2 h-5 w-5" />
                </Button>
              </LinkLocalized>
            </motion.div>
          </motion.div>
        </div>
      </div>

      {/* Table of Contents */}
      <div className="border-b">
        <div className="container mx-auto max-w-6xl px-4 sm:px-6 py-12">
          <div className="max-w-4xl mx-auto">
            <div className="text-center mb-8">
              <Badge className="mb-3" variant="scan-border">{t('features.toc.badge', 'Inhaltsverzeichnis')}</Badge>
              <h2 className="text-2xl font-bold">{t('features.toc.title', 'Springe direkt zu den Features')}</h2>
            </div>
            <div className="grid md:grid-cols-3 gap-4 text-sm">
              <a href="#tracing" className="flex items-center gap-2 p-3 rounded-lg border hover:border-primary hover:bg-primary/5 transition-colors">
                <Search className="h-4 w-4 text-primary" />
                <span>{t('features.toc.tracing', 'Transaction Tracing')}</span>
              </a>
              <a href="#alerts" className="flex items-center gap-2 p-3 rounded-lg border hover:border-primary hover:bg-primary/5 transition-colors">
                <Bell className="h-4 w-4 text-primary" />
                <span>{t('features.toc.alerts', 'Real-Time Alerts')}</span>
              </a>
              <a href="#graph" className="flex items-center gap-2 p-3 rounded-lg border hover:border-primary hover:bg-primary/5 transition-colors">
                <Network className="h-4 w-4 text-primary" />
                <span>{t('features.toc.graph', 'Graph Analytics')}</span>
              </a>
              <a href="#ai" className="flex items-center gap-2 p-3 rounded-lg border hover:border-primary hover:bg-primary/5 transition-colors">
                <Brain className="h-4 w-4 text-primary" />
                <span>{t('features.toc.ai', 'AI & ML')}</span>
              </a>
              <a href="#case" className="flex items-center gap-2 p-3 rounded-lg border hover:border-primary hover:bg-primary/5 transition-colors">
                <FileText className="h-4 w-4 text-primary" />
                <span>{t('features.toc.case', 'Case Management')}</span>
              </a>
              <a href="#security" className="flex items-center gap-2 p-3 rounded-lg border hover:border-primary hover:bg-primary/5 transition-colors">
                <Lock className="h-4 w-4 text-primary" />
                <span>{t('features.toc.security', 'Security')}</span>
              </a>
            </div>
          </div>
        </div>
      </div>

      {/* Main Features */}
      <div className="container mx-auto max-w-6xl px-4 sm:px-6 py-16">
        <div className="space-y-32">
          {/* Transaction Tracing */}
          <FeatureSection
            id="tracing"
            badge={t('features.tracing.badge', 'Transaction Tracing')}
            title={t('features.tracing.title', 'Multi-Chain Transaction Intelligence')}
            description={t('features.tracing.desc', 'Verfolge Transaktionen über alle wichtigen Blockchains hinweg. Mit Cross-Chain-Bridge-Detection, Privacy-Coin-Demixing und rekursivem Forward/Backward-Tracing.')}
            icon={<Search className="h-12 w-12" />}
            features={[
              {
                title: t('features.tracing.cross_chain.title', 'Cross-Chain Tracing'),
                description: t('features.tracing.cross_chain.desc', '100+ Blockchains unterstützt: EVM, UTXO, Solana, Cosmos und mehr'),
                icon: <Globe className="h-6 w-6" />
              },
              {
                title: t('features.tracing.bridge.title', 'Bridge Detection'),
                description: t('features.tracing.bridge.desc', 'Automatische Erkennung von Cross-Chain-Bridges und Wrapped Assets'),
                icon: <GitBranch className="h-6 w-6" />
              },
              {
                title: t('features.tracing.demixing.title', 'Privacy Coin Demixing'),
                description: t('features.tracing.demixing.desc', 'Heuristische Analyse von Tornado Cash, Mixer und Privacy Coins'),
                icon: <Shield className="h-6 w-6" />
              },
              {
                title: t('features.tracing.recursive.title', 'Recursive Tracing'),
                description: t('features.tracing.recursive.desc', 'Forward/Backward-Tracing mit konfigurierbarer Tiefe und Filters'),
                icon: <Activity className="h-6 w-6" />
              }
            ]}
            stats={[
              { label: t('features.stats.blockchains', 'Blockchains'), value: '100+' },
              { label: t('features.stats.max_depth', 'Max Tracing Depth'), value: '50 Hops' },
              { label: t('features.stats.bridges', 'Bridge Protocols'), value: '20+' }
            ]}
          />

          {/* Real-Time Alerts */}
          <FeatureSection
            id="alerts"
            badge={t('features.alerts.badge', 'Real-Time Monitoring')}
            title={t('features.alerts.title', 'Intelligente Alert-Engine')}
            description={t('features.alerts.desc', '15+ konfigurierbare Alert-Regeln mit Machine Learning. Erhalte Benachrichtigungen über Sanktionen, Mixing, High-Value-Transfers und Anomalien.')}
            icon={<Bell className="h-12 w-12" />}
            features={[
              {
                title: t('features.alerts.sanctions.title', 'Sanctions Screening'),
                description: t('features.alerts.sanctions.desc', 'OFAC/UN/EU/UK Sanktionslisten mit täglichen Updates'),
                icon: <Shield className="h-6 w-6" />
              },
              {
                title: t('features.alerts.mixing.title', 'Mixing Detection'),
                description: t('features.alerts.mixing.desc', 'Tornado Cash, Blender.io und andere Mixing Services'),
                icon: <Zap className="h-6 w-6" />
              },
              {
                title: t('features.alerts.anomaly.title', 'Anomaly Detection'),
                description: t('features.alerts.anomaly.desc', 'ML-basierte Erkennung ungewöhnlicher Transaktionsmuster'),
                icon: <Brain className="h-6 w-6" />
              },
              {
                title: t('features.alerts.custom_rules.title', 'Custom Rules'),
                description: t('features.alerts.custom_rules.desc', 'Eigene Alert-Regeln mit Rule DSL und Policy Engine'),
                icon: <Code className="h-6 w-6" />
              }
            ]}
            stats={[
              { label: t('features.stats.alert_rules', 'Alert Rules'), value: '15+' },
              { label: t('features.stats.response_time', 'Response Time'), value: '<100ms' },
              { label: t('features.stats.false_positives', 'False Positives'), value: '<5%' }
            ]}
          />

          {/* Graph Analytics */}
          <FeatureSection
            id="graph"
            badge={t('features.graph.badge', 'Graph Intelligence')}
            title={t('features.graph.title', 'Entity Resolution & Network Analysis')}
            description={t('features.graph.desc', 'Neo4j-basierte Graph-Datenbank für Entity Clustering, Community Detection und Visual Investigation.')}
            icon={<Network className="h-12 w-12" />}
            features={[
              {
                title: t('features.graph.clustering.title', 'Wallet Clustering'),
                description: t('features.graph.clustering.desc', 'Automatisches Clustering von zusammengehörigen Wallets'),
                icon: <Network className="h-6 w-6" />
              },
              {
                title: t('features.graph.labels.title', 'Entity Labels'),
                description: t('features.graph.labels.desc', 'Exchange/VASP/DeFi-Labels mit Community Intelligence'),
                icon: <Database className="h-6 w-6" />
              },
              {
                title: t('features.graph.visual.title', 'Visual Investigation'),
                description: t('features.graph.visual.desc', 'Interaktiver Graph-Explorer für komplexe Analysen'),
                icon: <Activity className="h-6 w-6" />
              },
              {
                title: t('features.graph.community.title', 'Community Detection'),
                description: t('features.graph.community.desc', 'Erkennung von Wallets-Gruppen mit gemeinsamen Interessen'),
                icon: <Server className="h-6 w-6" />
              }
            ]}
            stats={[
              { label: t('features.stats.entities', 'Entities'), value: '50M+' },
              { label: t('features.stats.relationships', 'Relationships'), value: '500M+' },
              { label: t('features.stats.query_time', 'Query Time'), value: '<500ms' }
            ]}
          />

          {/* AI & ML */}
          <FeatureSection
            id="ai"
            badge={t('features.ai.badge', 'AI & Machine Learning')}
            title={t('features.ai.title', 'KI-gestützte Analysen')}
            description={t('features.ai.desc', 'Machine Learning Models für Anomaly Detection, Risk Scoring und autonome AI-Agents für 24/7 Investigations.')}
            icon={<Brain className="h-12 w-12" />}
            features={[
              {
                title: t('features.ai.risk.title', 'Risk Scoring'),
                description: t('features.ai.risk.desc', 'ML-basierte Risiko-Bewertung von Adressen und Transaktionen'),
                icon: <TrendingUp className="h-6 w-6" />
              },
              {
                title: t('features.ai.agents.title', 'AI Agents'),
                description: t('features.ai.agents.desc', 'Autonome Agents mit LangChain und GPT-4 Integration'),
                icon: <Brain className="h-6 w-6" />
              },
              {
                title: t('features.ai.pattern.title', 'Pattern Recognition'),
                description: t('features.ai.pattern.desc', 'Erkennung von Fraud-Patterns und Behavioral Analysis'),
                icon: <Activity className="h-6 w-6" />
              },
              {
                title: t('features.ai.smart_contract.title', 'Smart Contract Analysis'),
                description: t('features.ai.smart_contract.desc', 'Bytecode-Similarity und Vulnerability Detection'),
                icon: <Code className="h-6 w-6" />
              }
            ]}
            stats={[
              { label: t('features.stats.ml_models', 'ML Models'), value: '16+' },
              { label: t('features.stats.ai_agents', 'AI Agents'), value: '24/7' },
              { label: t('features.stats.accuracy', 'Accuracy'), value: '95%+' }
            ]}
          />

          {/* Case Management */}
          <FeatureSection
            id="case"
            badge={t('features.case.badge', 'Investigation Workflow')}
            title={t('features.case.title', 'Case Management & Evidence Chain')}
            description={t('features.case.desc', 'Vollständiges Investigation Management mit Evidence Chain-of-Custody, eIDAS-Signaturen und Court-Admissible Reports.')}
            icon={<FileText className="h-12 w-12" />}
            features={[
              {
                title: t('features.case.tracking.title', 'Case Tracking'),
                description: t('features.case.tracking.desc', 'Strukturiertes Case Management mit Workflow-Status'),
                icon: <FileText className="h-6 w-6" />
              },
              {
                title: t('features.case.evidence.title', 'Evidence Chain'),
                description: t('features.case.evidence.desc', 'Lückenlose Chain-of-Custody für gerichtsverwertbare Beweise'),
                icon: <Lock className="h-6 w-6" />
              },
              {
                title: t('features.case.eidas.title', 'eIDAS Signatures'),
                description: t('features.case.eidas.desc', 'Qualifizierte elektronische Signaturen nach EU-Standard'),
                icon: <Shield className="h-6 w-6" />
              },
              {
                title: t('features.case.export.title', 'Export & Reports'),
                description: t('features.case.export.desc', 'PDF/Excel-Export mit Timestamping und Audit Trail'),
                icon: <Server className="h-6 w-6" />
              }
            ]}
            stats={[
              { label: t('features.stats.case_templates', 'Case Templates'), value: '10+' },
              { label: t('features.stats.evidence_types', 'Evidence Types'), value: 'All' },
              { label: t('features.stats.compliance', 'Compliance'), value: 'eIDAS' }
            ]}
          />

          {/* Security & Compliance */}
          <FeatureSection
            id="security"
            badge={t('features.security.badge', 'Enterprise Security')}
            title={t('features.security.title', 'Security & Compliance')}
            description={t('features.security.desc', 'Enterprise-Grade-Sicherheit mit RBAC, SSO/SAML, Audit Logs und GDPR-Compliance.')}
            icon={<Lock className="h-12 w-12" />}
            features={[
              {
                title: t('features.security.rbac.title', 'RBAC'),
                description: t('features.security.rbac.desc', 'Granulare Role-Based Access Control mit Custom Roles'),
                icon: <Lock className="h-6 w-6" />
              },
              {
                title: t('features.security.sso.title', 'SSO/SAML'),
                description: t('features.security.sso.desc', 'Single Sign-On mit SAML 2.0 und OAuth 2.0'),
                icon: <Shield className="h-6 w-6" />
              },
              {
                title: t('features.security.audit.title', 'Audit Logs'),
                description: t('features.security.audit.desc', 'Vollständige Audit Trails für Compliance-Nachweise'),
                icon: <FileText className="h-6 w-6" />
              },
              {
                title: t('features.security.privacy.title', 'Data Privacy'),
                description: t('features.security.privacy.desc', 'GDPR-Compliance mit PII-Anonymisierung'),
                icon: <Database className="h-6 w-6" />
              }
            ]}
            stats={[
              { label: t('features.stats.uptime_sla', 'Uptime SLA'), value: '99.9%' },
              { label: t('features.stats.security_certs', 'Security Certs'), value: 'SOC2/ISO' },
              { label: t('features.stats.encryption', 'Encryption'), value: 'AES-256' }
            ]}
          />
        </div>
      </div>

      {/* CTA */}
      <div className="border-t py-16">
        <div className="container mx-auto max-w-6xl px-4 sm:px-6">
          <motion.div 
            className="max-w-3xl mx-auto text-center"
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: '-100px' }}
            transition={{ duration: 0.7, ease: 'easeOut' }}
          >
            <motion.h2 
              className="text-4xl font-bold mb-4"
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6, delay: 0.2 }}
            >
              {t('features.cta.title', 'Bereit für die komplette Suite?')}
            </motion.h2>
            <motion.p 
              className="text-lg text-muted-foreground mb-8"
              initial={{ opacity: 0 }}
              whileInView={{ opacity: 1 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6, delay: 0.3 }}
            >
              {t('features.cta.subtitle', 'Starte jetzt mit einer kostenlosen Demo')}
            </motion.p>
            <motion.div 
              className="flex gap-4 justify-center"
              initial={{ opacity: 0, y: 10 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6, delay: 0.4 }}
            >
              <LinkLocalized to="/register">
                <Button size="xl" variant="gradient">
                  {t('features.cta.demo', 'Demo anfragen')}
                  <ArrowRight className="ml-2 h-5 w-5" />
                </Button>
              </LinkLocalized>
              <LinkLocalized to="/pricing">
                <Button size="xl" variant="outline">
                  {t('features.cta.pricing', 'Pricing ansehen')}
                </Button>
              </LinkLocalized>
            </motion.div>
          </motion.div>
        </div>
      </div>
    </div>
  )
}

interface FeatureSectionProps {
  id?: string
  badge: string
  title: string
  description: string
  icon: React.ReactNode
  features: Array<{
    title: string
    description: string
    icon: React.ReactNode
  }>
  stats: Array<{
    label: string
    value: string
  }>
}

// Animated Stat Component
function AnimatedStat({ value, label, delay = 0 }: { value: string; label: string; delay?: number }) {
  const ref = useRef<HTMLDivElement>(null)
  const isInView = useInView(ref, { once: true, margin: '-100px' })
  const [displayValue, setDisplayValue] = useState('0')

  useEffect(() => {
    if (!isInView) return

    // Parse number from value string
    const numMatch = value.match(/([0-9.]+)/)
    if (!numMatch) {
      setDisplayValue(value)
      return
    }

    const targetNum = parseFloat(numMatch[1])
    const suffix = value.replace(numMatch[1], '')
    let startTime: number | null = null
    const duration = 2000 // 2 seconds

    const animate = (currentTime: number) => {
      if (!startTime) startTime = currentTime
      const progress = Math.min((currentTime - startTime) / duration, 1)
      
      // Easing function
      const easeOutQuart = 1 - Math.pow(1 - progress, 4)
      const currentNum = easeOutQuart * targetNum
      
      setDisplayValue(currentNum.toFixed(targetNum < 10 ? 1 : 0) + suffix)
      
      if (progress < 1) {
        requestAnimationFrame(animate)
      } else {
        setDisplayValue(value)
      }
    }

    const timer = setTimeout(() => {
      requestAnimationFrame(animate)
    }, delay * 1000)

    return () => clearTimeout(timer)
  }, [isInView, value, delay])

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: '-100px' }}
      transition={{ duration: 0.5, delay }}
    >
      <div className="text-3xl font-bold text-primary">{displayValue}</div>
      <div className="text-sm text-muted-foreground">{label}</div>
    </motion.div>
  )
}

function FeatureSection({ id, badge, title, description, icon, features, stats }: FeatureSectionProps) {
  return (
    <motion.div 
      id={id}
      className="grid md:grid-cols-2 gap-12 items-center"
      initial={{ opacity: 0, y: 50 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: '-100px' }}
      transition={{ duration: 0.7, ease: 'easeOut' }}
    >
      <div>
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          whileInView={{ opacity: 1, x: 0 }}
          viewport={{ once: true, margin: '-100px' }}
          transition={{ duration: 0.5, delay: 0.2 }}
        >
          <Badge className="mb-4" variant="scan-border">{badge}</Badge>
        </motion.div>
        <motion.div 
          className="text-primary mb-6"
          initial={{ opacity: 0, scale: 0.8 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true, margin: '-100px' }}
          transition={{ duration: 0.5, delay: 0.3 }}
        >
          {icon}
        </motion.div>
        <motion.h2 
          className="text-4xl font-bold mb-4"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-100px' }}
          transition={{ duration: 0.6, delay: 0.4 }}
        >
          {title}
        </motion.h2>
        <motion.p 
          className="text-xl text-muted-foreground mb-8"
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true, margin: '-100px' }}
          transition={{ duration: 0.6, delay: 0.5 }}
        >
          {description}
        </motion.p>
        <div className="grid grid-cols-3 gap-6 mb-8">
          {stats.map((stat, i) => (
            <AnimatedStat key={i} value={stat.value} label={stat.label} delay={0.6 + i * 0.1} />
          ))}
        </div>
      </div>
      <div className="grid grid-cols-2 gap-4">
        {features.map((feature, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: '-100px' }}
            transition={{ 
              duration: 0.5, 
              delay: 0.7 + i * 0.1,
              ease: 'easeOut'
            }}
            whileHover={{ 
              y: -4,
              transition: { duration: 0.2 }
            }}
          >
            <Card className="h-full transition-shadow hover:shadow-lg">
              <CardHeader>
                <motion.div 
                  className="text-primary mb-2"
                  initial={{ scale: 0 }}
                  whileInView={{ scale: 1 }}
                  viewport={{ once: true, margin: '-100px' }}
                  transition={{ 
                    duration: 0.4, 
                    delay: 0.8 + i * 0.1,
                    type: 'spring',
                    stiffness: 200
                  }}
                >
                  {feature.icon}
                </motion.div>
                <CardTitle className="text-lg">{feature.title}</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">{feature.description}</p>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </div>
    </motion.div>
  )
}

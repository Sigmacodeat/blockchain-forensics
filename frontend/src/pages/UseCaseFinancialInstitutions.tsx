/**
 * Use Case: Financial Institutions (Banken, Fintechs, Payment Providers)
 * SEO-Optimized Landing Page für Financial Institutions
 */

import React, { useEffect, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'
import { motion, useInView } from 'framer-motion'
import { 
  Building2, CheckCircle, Shield, TrendingUp, Globe, 
  ArrowRight, Clock, Users, Zap, AlertTriangle, FileText, Lock 
} from 'lucide-react'
import FAQSection from '@/components/FAQSection'
import { usePageMeta } from '@/hooks/usePageMeta'
import { useEnhancedSEO } from '@/hooks/useEnhancedSEO'

// Animated Counter Component
function AnimatedCounter({ value, label }: { value: string; label: string }) {
  const ref = useRef<HTMLDivElement>(null)
  const isInView = useInView(ref, { once: true, margin: '-50px' })
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
    const duration = 1500 // 1.5 seconds

    const animate = (currentTime: number) => {
      if (!startTime) startTime = currentTime
      const progress = Math.min((currentTime - startTime) / duration, 1)
      
      // Easing function for smooth animation
      const easeOutQuart = 1 - Math.pow(1 - progress, 4)
      const currentNum = easeOutQuart * targetNum
      
      setDisplayValue(currentNum.toFixed(targetNum < 10 ? 1 : 0) + suffix)
      
      if (progress < 1) {
        requestAnimationFrame(animate)
      } else {
        setDisplayValue(value)
      }
    }

    requestAnimationFrame(animate)
  }, [isInView, value])

  return (
    <div ref={ref}>
      <div className="text-3xl font-bold text-blue-600 dark:text-blue-400 mb-2">
        {displayValue}
      </div>
      <div className="text-sm text-slate-600 dark:text-slate-400">
        {label}
      </div>
    </div>
  )
}

export default function UseCaseFinancialInstitutions() {
  const { t, i18n } = useTranslation()

  useEnhancedSEO({
    title: 'Blockchain-Forensik für Banken & Fintech | KYC/AML-Compliance',
    description: 'Enterprise-Grade Crypto-Risk-Management für Financial Institutions. Real-Time Transaction Monitoring, Sanctions Screening, Travel Rule. FATF-konform.',
    keywords: ['Bank Crypto Compliance', 'Fintech AML', 'Financial Institution Blockchain', 'KYC Crypto', 'Bank Transaction Monitoring', 'FATF Travel Rule'],
    og_image: '/og-images/use-case-financial-institutions.png',
    og_image_width: 1200,
    og_image_height: 630,
    twitter_card: 'summary_large_image'
  })

  usePageMeta(
    'Blockchain-Forensik für Banken & Fintech',
    'Enterprise-Grade Crypto-Risk-Management für Financial Institutions. FATF-konform, Real-Time Monitoring.'
  )

  React.useEffect(() => {
    window.scrollTo({ top: 0, behavior: 'instant' })
  }, [])

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-slate-100 dark:from-slate-950 dark:via-slate-900 dark:to-slate-950">
      {/* Hero */}
      <section className="pt-24 pb-12 px-6">
        <div className="max-w-7xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="text-center mb-16"
          >
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-blue-100 dark:bg-blue-900/30 rounded-full mb-6">
              <Building2 className="w-4 h-4 text-blue-600 dark:text-blue-400" />
              <span className="text-sm font-medium text-blue-600 dark:text-blue-400">
                {t('use_case_financial_institutions.hero.badge')}
              </span>
            </div>
            
            <h1 className="text-3xl sm:text-4xl md:text-5xl lg:text-6xl font-bold mb-4 md:mb-6 bg-gradient-to-r from-blue-600 to-blue-800 bg-clip-text text-transparent">
              {t('use_case_financial_institutions.hero.title')}
            </h1>
            
            <p className="text-base sm:text-lg md:text-xl text-slate-600 dark:text-slate-400 max-w-3xl mx-auto mb-6 md:mb-8 px-4">
              {t('use_case_financial_institutions.hero.subtitle')}
            </p>

            <div className="flex flex-wrap gap-4 justify-center">
              <Link
                to={`/${i18n.language}/universal-screening`}
                className="px-8 py-4 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-lg font-semibold hover:from-blue-700 hover:to-blue-800 transition-all shadow-lg flex items-center gap-2"
              >
                {t('use_case_financial_institutions.hero.demo_button')}
                <ArrowRight className="w-5 h-5" />
              </Link>
              <Link
                to={`/${i18n.language}/pricing`}
                className="px-8 py-4 bg-white dark:bg-slate-800 text-slate-900 dark:text-white rounded-lg font-semibold hover:shadow-lg transition-all border border-slate-200 dark:border-slate-700"
              >
                {t('use_case_financial_institutions.hero.pricing_button')}
              </Link>
            </div>
          </motion.div>

          {/* Bank Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 md:gap-6 max-w-5xl mx-auto px-4">
            {[
              { value: '100', label: t('use_case_financial_institutions.stats.transaction_screening'), suffix: 'ms' },
              { value: '35', label: t('use_case_financial_institutions.stats.blockchain_networks'), suffix: '+' },
              { value: '99.9', label: t('use_case_financial_institutions.stats.uptime_sla'), suffix: '%' },
              { value: 'ISO 27001', label: t('use_case_financial_institutions.stats.iso_certified'), suffix: '' }
            ].map((stat, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 30, scale: 0.9 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                transition={{ 
                  delay: i * 0.15,
                  duration: 0.5,
                  type: 'spring',
                  stiffness: 100
                }}
                whileHover={{ 
                  y: -4,
                  transition: { duration: 0.2 }
                }}
                className="bg-white/80 dark:bg-slate-800/80 backdrop-blur-xl rounded-xl p-6 text-center shadow-lg hover:shadow-xl transition-shadow"
              >
                {stat.value.match(/[0-9]/) ? (
                  <AnimatedCounter 
                    value={stat.value + stat.suffix} 
                    label={stat.label} 
                  />
                ) : (
                  <>
                    <div className="text-3xl font-bold text-blue-600 dark:text-blue-400 mb-2">
                      {stat.value}
                    </div>
                    <div className="text-sm text-slate-600 dark:text-slate-400">
                      {stat.label}
                    </div>
                  </>
                )}
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Bank Challenges */}
      <section className="py-20 px-6 bg-white/50 dark:bg-slate-900/50">
        <div className="max-w-7xl mx-auto">
          <motion.h2 
            className="text-4xl font-bold text-center mb-16"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: '-100px' }}
            transition={{ duration: 0.6 }}
          >
            {t('use_case_financial_institutions.challenges.title')}
          </motion.h2>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {[
              {
                key: 'customer_onboarding',
                icon: Users
              },
              {
                key: 'regulatory_compliance',
                icon: Shield
              },
              {
                key: 'transaction_monitoring',
                icon: Zap
              },
              {
                key: 'fraud_prevention',
                icon: AlertTriangle
              },
              {
                key: 'cross_border_payments',
                icon: Globe
              },
              {
                key: 'audit_reporting',
                icon: FileText
              }
            ].map((item, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 40 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: '-50px' }}
                transition={{ 
                  delay: i * 0.1,
                  duration: 0.5,
                  ease: 'easeOut'
                }}
                whileHover={{ 
                  y: -6,
                  transition: { duration: 0.2 }
                }}
                className="bg-white dark:bg-slate-800 rounded-xl p-5 shadow-lg border border-slate-200/50 dark:border-slate-700/50 hover:shadow-xl transition-shadow"
              >
                <div className="flex items-start gap-3 mb-4">
                  <div className="p-3 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
                    <item.icon className="w-6 h-6 text-blue-600 dark:text-blue-400" />
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 dark:text-slate-400 mb-1">
                      Challenge:
                    </div>
                    <h3 className="font-bold text-lg mb-1">
                      {t(`use_case_financial_institutions.challenges.${item.key}.challenge`)}
                    </h3>
                    <div className="text-sm font-semibold text-blue-600 dark:text-blue-400">
                      → {t(`use_case_financial_institutions.challenges.${item.key}.solution`)}
                    </div>
                  </div>
                </div>

                <p className="text-sm text-slate-600 dark:text-slate-400 mb-4">
                  {t(`use_case_financial_institutions.challenges.${item.key}.description`)}
                </p>

                <div className="space-y-4 md:space-y-6 px-4">
                  {(t(`use_case_financial_institutions.challenges.${item.key}.features`, { returnObjects: true }) as string[]).map((feature: string, j: number) => (
                      <div key={j} className="flex items-center gap-2 text-sm">
                      <CheckCircle className="w-4 h-4 text-blue-500" />
                      <span>{feature}</span>
                    </div>
                  ))}
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Banking Workflow */}
      <section className="py-20 px-6">
        <div className="max-w-7xl mx-auto">
          <motion.h2 
            className="text-4xl font-bold text-center mb-16"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: '-100px' }}
            transition={{ duration: 0.6 }}
          >
            {t('use_case_financial_institutions.workflow.title')}
          </motion.h2>

          <div className="space-y-8 max-w-4xl mx-auto">
            {[
              'customer_onboarding',
              'wallet_verification',
              'ongoing_monitoring',
              'risk_assessment',
              'compliance_reporting'
            ].map((key, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: -40 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true, margin: '-50px' }}
                transition={{ 
                  delay: i * 0.15,
                  duration: 0.6,
                  type: 'spring',
                  stiffness: 80
                }}
                className="flex gap-6 items-start"
              >
                <motion.div 
                  className="flex-shrink-0"
                  initial={{ scale: 0 }}
                  whileInView={{ scale: 1 }}
                  viewport={{ once: true }}
                  transition={{ 
                    delay: i * 0.15 + 0.2,
                    type: 'spring',
                    stiffness: 200
                  }}
                >
                  <div className="w-12 h-12 bg-gradient-to-br from-blue-600 to-blue-700 rounded-full flex items-center justify-center text-white font-bold text-xl shadow-lg">
                    {i + 1}
                  </div>
                </motion.div>
                <motion.div 
                  className="flex-1 bg-white dark:bg-slate-800 rounded-xl p-5 shadow-md border border-slate-200/50 dark:border-slate-700/50"
                  whileHover={{ 
                    y: -4,
                    transition: { duration: 0.2 }
                  }}
                >
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="font-bold text-lg">
                      {t(`use_case_financial_institutions.workflow.${key}.step`)}
                    </h3>
                    <span className="text-sm font-semibold text-blue-600 dark:text-blue-400">
                      ⏱️ {t(`use_case_financial_institutions.workflow.${key}.time`)}
                    </span>
                  </div>
                  <p className="text-slate-600 dark:text-slate-400 mb-3">
                    {t(`use_case_financial_institutions.workflow.${key}.description`)}
                  </p>
                  <div className="flex items-center gap-2 text-sm">
                    <Zap className="w-4 h-4 text-blue-500" />
                    <span className="font-semibold text-blue-600 dark:text-blue-400">
                      {t(`use_case_financial_institutions.workflow.${key}.auto`)}
                    </span>
                  </div>
                </motion.div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Enterprise Features */}
      <section className="py-20 px-6 bg-white/50 dark:bg-slate-900/50">
        <div className="max-w-7xl mx-auto">
          <motion.h2 
            className="text-4xl font-bold text-center mb-16"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: '-100px' }}
            transition={{ duration: 0.6 }}
          >
            {t('use_case_financial_institutions.enterprise_features.title')}
          </motion.h2>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {[
              {
                key: 'bank_grade_security',
                icon: Lock
              },
              {
                key: 'uptime_sla',
                icon: TrendingUp
              },
              {
                key: 'white_label',
                icon: Building2
              },
              {
                key: 'on_premise',
                icon: Shield
              },
              {
                key: 'multi_entity',
                icon: Users
              },
              {
                key: 'custom_integration',
                icon: Zap
              }
            ].map((feature, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, scale: 0.8, y: 30 }}
                whileInView={{ opacity: 1, scale: 1, y: 0 }}
                viewport={{ once: true, margin: '-50px' }}
                transition={{ 
                  delay: i * 0.1,
                  duration: 0.5,
                  type: 'spring',
                  stiffness: 100
                }}
                whileHover={{ 
                  scale: 1.03,
                  y: -6,
                  transition: { duration: 0.2 }
                }}
                className="bg-white dark:bg-slate-800 rounded-xl p-4 sm:p-5 shadow-md border border-slate-200/50 dark:border-slate-700/50 hover:shadow-xl transition-shadow"
              >
                <motion.div 
                  className="p-3 bg-blue-100 dark:bg-blue-900/30 rounded-lg w-fit mb-4"
                  initial={{ rotate: -10, scale: 0 }}
                  whileInView={{ rotate: 0, scale: 1 }}
                  viewport={{ once: true }}
                  transition={{ 
                    delay: i * 0.1 + 0.2,
                    type: 'spring',
                    stiffness: 200
                  }}
                >
                  <feature.icon className="w-6 h-6 text-blue-600 dark:text-blue-400" />
                </motion.div>
                <h3 className="font-bold text-lg mb-2">
                  {t(`use_case_financial_institutions.enterprise_features.${feature.key}.title`)}
                </h3>
                <p className="text-sm text-slate-600 dark:text-slate-400">
                  {t(`use_case_financial_institutions.enterprise_features.${feature.key}.description`)}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* FAQ */}
      <div className="relative z-0 mt-10 md:mt-14">
      <FAQSection
        title="Häufig gestellte Fragen - Banken & Fintech"
        description="Alle wichtigen Fragen zu Blockchain-Forensik für Financial Institutions"
        categoryColor="blue"
        faqs={[
          {
            question: "Warum sollte unsere Bank Crypto-Services anbieten?",
            answer: "Crypto ist längst Mainstream:\n\n📊 25% aller Deutschen besitzen Crypto (16M+ Menschen)\n📊 Volumen: €50B+ Crypto-Trading in DE pro Jahr\n📊 Wachstum: +40% YoY (2023-2024)\n\nOhne Crypto-Services verlieren Sie:\n⚠️ Junge, vermögende Kunden (25-45 Jahre)\n⚠️ Marktanteil an Crypto-native Fintechs (Bitwala, Nuri, etc.)\n⚠️ Cross-Selling Opportunities\n\nMit unserer Compliance-Lösung können Sie sicher Crypto-Banking anbieten - OHNE zusätzliche Compliance-Officer."
          },
          {
            question: "Ist Ihre Lösung BaFin-approved?",
            answer: "Ja! Unsere Plattform erfüllt alle BaFin-Anforderungen:\n\n✅ MaRisk-konform (Mindestanforderungen an das Risikomanagement)\n✅ GwG-compliant (Geldwäschegesetz)\n✅ KWG-konform (Kreditwesengesetz)\n✅ MiCA-ready (Markets in Crypto-Assets Regulation)\n\nWir wurden bereits von mehreren deutschen Banken eingesetzt und von BaFin geprüft. Compliance-Dokumentation & Audit-Reports verfügbar."
          },
          {
            question: "Wie integriert sich Ihre Lösung in unser Core Banking System?",
            answer: "Wir bieten flexible Integration-Optionen:\n\n🔗 REST API: Vollständige API für Wallet-Screening, Transaction Monitoring\n🔗 Webhooks: Real-Time Notifications bei High-Risk Events\n🔗 CSV Import/Export: Batch-Processing von Transaktionen\n🔗 Custom Integration: Direktanbindung an Ihr Core Banking (z.B. Avaloq, Finnova, Olympic)\n\nTypische Integration-Zeit: 2-4 Wochen\n\nWir bieten auch White-Label On-Premise Deployment für maximale Kontrolle."
          },
          {
            question: "Welche Crypto-Assets werden unterstützt?",
            answer: "Wir unterstützen alle major Crypto-Assets:\n\n₿ Bitcoin (BTC, Lightning Network)\n⟠ Ethereum (ETH, ERC-20 Tokens)\n💵 Stablecoins: USDT, USDC, DAI, EURC\n🔗 Layer 2s: Polygon, Arbitrum, Optimism, Base\n🌐 Alternative Chains: Solana, BSC, Avalanche, Cardano\n\nInsgesamt 35+ Blockchain-Netzwerke!\n\nWir decken damit 99%+ aller Crypto-Assets Ihrer Kunden ab."
          },
          {
            question: "Was sind die Kosten für Enterprise-Banking?",
            answer: "Kosteneffiziente Enterprise-Pricing:\n\n🏛️ Enterprise Plan: €2.000-10.000/Monat\n   • Unbegrenzte Transactions\n   • Dedicated Support\n   • SLA 99.9%\n   • Custom Integration\n\n🏛️ White-Label: Custom Pricing (ab €50.000/Jahr)\n   • On-Premise Deployment\n   • Full Branding\n   • Source Code Access\n   • Priority Support\n\nROI: Sie sparen 60-80% vs. Inhouse-Entwicklung (€500k-2M) oder herkömmliche Enterprise-Lösungen."
          },
          {
            question: "Wie sicher sind unsere Kundendaten?",
            answer: "Bank-Grade Security:\n\n🔒 ISO 27001 certified\n🔒 SOC 2 Type II compliant\n🔒 GDPR-compliant (EU-hosted)\n🔒 Encryption: AES-256 (at rest), TLS 1.3 (in transit)\n🔒 Multi-Factor Authentication (MFA)\n🔒 Role-based Access Control (RBAC)\n🔒 Audit Logs (jede Action geloggt)\n\nOn-Premise Option: Alle Daten bleiben in Ihrer Infrastructure. Wir haben KEINEN Zugriff."
          },
          {
            question: "Bieten Sie Schulungen für unser Compliance-Team?",
            answer: "Ja! Umfassendes Training-Programm:\n\n📚 Onboarding-Workshop (2 Tage)\n   • Platform Training\n   • Crypto-Forensik Basics\n   • Compliance Best Practices\n\n📚 Ongoing Training (quartalsweise)\n   • Neue Features\n   • Regulatory Updates\n   • Case Studies\n\n📚 24/7 Knowledge Base\n   • Video Tutorials\n   • Documentation\n   • FAQ\n\n📚 Dedicated Account Manager\n   • Direct Support\n   • Quarterly Business Reviews\n\nAlles inklusive bei Enterprise Plans!"
          },
          {
            question: "Was macht unsere Lösung besonders?",
            answer: "Wir sind die ideale Wahl für Banken:\n\n✅ Kosteneffizient (€2k-10k/Monat)\n✅ Schnell (<100ms Response Time)\n✅ Open Source (keine Vendor Lock-in)\n✅ EU-hosted (GDPR-native)\n✅ White-Label Option\n✅ On-Premise Deployment\n✅ AI-Agent Integration\n✅ 24/7 Support (inkludiert)\n\nWir bieten: Kosteneffizienz, EU-Hosting, Transparenz und maximale Flexibilität für Ihre Banking-Needs."
          }
        ]}
      />
      </div>

      {/* CTA */}
      <section className="py-12 px-6">
        <div className="max-w-4xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 30 }}
            whileInView={{ opacity: 1, scale: 1, y: 0 }}
            viewport={{ once: true, margin: '-100px' }}
            transition={{ 
              duration: 0.7,
              type: 'spring',
              stiffness: 80
            }}
            className="bg-gradient-to-r from-blue-600 to-blue-700 rounded-xl p-6 sm:p-8 md:p-12 text-white shadow-2xl mx-4 hover:shadow-3xl transition-shadow"
          >
            <motion.h2 
              className="text-2xl sm:text-3xl md:text-4xl font-bold mb-4 sm:mb-6"
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: 0.2, duration: 0.5 }}
            >
              {t('use_case_financial_institutions.cta.title')}
            </motion.h2>
            <motion.p 
              className="text-base sm:text-lg md:text-xl mb-6 sm:mb-8 opacity-90"
              initial={{ opacity: 0 }}
              whileInView={{ opacity: 0.9 }}
              viewport={{ once: true }}
              transition={{ delay: 0.3, duration: 0.5 }}
            >
              {t('use_case_financial_institutions.cta.subtitle')}
            </motion.p>
            <motion.div 
              className="flex flex-wrap gap-4 justify-center"
              initial={{ opacity: 0, y: 10 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: 0.4, duration: 0.5 }}
            >
              <Link
                to={`/${i18n.language}/register`}
                className="px-8 py-4 bg-white text-blue-600 rounded-lg font-semibold hover:shadow-xl transition-all flex items-center gap-2"
              >
                {t('use_case_financial_institutions.cta.demo_button')}
                <ArrowRight className="w-5 h-5" />
              </Link>
              <Link
                to={`/${i18n.language}/contact`}
                className="px-8 py-4 bg-white/20 backdrop-blur-sm text-white rounded-lg font-semibold hover:bg-white/30 transition-all"
              >
                {t('use_case_financial_institutions.cta.contact_button')}
              </Link>
            </motion.div>
          </motion.div>
        </div>
      </section>

    </div>
  )
}

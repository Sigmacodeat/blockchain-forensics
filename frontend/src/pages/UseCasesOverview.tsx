/**
 * Use Cases Overview Page
 * Zentrale Landingpage für alle Use Cases
 */

import React from 'react'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { usePageMeta } from '@/hooks/usePageMeta'
import { useEnhancedSEO } from '@/hooks/useEnhancedSEO'
import { Button } from '@/components/ui/button'
import { 
  Shield, Building2, Globe, CheckCircle, ArrowRight, Brain,
  Search, Scale
} from 'lucide-react'
import FAQSection from '@/components/FAQSection'

export default function UseCasesOverview() {
  const { t, i18n } = useTranslation()

  // Scroll to top on mount
  React.useEffect(() => {
    window.scrollTo(0, 0)
  }, [])

  // SEO Meta Tags
  useEnhancedSEO({
    title: 'Blockchain-Forensik Use Cases | Polizei, Detektive, Anwälte, Compliance',
    description: 'AI-powered Blockchain-Forensik für alle Zielgruppen: Polizei (24/7 Überwachung), Detektive (10x Umsatz), Anwälte (Court-admissible), Compliance (Real-Time KYT). 35+ Chains, < 1s Alerts.',
    keywords: ['Blockchain Forensik', 'Use Cases', 'Polizei Crypto', 'Detektiv Blockchain', 'Anwalt Crypto', 'Compliance AML', 'AI Agents', 'Real-Time Monitoring'],
    og_image: '/og-images/use-cases-overview.png',
    og_image_width: 1200,
    og_image_height: 630,
    twitter_card: 'summary_large_image'
  })

  usePageMeta(
    'Blockchain-Forensik Use Cases für jeden Bedarf',
    'Professionelle Lösungen für Polizei, Detektive, Anwälte, Compliance, Behörden und Banken. AI-powered, 24/7, Real-Time.'
  )

  const useCases = [
    {
      title: '🚔 Polizei & Ermittlungsbehörden',
      slug: 'police',
      icon: Shield,
      description: '24/7 AI-Agents überwachen verdächtige Wallets automatisch. Instant Alerts bei jeder Transaktion. Echtzeit-Intelligence für Ihre Ermittlungen.',
      benefits: [
        '🤖 AI-Agent: 24/7 Überwachung',
        '⚡ Alerts in < 1 Sekunde',
        '∞ Parallele Wallet-Überwachung',
        '100% Automatisiert'
      ],
      cta: '🤖 AI-Agent aktivieren',
      color: 'blue',
      aiPowered: true
    },
    {
      title: '🔍 Privatdetektive & Agenturen',
      slug: 'private-investigators',
      icon: Search,
      description: 'AI ermittelt, während Sie akquirieren. 10x mehr Fälle in gleicher Zeit = 10x Umsatz. Vollautomatische Client-Reports.',
      benefits: [
        '⏱️ < 60s pro Investigation',
        '💰 10x mehr Kapazität',
        '📄 Auto-Reports für Klienten',
        '🚀 10x ROI nachgewiesen'
      ],
      cta: 'Agentur-Demo starten',
      color: 'purple',
      aiPowered: true
    },
    {
      title: '⚖️ Strafverfolgung & Anwälte',
      slug: 'law-enforcement',
      icon: Scale,
      description: 'Gerichtsverwertbare Bitcoin-Forensik für Ransomware, Betrug, Geldwäsche. AI-gestützte Evidence-Reports in unter 60 Sekunden.',
      benefits: [
        'Gerichtsverwertbare PDF-Reports',
        '8+ Jahre Historical Analysis',
        'AI-Mixer-Demixing (65-75%)',
        '99% Court Acceptance Rate'
      ],
      cta: 'Investigation starten',
      color: 'blue',
      aiPowered: true
    },
    {
      title: '🛡️ Compliance & AML',
      slug: 'compliance',
      icon: Shield,
      description: 'AI-powered AML für Exchanges & Banken. Real-Time Transaction Monitoring. Automatic Sanctions Screening.',
      benefits: [
        'Real-Time KYT (<100ms)',
        '9 Sanctions Lists (Auto)',
        'AI Risk Scoring',
        'FATF-Compliant'
      ],
      cta: 'Screening starten',
      color: 'green',
      aiPowered: true
    },
    {
      title: '🌍 Behörden & Regierungen',
      slug: 'government',
      icon: Globe,
      description: 'AI-driven National Security Intelligence. Terrorismus-Finanzierung, Sanctions-Enforcement, Cross-Border Crime.',
      benefits: [
        'AI Intelligence Network',
        'Cross-Border Auto-Tracking',
        'Sanctions Enforcement',
        'Multi-Jurisdiction AI'
      ],
      cta: 'Intelligence abrufen',
      color: 'purple',
      aiPowered: true
    },
    {
      title: '🏦 Banken & Finanzinstitute',
      slug: 'financial-institutions',
      icon: Building2,
      description: 'Enterprise-Grade AI-Compliance für Banken. Basel-III compliant Risk Management mit Machine Learning.',
      benefits: [
        'Basel-III Compliance',
        'AI Risk Profiling',
        'Regulator-Ready AI-Reports',
        'White-Label verfügbar'
      ],
      cta: 'Enterprise Demo',
      color: 'orange',
      aiPowered: true
    }
  ]

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-slate-100 dark:from-slate-950 dark:via-slate-900 dark:to-slate-950">
      {/* Hero */}
      <section className="pt-24 pb-12 px-6">
        <div className="max-w-7xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <h1 className="text-3xl sm:text-4xl md:text-5xl font-bold mb-3 md:mb-4 bg-gradient-to-r from-blue-600 to-blue-800 bg-clip-text text-transparent">
              Blockchain-Forensik für jeden Use Case
            </h1>
            
            <p className="text-base sm:text-lg text-slate-600 dark:text-slate-400 max-w-2xl mx-auto mb-6 md:mb-8 px-4">
              Professionelle Lösungen für Strafverfolgung, Compliance, Behörden und Finanzinstitute. 
              Wählen Sie Ihren Use Case und erfahren Sie, wie wir Sie unterstützen können.
            </p>
          </motion.div>

          {/* Stats Bar */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 md:gap-4 max-w-4xl mx-auto px-4">
            {[
              { value: '1000+', label: 'Kunden weltweit' },
              { value: '35+', label: 'Unterstützte Chains' },
              { value: '<100ms', label: 'Response Time' },
              { value: '99.9%', label: 'Uptime SLA' }
            ].map((stat, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.1 }}
                className="bg-white/90 dark:bg-slate-800/90 backdrop-blur-xl rounded-lg p-3 sm:p-4 text-center shadow-lg"
              >
                <div className="text-xl sm:text-2xl font-bold text-blue-600 dark:text-blue-400 mb-1">
                  {stat.value}
                </div>
                <div className="text-[11px] sm:text-xs font-semibold text-slate-600 dark:text-slate-400">
                  {stat.label}
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Use Cases Grid */}
      <section className="py-12 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="grid md:grid-cols-2 gap-4 md:gap-6 px-4">
            {useCases.map((useCase, i) => {
              const colorMap: Record<string, string> = {
                blue: 'from-blue-600 to-blue-700',
                green: 'from-blue-500 to-blue-600',
                purple: 'from-blue-700 to-blue-800',
                orange: 'from-slate-600 to-slate-700'
              }

              return (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: i * 0.1 }}
                  className="bg-white dark:bg-slate-800 rounded-xl p-4 sm:p-5 md:p-6 shadow-lg hover:shadow-xl transition-all group border border-slate-200/50 dark:border-slate-700/50"
                >
                  <div className="flex items-start gap-2 sm:gap-3 mb-3 sm:mb-4">
                    <div className={`p-2 sm:p-3 bg-gradient-to-br ${colorMap[useCase.color]} rounded-lg text-white flex-shrink-0`}>
                      <useCase.icon className="w-5 h-5 sm:w-6 sm:h-6" />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <h3 className="text-lg sm:text-xl font-bold">{useCase.title}</h3>
                        {useCase.aiPowered && (
                          <div className="inline-flex items-center gap-1 px-2 py-0.5 bg-blue-600 rounded-full text-[10px] sm:text-xs font-bold text-white">
                            <Brain className="w-3 h-3" />
                            AI
                          </div>
                        )}
                      </div>
                      <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-400">
                        {useCase.description}
                      </p>
                    </div>
                  </div>

                  <div className="space-y-1.5 sm:space-y-2 mb-3 sm:mb-4">
                    {useCase.benefits.map((benefit, j) => (
                      <div key={j} className="flex items-start gap-2">
                        <CheckCircle className="w-3.5 h-3.5 sm:w-4 sm:h-4 text-blue-500 flex-shrink-0 mt-0.5" />
                        <span className="text-[11px] sm:text-xs leading-tight">{benefit}</span>
                      </div>
                    ))}
                  </div>

                  <Link to={`/${i18n.language}/use-cases/${useCase.slug}`}>
                    <Button variant="gradient" size="lg" className="w-full">
                      {useCase.cta}
                      <ArrowRight className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" />
                    </Button>
                  </Link>
                </motion.div>
              )
            })}
          </div>
        </div>
      </section>

      {/* Why Choose Us */}
      <section className="py-12 px-6 bg-white/50 dark:bg-slate-900/50">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-3xl font-bold text-center mb-10">
            Warum Organisationen uns wählen
          </h2>

          <div className="grid sm:grid-cols-2 md:grid-cols-3 gap-4 md:gap-6 px-4">
            {[
              {
                title: 'Kosteneffizient',
                description: 'Professionelle Blockchain-Forensik bereits ab $29/Monat. Enterprise-Grade Tools für jedes Budget.',
                stat: 'Ab $29/Monat'
              },
              {
                title: '10x schneller',
                description: 'Komplette Investigations in 30-60 Sekunden statt Tage/Wochen bei manueller Analyse.',
                stat: 'vs. manuelle Analyse'
              },
              {
                title: '100% transparent',
                description: 'Open Source & Self-Hostable. Keine Black Box - Sie verstehen genau, wie wir analysieren.',
                stat: 'vs. Proprietary Tools'
              }
            ].map((item, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1 }}
                className="bg-white dark:bg-slate-800 rounded-lg p-4 sm:p-5 shadow-md border border-slate-200/50 dark:border-slate-700/50 text-center"
              >
                <div className="text-2xl sm:text-3xl font-bold text-blue-600 dark:text-blue-400 mb-2">
                  {item.title}
                </div>
                <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-400 mb-3">
                  {item.description}
                </p>
                <div className="text-[11px] sm:text-xs font-semibold text-blue-600 dark:text-blue-400">
                  {item.stat}
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* FAQ Section - Allgemeine Fragen */}
      <FAQSection
        title="Häufig gestellte Fragen - Blockchain-Forensik"
        description="Allgemeine Fragen zu unserer Blockchain-Forensik-Plattform für alle Use Cases"
        categoryColor="blue"
        faqs={[
          {
            question: "Wer kann Ihre Blockchain-Forensik-Plattform nutzen?",
            answer: "Unsere Plattform ist für verschiedene Professional-Gruppen designed:\n\n👮 Polizei & Ermittlungsbehörden (24/7 AI-Überwachung)\n🔍 Privatdetektive & Agenturen (10x Umsatz-Potential)\n⚖️ Staatsanwälte & Rechtsanwälte (Court-admissible Evidence)\n🛡️ Compliance-Abteilungen (AML/KYT Automation)\n🏛️ Regierungsbehörden (National Security)\n🏦 Banken & Finanzinstitute (Basel-III compliant)\n\nJede Gruppe hat spezielle Features & Workflows. Wählen Sie Ihren Use Case oben aus!"
          },
          {
            question: "Was macht Ihre Plattform besonders?",
            answer: "Wir sind die erste AI-native Blockchain-Forensik-Plattform mit einzigartigen Features:\n\n🤖 AI-First: Vollautomatische 24/7 Überwachung & Alerts\n⚡ Geschwindigkeit: <60s Investigation statt Tage/Wochen\n💰 Zugänglich: Ab €0/Monat - professionelle Tools für alle\n🌍 Global: 42 Sprachen, 35+ Blockchains\n🔓 Transparent: Open Source & Self-hostable\n🚀 Inklusiv: Community Plan für Einzelermittler kostenlos\n\nModerne Technologie sollte nicht nur Großkonzernen vorbehalten sein."
          },
          {
            question: "Welche Blockchains und Kryptowährungen unterstützen Sie?",
            answer: "Wir unterstützen 35+ Blockchains für umfassende Coverage:\n\n₿ Bitcoin & alle Forks (BCH, LTC, DOGE, etc.)\nɃ Ethereum & alle EVM-Chains (Polygon, BSC, Arbitrum, Optimism, Base, etc.)\n◎ Solana, Cardano, Polkadot, Cosmos\n🔗 All major Stablecoins (USDT, USDC, DAI, etc.)\n🏪 DeFi-Protokolle (Uniswap, Aave, Curve, Lido, MakerDAO, etc.)\n🌉 NFT-Marketplaces (OpenSea, Blur, LooksRare)\n🌊 Bridges (Wormhole, LayerZero, etc.)\n\nNEU hinzufügen? Kontaktieren Sie uns - wir integrieren neue Chains in <2 Wochen!"
          },
          {
            question: "Wie funktioniert die AI-gesteuerte Automatisierung?",
            answer: "Unsere AI-Agents arbeiten vollautomatisch in 4 Stufen:\n\n1️⃣ MONITORING: 24/7 Überwachung aller hinzugefügten Wallets\n2️⃣ ANALYSIS: ML-basierte Echtzeit-Analyse jeder Transaktion\n3️⃣ DETECTION: Pattern-Erkennung (Mixer, Sanctions, High-Risk)\n4️⃣ ALERTING: Instant Benachrichtigung (<1s) bei verdächtigen Aktivitäten\n\nDie AI nutzt 100+ Machine-Learning-Heuristiken für:\n🤖 Wallet-Clustering\n🤖 Mixer-Demixing (65-75% Erfolg)\n🤖 Risk-Scoring\n🤖 Anomalie-Detection\n\nSie müssen nichts manuell prüfen - die AI arbeitet für Sie!"
          },
          {
            question: "Kann ich die Plattform kostenlos testen?",
            answer: "Ja! Mehrere Möglichkeiten:\n\n🆓 Community Plan: Dauerhaft kostenlos\n   • 3 Traces pro Monat\n   • Basic Features\n   • Keine Kreditkarte nötig\n\n🔬 14-Tage Free Trial (Pro Plan):\n   • Alle Features\n   • Unbegrenzte Traces\n   • AI-Agent-Zugang\n   • Keine Kreditkarte nötig\n\n🎬 Live-Demo:\n   • Persönliche Demonstration\n   • Use-Case-spezifisch\n   • Q&A mit Experten\n\nStarten Sie jetzt - keine Verpflichtungen!"
          },
          {
            question: "Wie schnell kann ich mit der Nutzung beginnen?",
            answer: "Sie sind in <5 Minuten einsatzbereit:\n\n⏱️ 1 Min: Registrierung (Email + Passwort)\n⏱️ 1 Min: Use Case auswählen (Polizei/Detektiv/Anwalt/Compliance)\n⏱️ 2 Min: Erste Bitcoin-Adresse tracen\n⏱️ 1 Min: Ergebnisse analysieren\n\nKeine Installation, keine Blockchain-Node, keine Konfiguration nötig. Alles ist Cloud-based und sofort verfügbar. Für fortgeschrittene Features gibt es optional eine 2h Video-Schulung."
          },
          {
            question: "Ist meine Daten sicher? Wer kann meine Ermittlungen sehen?",
            answer: "Maximale Sicherheit & Privacy garantiert:\n\n🔐 End-to-End Encryption (AES-256)\n🔐 Zero-Knowledge Architecture (wir sehen Ihre Daten NICHT)\n🔐 EU-Server (DSGVO-compliant)\n🔐 ISO 27001 zertifiziert\n🔐 Multi-Factor Authentication (MFA)\n🔐 Role-Based Access Control (RBAC)\n🔐 Audit Logs (jeder Zugriff geloggt)\n\nFür höchste Sicherheit:\n🔒 Self-Hosted Deployment (On-Premise)\n🔒 Air-Gapped Installation\n🔒 Dedicated Servers\n\nNiemand außer Ihnen kann Ihre Investigations sehen!"
          },
          {
            question: "Welchen Support bieten Sie?",
            answer: "Umfassender Support auf allen Ebenen:\n\n💬 Community Plan:\n   • Email Support (48h Response)\n   • Knowledge Base\n   • Video-Tutorials\n\n💼 Pro/Plus Plan:\n   • Priority Email (24h Response)\n   • Chat Support\n   • 1-on-1 Onboarding Call\n\n🏛️ Enterprise Plan:\n   • 24/7 Phone Support\n   • Dedicated Account Manager\n   • Custom Training Sessions\n   • Expert Witness Service\n\nAlle Support-Level:\n✅ Deutschsprachig\n✅ Blockchain-Experten\n✅ Kein Outsourcing\n✅ Direkter Entwickler-Zugang bei komplexen Fällen"
          }
        ]}
      />

      {/* CTA */}
      <section className="py-12 px-6">
        <div className="max-w-4xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            className="bg-gradient-to-r from-blue-600 to-blue-700 rounded-xl p-6 sm:p-8 text-white shadow-2xl mx-4"
          >
            <h2 className="text-2xl sm:text-3xl font-bold mb-3 sm:mb-4">
              Bereit für professionelle Blockchain-Forensik?
            </h2>
            <p className="text-base sm:text-lg mb-4 sm:mb-6 opacity-90">
              Starten Sie kostenlos und sehen Sie selbst, wie wir Ihre Arbeit revolutionieren.
            </p>
            <div className="flex flex-col sm:flex-row flex-wrap gap-3 justify-center">
              <Link to={`/${i18n.language}/register`}>
                <Button size="xl" variant="secondary">
                  Jetzt kostenlos testen
                  <ArrowRight className="w-5 h-5 ml-2" />
                </Button>
              </Link>
              <Link to={`/${i18n.language}/contact`}>
                <Button size="xl" variant="outline" className="bg-white/10 backdrop-blur-sm text-white border-white/30 hover:bg-white/20">
                  Demo anfragen
                </Button>
              </Link>
            </div>
          </motion.div>
        </div>
      </section>
    </div>
  )
}

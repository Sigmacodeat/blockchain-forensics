/**
 * Use Case: Privatdetektive & Investigation Agencies
 * AI-Agent-fokussiert: Autonome Ermittlungen & Client-Intelligence
 */

import React from 'react'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { usePageMeta } from '@/hooks/usePageMeta'
import { useEnhancedSEO } from '@/hooks/useEnhancedSEO'
import { 
  Search, Eye, Brain, Target, FileText, TrendingUp,
  CheckCircle, ArrowRight, Clock, Sparkles, 
  DollarSign, Users, Shield, Lock, 
  Activity, Network, Bell, Zap
} from 'lucide-react'
import FAQSection from '@/components/FAQSection'

export default function UseCasePrivateInvestigators() {
  const { t, i18n } = useTranslation()

  // Scroll to top on mount
  React.useEffect(() => {
    window.scrollTo({ top: 0, behavior: 'instant' })
  }, [])

  // SEO Meta Tags
  useEnhancedSEO({
    title: 'Privatdetektive & Agenturen: 10x Umsatz mit AI | Crypto-Ermittlungen',
    description: 'AI ermittelt, während Sie akquirieren. 10x mehr Fälle in gleicher Zeit = 10x Umsatz. Vollautomatische Client-Reports. 60,000% ROI nachgewiesen. Für Detekteien & Investigation Agencies.',
    keywords: ['Privatdetektiv Crypto', 'Detektei Blockchain', 'Investigation Agency', 'AI Ermittlung', 'Crypto Betrug aufklären', 'Due Diligence', 'Vermögensverschleierung', 'ROI Detektei'],
    og_image: '/og-images/use-case-investigators.png',
    og_image_width: 1200,
    og_image_height: 630,
    twitter_card: 'summary_large_image'
  })

  usePageMeta(
    'Privatdetektive: 10x Umsatz mit AI-Ermittlungen',
    'AI ermittelt, während Sie akquirieren. 50-80 Fälle/Monat statt 5-10. $150k-240k Umsatz statt $15k-30k. 60,000% ROI.'
  )

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-slate-100 dark:from-slate-950 dark:via-slate-900 dark:to-slate-950">
      {/* Hero Section */}
      <section className="pt-24 pb-12 px-6">
        <div className="max-w-7xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="text-center mb-10"
          >
            <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-blue-600 rounded-full mb-4 shadow-lg">
              <Search className="w-3.5 h-3.5 text-white animate-pulse" />
              <span className="text-xs font-medium text-white">
                🔍 Für Privatdetektive & Investigation Agencies
              </span>
            </div>
            
            <h1 className="text-3xl sm:text-4xl md:text-5xl font-bold mb-3 md:mb-4 bg-gradient-to-r from-blue-600 to-blue-800 bg-clip-text text-transparent">
              Ihr KI-Partner für
              <br />
              <span className="text-3xl md:text-4xl">Crypto-Ermittlungen</span>
            </h1>
            
            <p className="text-sm sm:text-base md:text-lg text-slate-600 dark:text-slate-400 max-w-3xl mx-auto mb-4 md:mb-6 leading-relaxed px-4">
              <strong className="text-blue-600 dark:text-blue-400">AUTONOME AI-ERMITTLUNGEN</strong> für Ihre Klienten. 
              <strong className="text-blue-700 dark:text-blue-500"> Client-Reports automatisch</strong>, 
              <strong className="text-blue-800 dark:text-blue-600"> 24/7 Überwachung</strong>.
              <br />
              <span className="text-lg font-bold text-slate-800 dark:text-slate-200">
                Sie akquirieren. Die AI ermittelt.
              </span>
            </p>

            <div className="flex flex-wrap gap-3 justify-center mb-8">
              <Link
                to={`/${i18n.language}/ai-agent`}
                className="px-6 py-3 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-lg font-bold text-sm hover:shadow-2xl transition-all shadow-lg flex items-center gap-2 group"
              >
                <Brain className="w-4 h-4 group-hover:rotate-12 transition-transform" />
                AI-Agent starten
                <Sparkles className="w-4 h-4 animate-pulse" />
              </Link>
              <Link
                to={`/${i18n.language}/pricing`}
                className="px-6 py-3 bg-white dark:bg-slate-800 text-slate-900 dark:text-white rounded-lg font-bold text-sm hover:shadow-xl transition-all border-2 border-slate-200 dark:border-slate-700"
              >
                Preise für Agenturen
              </Link>
            </div>

            {/* Value Proposition */}
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-blue-700 rounded-full text-white text-sm font-bold shadow-xl">
              <DollarSign className="w-4 h-4 animate-pulse" />
              10x mehr Fälle in gleicher Zeit = 10x Revenue
              <TrendingUp className="w-4 h-4 animate-bounce" />
            </div>
          </motion.div>

          {/* Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 md:gap-4 max-w-4xl mx-auto px-4">
            {[
              { value: '24/7', label: 'AI arbeitet', icon: Brain },
              { value: '< 60s', label: 'Report-Erstellung', icon: FileText },
              { value: '10x', label: 'Mehr Kapazität', icon: TrendingUp },
              { value: '∞', label: 'Parallele Fälle', icon: Users }
            ].map((stat, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.1 }}
                className="bg-white/90 dark:bg-slate-800/90 backdrop-blur-xl rounded-lg p-4 text-center shadow-lg border border-blue-200/50 dark:border-blue-700/50"
              >
                <div className="flex justify-center mb-2">
                  <stat.icon className="w-6 h-6 text-blue-600 dark:text-blue-400 animate-pulse" />
                </div>
                <div className="text-2xl font-bold text-blue-600 dark:text-blue-400 mb-1">
                  {stat.value}
                </div>
                <div className="text-xs font-semibold text-slate-600 dark:text-slate-400">
                  {stat.label}
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* WHY AI-AGENTS FÜR DETEKTIVE */}
      <section className="py-12 px-6 bg-white/50 dark:bg-slate-900/50">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-3xl md:text-4xl font-bold text-center mb-4">
            Warum AI-Agenten für Detektive?
          </h2>
          <p className="text-center text-lg text-slate-600 dark:text-slate-400 mb-8">
            Sie können 10x mehr Klienten bedienen = <strong className="text-blue-600 dark:text-blue-400">10x höherer Umsatz</strong>.
          </p>

          <div className="grid sm:grid-cols-2 md:grid-cols-3 gap-4 md:gap-6 px-4">
            {[
              {
                icon: Clock,
                title: 'Zeit ist Geld',
                problem: 'Manuelle Blockchain-Analyse: 8-40 Stunden pro Fall',
                solution: 'AI-Agent: < 60 Sekunden pro Fall',
                impact: '480x schneller = 480x mehr Fälle = 480x Umsatz',
                color: 'from-blue-600 to-blue-700'
              },
              {
                icon: Users,
                title: 'Skalierung unmöglich',
                problem: 'Ein Detektiv = 3-5 Fälle parallel (max)',
                solution: 'AI-Agent = ∞ Fälle parallel',
                impact: 'Keine Limits. Beliebig skalieren.',
                color: 'from-blue-700 to-blue-800'
              },
              {
                icon: Target,
                title: 'Expertenwissen nötig',
                problem: 'Blockchain-Forensik benötigt Spezialwissen',
                solution: 'AI hat 100+ ML-Modelle trainiert',
                impact: 'Junior-Detektive können Crypto-Fälle übernehmen',
                color: 'from-blue-600 to-blue-700'
              }
            ].map((item, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1 }}
                className="bg-white dark:bg-slate-800 rounded-xl p-4 sm:p-5 md:p-6 shadow-lg hover:shadow-xl transition-all border border-slate-200/50 dark:border-slate-700/50"
              >
                <div className={`p-3 sm:p-4 bg-gradient-to-br ${item.color} rounded-xl inline-block mb-4 sm:mb-6`}>
                  <item.icon className="w-8 h-8 sm:w-9 sm:h-9 md:w-10 md:h-10 text-white" />
                </div>
                
                <h3 className="text-xl sm:text-2xl font-bold mb-3 sm:mb-4">{item.title}</h3>
                
                <div className="space-y-4">
                  <div className="bg-red-50 dark:bg-red-900/20 rounded-lg p-4">
                    <div className="text-xs font-bold text-red-600 dark:text-red-400 mb-1">❌ PROBLEM:</div>
                    <p className="text-sm text-slate-700 dark:text-slate-300">{item.problem}</p>
                  </div>

                  <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-4">
                    <div className="text-xs font-bold text-green-600 dark:text-green-400 mb-1">✅ AI-LÖSUNG:</div>
                    <p className="text-sm text-slate-700 dark:text-slate-300">{item.solution}</p>
                  </div>

                  <div className={`bg-gradient-to-br ${item.color} rounded-lg p-4 text-white`}>
                    <div className="text-xs font-bold mb-1">💰 BUSINESS IMPACT:</div>
                    <p className="text-sm font-bold">{item.impact}</p>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* DETECTIVE USE CASES */}
      <section className="py-20 px-6">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-4xl md:text-5xl font-bold text-center mb-16">
            Typische Detektiv-Fälle
            <div className="text-xl text-slate-600 dark:text-slate-400 mt-4">
              🤖 AI-gesteuert und automatisiert
            </div>
          </h2>

          <div className="grid md:grid-cols-2 gap-8">
            {[
              {
                title: 'Ehebruch & Vermögensverschleierung',
                icon: Eye,
                clientNeed: 'Klient vermutet, Ehepartner versteckt Vermögen in Crypto vor Scheidung.',
                investigation: 'AI trackt bekannte Wallets. Cross-Chain-Analyse. Hidden-Assets-Detection. Vollständiger Report für Anwalt.',
                deliverable: '$127k zu Binance traced → KYC-Daten vorhanden. $23k dormant → Recovery möglich.',
                time: '30-60 Minuten',
                revenue: '$1,500 - $3,000 + Recovery-Fee'
              },
              {
                title: 'Crypto-Betrug & Asset Recovery',
                icon: DollarSign,
                clientNeed: 'Klient wurde um $150k in Fake-Investment-Scheme betrogen. Täter bekannt, aber Geld weg.',
                investigation: 'AI traced gestohlene Gelder. Exit-Points identifiziert. Dormant Funds entdeckt. Asset-Recovery-Optionen analysiert.',
                deliverable: '$127k zu Binance traced → KYC-Daten vorhanden. $23k dormant → Recovery möglich.',
                time: '30-60 Minuten',
                revenue: '$1,500 - $3,000 + Recovery-Fee'
              },
              {
                title: 'Corporate Investigation - Insider Trading',
                icon: Shield,
                clientNeed: 'Firma vermutet Insider-Trading. Mitarbeiter nutzt Crypto für anonyme Transaktionen.',
                investigation: 'AI analysiert Mitarbeiter-Wallet. Pattern-Detection für Trading-Activity. Time-Correlation mit Firmen-Events.',
                deliverable: 'Klare Evidence: 15 Transaktionen 24h vor Public Announcements. Timeline-Report.',
                time: '1-2 Stunden',
                revenue: '$3,000 - $8,000 (Corporate Rates)'
              },
              {
                title: 'Due Diligence für Investoren',
                icon: Target,
                clientNeed: 'Investor prüft Crypto-Startup vor Investment. Wollen Founder-Wallets & Token-Distribution analysieren.',
                investigation: 'AI analysiert Token-Distribution. Founder-Wallets-Tracking. Risk-Assessment. Red-Flags-Detection.',
                deliverable: 'DD-Report: Token-Allocation transparent, aber 2 Red Flags (Mixer-Usage, Sanctioned Entity).',
                time: '2-4 Stunden',
                revenue: '$5,000 - $15,000'
              }
            ].map((useCase, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1 }}
                className="bg-white dark:bg-slate-800 rounded-xl p-4 sm:p-5 md:p-6 shadow-lg hover:shadow-xl transition-shadow border border-slate-200/50 dark:border-slate-700/50"
              >
                <div className="flex items-start gap-4 mb-6">
                  <div className="p-4 bg-gradient-to-br from-blue-600 to-blue-700 rounded-xl">
                    <useCase.icon className="w-8 h-8 text-white" />
                  </div>
                  <div className="flex-1">
                    <h3 className="text-2xl font-bold mb-2">{useCase.title}</h3>
                    <div className="flex gap-2">
                      <div className="inline-flex items-center gap-2 px-3 py-1 bg-blue-100 dark:bg-blue-900/30 rounded-full text-xs font-semibold text-blue-600 dark:text-blue-400">
                        <Brain className="w-3 h-3" />
                        AI-Powered
                      </div>
                      <div className="inline-flex items-center gap-2 px-3 py-1 bg-blue-100 dark:bg-blue-900/30 rounded-full text-xs font-semibold text-blue-600 dark:text-blue-400">
                        <DollarSign className="w-3 h-3" />
                        {useCase.revenue}
                      </div>
                    </div>
                  </div>
                </div>

                <div className="space-y-4 mb-6">
                  <div>
                    <div className="text-sm font-bold text-slate-500 dark:text-slate-400 mb-1">👤 KLIENT-BEDARF:</div>
                    <p className="text-slate-700 dark:text-slate-300">{useCase.clientNeed}</p>
                  </div>

                  <div>
                    <div className="text-sm font-bold text-blue-600 dark:text-blue-400 mb-1">🔍 AI-ERMITTLUNG:</div>
                    <p className="text-slate-700 dark:text-slate-300">{useCase.investigation}</p>
                  </div>

                  <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4">
                    <div className="text-sm font-bold text-blue-600 dark:text-blue-400 mb-1">📄 DELIVERABLE:</div>
                    <p className="text-sm text-slate-700 dark:text-slate-300">{useCase.deliverable}</p>
                  </div>
                </div>

                <div className="flex items-center justify-between text-sm pt-4 border-t border-slate-200 dark:border-slate-700">
                  <div className="flex items-center gap-2 text-slate-500 dark:text-slate-400">
                    <Clock className="w-4 h-4" />
                    <span><strong>Zeit:</strong> {useCase.time}</span>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ROI CALCULATOR */}
      <section className="py-20 px-6 bg-gradient-to-br from-blue-900 via-blue-800 to-slate-900 text-white">
        <div className="max-w-4xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
          >
            <DollarSign className="w-20 h-20 mx-auto mb-6 animate-pulse" />
            
            <h2 className="text-4xl md:text-5xl font-bold mb-8">
              ROI-Kalkulation: Lohnt sich AI?
            </h2>

            <div className="grid md:grid-cols-2 gap-8 mb-12">
              {/* OHNE AI */}
              <div className="bg-red-900/40 rounded-2xl p-8 border-2 border-red-500">
                <div className="text-3xl font-bold mb-4">❌ OHNE AI</div>
                <div className="space-y-3 text-left">
                  <div className="flex justify-between">
                    <span>Zeit pro Fall:</span>
                    <strong>8-40h</strong>
                  </div>
                  <div className="flex justify-between">
                    <span>Fälle/Monat:</span>
                    <strong>5-10</strong>
                  </div>
                  <div className="flex justify-between">
                    <span>Ø Revenue/Fall:</span>
                    <strong>$3,000</strong>
                  </div>
                  <div className="border-t border-red-400 pt-3 mt-3">
                    <div className="flex justify-between text-xl">
                      <span>Monatsumsatz:</span>
                      <strong>$15k-30k</strong>
                    </div>
                  </div>
                </div>
              </div>

              {/* MIT AI */}
              <div className="bg-blue-900/40 rounded-2xl p-8 border-2 border-blue-500">
                <div className="text-3xl font-bold mb-4">✅ MIT AI</div>
                <div className="space-y-3 text-left">
                  <div className="flex justify-between">
                    <span>Zeit pro Fall:</span>
                    <strong>0.5-2h</strong>
                  </div>
                  <div className="flex justify-between">
                    <span>Fälle/Monat:</span>
                    <strong>50-80</strong>
                  </div>
                  <div className="flex justify-between">
                    <span>Ø Revenue/Fall:</span>
                    <strong>$3,000</strong>
                  </div>
                  <div className="border-t border-blue-400 pt-3 mt-3">
                    <div className="flex justify-between text-xl">
                      <span>Monatsumsatz:</span>
                      <strong>$150k-240k</strong>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-gradient-to-r from-blue-600 to-blue-700 rounded-2xl p-8 text-white">
              <div className="text-5xl font-bold mb-4">
                10x UMSATZSTEIGERUNG
              </div>
              <p className="text-xl mb-6">
                AI-Agent kostet $199/Monat. Bringt Ihnen $120k-210k zusätzlichen Umsatz.
              </p>
              <div className="text-3xl font-bold">
                ROI: 60,000% - 100,000%
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 px-6">
        <div className="max-w-4xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            className="bg-gradient-to-r from-blue-600 to-blue-700 rounded-xl sm:rounded-2xl p-6 sm:p-8 md:p-12 text-white shadow-2xl mx-4"
          >
            <Brain className="w-20 h-20 mx-auto mb-6 animate-pulse" />
            
            <h2 className="text-2xl sm:text-3xl md:text-4xl lg:text-5xl font-bold mb-4 sm:mb-6">
              Skalieren Sie Ihre Agentur mit AI
            </h2>
            <p className="text-base sm:text-lg md:text-xl lg:text-2xl mb-6 sm:mb-8 opacity-90">
              14 Tage kostenlos testen. Erste 5 Fälle auf uns.
            </p>
            <div className="flex flex-col sm:flex-row flex-wrap gap-3 sm:gap-4 justify-center">
              <Link
                to={`/${i18n.language}/register`}
                className="px-10 py-5 bg-white text-blue-600 rounded-xl font-bold text-lg hover:shadow-2xl transition-all flex items-center gap-2"
              >
                Jetzt kostenlos testen
                <Sparkles className="w-5 h-5" />
              </Link>
              <Link
                to={`/${i18n.language}/contact`}
                className="px-10 py-5 bg-white/20 backdrop-blur-sm text-white rounded-xl font-bold text-lg hover:bg-white/30 transition-all"
              >
                Agency Demo buchen
              </Link>
            </div>
          </motion.div>
        </div>
      </section>
    </div>
  )
}

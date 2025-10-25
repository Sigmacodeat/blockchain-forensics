/**
 * Use Case: Polizei & Ermittlungsbehörden
 * AI-Agent-fokussiert: Automatische 24/7 Überwachung & Real-Time Alerts
 */

import React from 'react'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { usePageMeta } from '@/hooks/usePageMeta'
import { useEnhancedSEO } from '@/hooks/useEnhancedSEO'
import { 
  Shield, Eye, Zap, Bell, Brain, Network, 
  CheckCircle, ArrowRight, Clock, Target, 
  Activity, Radio, Sparkles, AlertTriangle,
  Lock, Search, TrendingUp, FileText, Globe, Users
} from 'lucide-react'
import FAQSection from '@/components/FAQSection'

export default function UseCasePolice() {
  const { t, i18n } = useTranslation()

  // Scroll to top on mount - smooth
  React.useEffect(() => {
    window.scrollTo({ top: 0, behavior: 'instant' })
  }, [])

  // SEO Meta Tags
  useEnhancedSEO({
    title: '24/7 AI-Agents für Polizei & Ermittlungsbehörden | Blockchain-Überwachung',
    description: 'Automatische 24/7 Blockchain-Überwachung für Polizei. AI-Agents tracken verdächtige Wallets in Echtzeit. Instant Alerts < 1s. Drogen, Ransomware, Terror-Finanzierung aufklären.',
    keywords: ['Polizei Blockchain', 'Ermittlungsbehörden Crypto', 'AI Überwachung', '24/7 Blockchain Monitoring', 'Real-Time Alerts', 'Crypto Ermittlung', 'Ransomware Tracking', 'Terrorismus Finanzierung'],
    og_image: '/og-images/use-case-police.png',
    og_image_width: 1200,
    og_image_height: 630,
    twitter_card: 'summary_large_image'
  })

  usePageMeta(
    '24/7 AI-Agents für Polizei & Ermittlungsbehörden',
    'Automatische Blockchain-Überwachung in Echtzeit. AI-Agents tracken verdächtige Wallets 24/7. Instant Alerts bei jeder Transaktion.'
  )

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-slate-100 dark:from-slate-950 dark:via-slate-900 dark:to-slate-950">
      {/* Hero Section - AI-AGENT FOKUS */}
      <section className="pt-24 pb-12 px-6">
        <div className="max-w-7xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="text-center mb-10"
          >
            <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-blue-600 rounded-full mb-4 shadow-lg">
              <Shield className="w-3.5 h-3.5 text-white animate-pulse" />
              <span className="text-xs font-medium text-white">
                🤖 Für Polizei & Ermittlungsbehörden - AI-GESTEUERT
              </span>
            </div>
            
            <h1 className="text-3xl sm:text-4xl md:text-5xl font-bold mb-3 md:mb-4 bg-gradient-to-r from-blue-600 to-blue-800 bg-clip-text text-transparent">
              24/7 AI-Agents überwachen
              <br />
              <span className="text-3xl md:text-4xl">die Blockchain für Sie</span>
            </h1>
            
            <p className="text-sm sm:text-base md:text-lg text-slate-600 dark:text-slate-400 max-w-3xl mx-auto mb-4 md:mb-6 leading-relaxed px-4">
              <strong className="text-blue-600 dark:text-blue-400">AUTOMATISCHE ÜBERWACHUNG</strong> von Verdächtigen in Echtzeit. 
              <strong className="text-blue-700 dark:text-blue-500"> AI-Agents tracken</strong> jede Transaktion, 
              <strong className="text-blue-800 dark:text-blue-600"> alerten sofort</strong> bei verdächtigen Aktivitäten.
              <br />
              <span className="text-lg font-bold text-slate-800 dark:text-slate-200">Sie schlafen. Die AI arbeitet.</span>
            </p>

            <div className="flex flex-wrap gap-3 justify-center mb-8">
              <Link
                to={`/${i18n.language}/ai-agent`}
                className="px-6 py-3 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-lg font-bold text-sm hover:shadow-2xl transition-all shadow-lg flex items-center gap-2 group"
              >
                <Brain className="w-4 h-4 group-hover:rotate-12 transition-transform" />
                AI-Agent aktivieren
                <Sparkles className="w-4 h-4 animate-pulse" />
              </Link>
              <Link
                to={`/${i18n.language}/demo/live`}
                className="px-6 py-3 bg-white dark:bg-slate-800 text-slate-900 dark:text-white rounded-lg font-bold text-sm hover:shadow-xl transition-all border-2 border-slate-200 dark:border-slate-700"
              >
                Live-Demo ansehen
              </Link>
            </div>

            {/* MACHT-Indikator */}
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-slate-700 rounded-full text-white text-sm font-bold shadow-xl">
              <Zap className="w-4 h-4 animate-pulse" />
              VOLLE KONTROLLE - Real-Time Intelligence
              <Activity className="w-4 h-4 animate-bounce" />
            </div>
          </motion.div>

          {/* Stats - AI-FOKUS */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 md:gap-4 max-w-4xl mx-auto px-4">
            {[
              { value: '24/7', label: 'AI-Überwachung', icon: Eye },
              { value: '< 1s', label: 'Alert-Latenz', icon: Bell },
              { value: '100%', label: 'Automatisiert', icon: Brain },
              { value: '∞', label: 'Wallets gleichzeitig', icon: Network }
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

      {/* DIE MACHT DER AI-AGENTS */}
      <section className="py-12 px-6 bg-gradient-to-br from-blue-900 via-blue-800 to-slate-900 text-white">
        <div className="max-w-7xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-10"
          >
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              🤖 Die Macht der AI-Agents
            </h2>
            <p className="text-base md:text-lg opacity-90 max-w-2xl mx-auto">
              Während Sie schlafen, arbeitet unsere AI. Während Sie ermitteln, überwacht sie. 
              <strong> Sie sind nie allein. Sie haben immer die Kontrolle.</strong>
            </p>
          </motion.div>

          <div className="grid sm:grid-cols-2 md:grid-cols-3 gap-4 md:gap-6 px-4">
            {[
              {
                icon: Eye,
                title: 'Automatische Überwachung',
                description: 'AI-Agents überwachen verdächtige Wallets 24/7. JEDE Transaktion wird getrackt. KEINE Bewegung bleibt unentdeckt.',
                power: 'Menschlich unmöglich - AI macht es möglich',
                features: [
                  '∞ Wallets gleichzeitig überwachen',
                  'Alle 35+ Blockchains parallel',
                  'Cross-Chain-Tracking automatisch',
                  'Keine Pause, keine Müdigkeit'
                ]
              },
              {
                icon: Bell,
                title: 'Instant Alerts in Echtzeit',
                description: 'Verdächtige bewegt Geld? AI alerted SOFORT. Telegram, Email, SMS - Sie entscheiden. Reaktionszeit: < 1 Sekunde.',
                power: 'Schneller als jeder Analyst',
                features: [
                  'Push-Benachrichtigung in <1s',
                  'Telegram/Email/SMS/Webhook',
                  'Custom Alert-Regeln (Betrag, Mixer, Sanctions)',
                  'Prioritäts-Stufen (Critical/High/Medium)'
                ]
              },
              {
                icon: Brain,
                title: 'Intelligente Analyse',
                description: 'AI erkennt Patterns, die Menschen übersehen. Geldwäsche-Strukturen, Peel-Chains, Mixer-Nutzung - AI analysiert alles automatisch.',
                power: 'Übermenschliche Pattern-Erkennung',
                features: [
                  '100+ ML-Heuristiken aktiv',
                  'Mixer-Demixing (65-75% Erfolg)',
                  'Wallet-Clustering automatisch',
                  'Risk-Scoring in Echtzeit'
                ]
              }
            ].map((feature, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1 }}
                className="bg-white/10 backdrop-blur-xl rounded-xl p-4 sm:p-5 md:p-6 border border-white/20 hover:bg-white/20 transition-all group"
              >
                <div className="p-2 sm:p-3 bg-gradient-to-br from-blue-600 to-blue-700 rounded-lg inline-block mb-3 sm:mb-4 group-hover:scale-110 transition-transform">
                  <feature.icon className="w-6 h-6 sm:w-7 sm:h-7 md:w-8 md:h-8 text-white" />
                </div>
                
                <h3 className="text-lg sm:text-xl font-bold mb-2">{feature.title}</h3>
                <p className="text-xs sm:text-sm opacity-90 mb-3">{feature.description}</p>
                
                <div className="px-3 py-1.5 bg-blue-700 rounded-lg inline-block mb-4 font-bold text-xs">
                  💪 {feature.power}
                </div>

                <div className="space-y-1.5">
                  {feature.features.map((item, j) => (
                    <div key={j} className="flex items-start gap-2">
                      <CheckCircle className="w-4 h-4 text-blue-400 flex-shrink-0 mt-0.5" />
                      <span className="text-xs">{item}</span>
                    </div>
                  ))}
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* POLIZEI USE CASES */}
      <section className="py-12 px-6">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-3xl md:text-4xl font-bold text-center mb-10">
            Typische Polizei-Ermittlungen
            <div className="text-base text-slate-600 dark:text-slate-400 mt-2">
              🤖 Alle mit AI-Agent-Unterstützung
            </div>
          </h2>

          <div className="grid md:grid-cols-2 gap-6">
            {[
              {
                title: 'Drogen-Handel auf Dark Web',
                icon: Lock,
                scenario: 'Verdächtiger betreibt Dark-Web-Shop. Bitcoin-Adressen aus Ermittlung bekannt.',
                aiSolution: 'AI-Agent überwacht ALLE Adressen 24/7. Alert bei JEDER Transaktion. Cross-Chain-Tracking zu Exchanges. Exit-Point-Detection automatisch.',
                result: '127 BTC bewegt → Alert nach 0.8s → Exit zu Binance identifiziert → KYC-Anfrage → Festnahme nach 72h',
                time: 'Echtzeit-Überwachung + 72h bis Festnahme',
                aiFeatures: ['24/7 Monitoring', 'Instant Alerts', 'Auto-Tracing', 'Exchange-Detection']
              },
              {
                title: 'Ransomware-Gangs',
                icon: Shield,
                scenario: 'Ransomware-Gang erpresst 150+ Firmen. Lösegeldzahlungen gehen an bekannte Wallets.',
                aiSolution: 'AI überwacht alle Gang-Wallets. Erkennt Auszahlungen automatisch. Mixer-Demixing aktiv. Dormant-Funds-Tracking parallel.',
                result: '456 BTC über 8 Monate → 78% zu Exchanges traced → 45 Verdächtige identifiziert → International Coordination',
                time: '8 Monate Überwachung, kontinuierliche Intelligence',
                aiFeatures: ['Multi-Wallet-Tracking', 'Mixer-Demixing', 'Gang-Network-Analysis', 'Dormant-Alerts']
              },
              {
                title: 'Terrorismus-Finanzierung',
                icon: Globe,
                scenario: 'Verdacht auf Terrorismus-Finanzierung via Crypto. Mehrere Verdächtige, unklare Connections.',
                aiSolution: 'AI analysiert Netzwerk automatisch. Clustering findet gemeinsame Wallets. Sanctions-Screening aktiv. Cross-Border-Intelligence.',
                result: 'Netzwerk von 234 Wallets entdeckt → 45 Sanctioned Entities → 3 Jurisdictions → Vollständige Aufklärung',
                time: '30 Tage Investigation, 24/7 AI-Unterstützung',
                aiFeatures: ['Network-Discovery', 'Sanctions-Check', 'Multi-Jurisdiction', 'Intelligence-Sharing']
              },
              {
                title: 'Organisierte Kriminalität',
                icon: Users,
                scenario: 'OK-Gruppe wäscht Geld aus Drogenhandel, Prostitution, Schutzgeld via Crypto.',
                aiSolution: 'AI erkennt Geldwäsche-Patterns automatisch. Peel-Chains, Round-Amounts, Layering - alles wird geflashed. Risk-Scoring in Echtzeit.',
                result: 'Komplexe Struktur mit 89 Wallets aufgedeckt → Alle Connections visualisiert → Gerichtsverwertbare Evidence',
                time: '45 Tage, AI-gestützte Pattern-Analyse',
                aiFeatures: ['Pattern-Detection', 'Geldwäsche-Scoring', 'Network-Visualization', 'Evidence-Generation']
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
                <div className="flex items-start gap-3 mb-4">
                  <div className="p-3 bg-gradient-to-br from-blue-600 to-blue-700 rounded-lg">
                    <useCase.icon className="w-6 h-6 text-white" />
                  </div>
                  <div className="flex-1">
                    <h3 className="text-lg font-bold mb-1">{useCase.title}</h3>
                    <div className="inline-flex items-center gap-1 px-2 py-0.5 bg-blue-100 dark:bg-blue-900/30 rounded-full text-xs font-semibold text-blue-600 dark:text-blue-400">
                      <Brain className="w-3 h-3" />
                      AI-Powered
                    </div>
                  </div>
                </div>

                <div className="space-y-3 mb-4">
                  <div>
                    <div className="text-xs font-bold text-slate-500 dark:text-slate-400 mb-1">📋 SZENARIO:</div>
                    <p className="text-sm text-slate-700 dark:text-slate-300">{useCase.scenario}</p>
                  </div>

                  <div>
                    <div className="text-xs font-bold text-blue-600 dark:text-blue-400 mb-1">🤖 AI-LÖSUNG:</div>
                    <p className="text-sm text-slate-700 dark:text-slate-300">{useCase.aiSolution}</p>
                  </div>

                  <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-3">
                    <div className="text-xs font-bold text-green-600 dark:text-green-400 mb-1">✅ ERGEBNIS:</div>
                    <p className="text-xs text-slate-700 dark:text-slate-300">{useCase.result}</p>
                  </div>
                </div>

                <div className="flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400 mb-3 pb-3 border-b border-slate-200 dark:border-slate-700">
                  <Clock className="w-3 h-3" />
                  <strong>Zeitrahmen:</strong> {useCase.time}
                </div>

                <div className="grid grid-cols-2 gap-1.5">
                  {useCase.aiFeatures.map((feature, j) => (
                    <div key={j} className="flex items-center gap-1.5 text-xs bg-blue-50 dark:bg-blue-900/20 px-2 py-1.5 rounded-lg">
                      <Sparkles className="w-3 h-3 text-blue-500" />
                      <span className="font-medium text-xs">{feature}</span>
                    </div>
                  ))}
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* AI-AGENT WORKFLOW */}
      <section className="py-12 md:py-16 pb-24 px-6 bg-gradient-to-br from-slate-900 via-blue-900 to-slate-800 text-white relative z-10">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-3xl md:text-4xl font-bold text-center mb-10">
            So arbeitet der AI-Agent für Sie
          </h2>

          <div className="grid md:grid-cols-4 gap-4">
            {[
              {
                step: '1',
                title: 'Wallets hinzufügen',
                description: 'Verdächtige Wallets zu AI-Agent hinzufügen. Chat-Command oder UI.',
                action: '"Überwache 1A1zP1..."',
                time: '10 Sekunden'
              },
              {
                step: '2',
                title: 'AI aktiviert sich',
                description: 'Agent startet automatisch. Überwacht 24/7. Alle Chains parallel.',
                action: 'Fully autonomous',
                time: 'Instant'
              },
              {
                step: '3',
                title: 'Echtzeit-Überwachung',
                description: 'Jede Transaktion wird analysiert. Risk-Scoring, Pattern-Detection, Alerts.',
                action: 'Kontinuierlich',
                time: '< 1s Latenz'
              },
              {
                step: '4',
                title: 'Sie werden alerted',
                description: 'Verdächtige Aktivität? Instant Alert via Telegram/Email. Mit Details & Actions.',
                action: 'Push + Report',
                time: '< 1 Sekunde'
              }
            ].map((item, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1 }}
                className="relative"
              >
                <div className="bg-gradient-to-br from-blue-600 to-blue-700 text-white rounded-full w-12 h-12 flex items-center justify-center text-lg font-bold mb-3 mx-auto shadow-xl">
                  {item.step}
                </div>
                <div className="bg-white/10 backdrop-blur-xl rounded-lg p-4 shadow-xl border border-white/20 h-full">
                  <h3 className="font-bold text-base mb-2">{item.title}</h3>
                  <p className="text-xs opacity-90 mb-3">{item.description}</p>
                  
                  <div className="space-y-1.5">
                    <div className="flex items-center gap-1.5 text-xs bg-blue-500/20 px-2 py-1.5 rounded-lg">
                      <Target className="w-3 h-3" />
                      <span><strong>Action:</strong> {item.action}</span>
                    </div>
                    <div className="flex items-center gap-1.5 text-xs bg-blue-600/20 px-2 py-1.5 rounded-lg">
                      <Clock className="w-3 h-3" />
                      <span><strong>Zeit:</strong> {item.time}</span>
                    </div>
                  </div>
                </div>
                {i < 3 && (
                  <div className="hidden md:block absolute top-8 left-full w-full h-0.5 bg-blue-600 -z-10" />
                )}
              </motion.div>
            ))}
          </div>

          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            className="mt-8 text-center"
          >
            <div className="inline-flex items-center gap-2 px-6 py-3 bg-slate-700 rounded-full text-white font-bold text-sm shadow-2xl">
              <Zap className="w-4 h-4 animate-pulse" />
              VOLLAUTOMATISCH - Sie entscheiden nur, WAS überwacht wird
              <Activity className="w-4 h-4 animate-bounce" />
            </div>
          </motion.div>
        </div>
      </section>

      {/* FAQ Section */}
      <div className="relative z-0 mt-8 md:mt-12">
      <FAQSection
        title="Häufig gestellte Fragen - Polizei & Ermittlungsbehörden"
        description="Alle wichtigen Fragen zu AI-gestützten Blockchain-Ermittlungen für Strafverfolgungsbehörden"
        categoryColor="blue"
        faqs={[
          {
            question: "Wie funktioniert die 24/7 AI-Agent-Überwachung genau?",
            answer: "Unser AI-Agent überwacht automatisch alle von Ihnen hinzugefügten verdächtigen Wallets rund um die Uhr. Bei jeder Transaktion analysiert die AI in Echtzeit:\n\n✅ Transaktionsmuster und Anomalien\n✅ Verbindungen zu bekannten Mixern\n✅ Exit-Points zu Exchanges\n✅ Cross-Chain-Bewegungen\n✅ Sanctions-List-Matches\n\nSie erhalten instant Alerts (<1 Sekunde) via Telegram, Email oder SMS, sobald verdächtige Aktivität erkannt wird. Die AI arbeitet vollautomatisch - Sie müssen nichts manuell prüfen."
          },
          {
            question: "Sind die generierten Reports gerichtsverwertbar?",
            answer: "Ja, absolut! Alle unsere Reports erfüllen höchste Standards für gerichtsverwertbare Beweismittel:\n\n📄 Timestamped PDF-Reports mit Chain-of-Custody\n🔒 SHA256-Hashwerte für Integrität\n✍️ Optional: RSA-PSS digitale Signaturen\n⚖️ 99% Court Acceptance Rate (basierend auf realen Fällen)\n📊 Detaillierte Methodologie & Nachvollziehbarkeit\n\nUnsere Reports werden bereits von Staatsanwaltschaften in mehreren Ländern akzeptiert. Wir bieten auch Expert Witness Support für komplexe Fälle."
          },
          {
            question: "Welche Blockchains und Kryptowährungen werden unterstützt?",
            answer: "Wir unterstützen 35+ Blockchains, darunter:\n\n💎 Bitcoin (inkl. Lightning Network)\n💎 Ethereum & alle EVM-Chains (Polygon, BSC, Arbitrum, Optimism, etc.)\n💎 Solana, Cardano, Polkadot\n💎 Privacy Coins (Monero-Tracing limitiert, Zcash transparent addresses)\n💎 DeFi-Protokolle (Uniswap, Aave, Compound, etc.)\n\nCross-Chain-Tracking funktioniert automatisch - wenn Gelder über Bridges bewegt werden, verfolgen wir sie nahtlos über alle Chains hinweg."
          },
          {
            question: "Wie schnell kann ich mit Ermittlungsergebnissen rechnen?",
            answer: "Unsere AI-Technologie ermöglicht beispiellose Geschwindigkeit:\n\n⚡ Basic Trace: 30-60 Sekunden\n⚡ Deep Investigation: 2-5 Minuten\n⚡ Complex Network Analysis: 10-15 Minuten\n⚡ AI-Agent Alerts: <1 Sekunde bei Live-Überwachung\n\nWährend traditionelle manuelle Analysen Tage bis Wochen dauern, liefern wir Ergebnisse in Minuten. Das ist echter Zeitgewinn für Ihre Ermittlungen."
          },
          {
            question: "Was kostet die Plattform für Behörden?",
            answer: "Wir bieten faire, transparente Preise für jede Behördengröße:\n\n🆓 Community Plan: Kostenlos für Einzelermittler (limitierte Features)\n💼 Pro Plan: €99/Monat für Teams (unbegrenzte Traces)\n🏛️ Agency Plan: Ab €499/Monat (Multi-User, API-Zugang, Priority Support)\n🌍 Enterprise: Custom Pricing für große Behörden (Self-Hosted möglich)\n\nProfessionelle Blockchain-Forensik muss nicht unbezahlbar sein. Unsere Preisgestaltung macht modernste Technologie für alle Behörden zugänglich."
          },
          {
            question: "Wie sicher sind meine Ermittlungsdaten?",
            answer: "Datensicherheit hat bei uns höchste Priorität:\n\n🔐 End-to-End Verschlüsselung (AES-256)\n🔐 Zero-Knowledge Architecture (wir sehen Ihre Daten nicht)\n🔐 Optional: Self-Hosted Deployment für maximale Kontrolle\n🔐 EU-Server (DSGVO-konform)\n🔐 Multi-Factor Authentication (MFA)\n🔐 Role-Based Access Control (RBAC)\n🔐 Audit Logs für alle Zugriffe\n\nFür sensible Ermittlungen bieten wir Air-Gapped Deployments an."
          },
          {
            question: "Benötige ich Blockchain-Expertise, um die Plattform zu nutzen?",
            answer: "Nein! Unsere Plattform ist für Ermittler ohne Blockchain-Kenntnisse designed:\n\n👤 Natural Language Interface: Fragen Sie die AI in normaler Sprache\n👤 Intuitive UI: Keine komplexen Blockchain-Explorer nötig\n👤 Auto-Erklärungen: AI erklärt alle technischen Details verständlich\n👤 Video-Tutorials: Kostenlose Schulungen für Ihr Team\n👤 24/7 Support: Deutschsprachiger Expert Support\n\nDurchschnittliche Einarbeitungszeit: <2 Stunden. Sie können sofort produktiv sein."
          },
          {
            question: "Kann ich mehrere Fälle parallel überwachen?",
            answer: "Ja, unbegrenzt! Der AI-Agent kann:\n\n♾️ Unbegrenzt viele Wallets gleichzeitig überwachen\n♾️ Jeden Fall separat organisieren (Case Management)\n♾️ Individuelle Alert-Regeln pro Fall setzen\n♾️ Team-Collaboration: Mehrere Ermittler pro Fall\n♾️ Automatische Case-Reports generieren\n\nTypische Nutzung: 10-50 aktive Fälle parallel. Große Behörden: 200+ Fälle gleichzeitig ohne Performance-Verlust."
          }
        ]}
      />
      </div>

      {/* CTA */}
      <section className="py-12 px-6">
        <div className="max-w-4xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            className="bg-gradient-to-r from-blue-600 to-blue-700 rounded-xl p-6 sm:p-8 text-white shadow-2xl mx-4"
          >
            <Brain className="w-16 h-16 mx-auto mb-4 animate-pulse" />
            
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              Aktivieren Sie Ihren AI-Agent jetzt
            </h2>
            <p className="text-base md:text-lg mb-6 opacity-90">
              14 Tage kostenlos testen. Keine Kreditkarte. Volle AI-Power.
            </p>
            <div className="flex flex-wrap gap-3 justify-center">
              <Link
                to={`/${i18n.language}/register`}
                className="px-6 py-3 bg-white text-blue-600 rounded-lg font-bold text-sm hover:shadow-2xl transition-all flex items-center gap-2"
              >
                AI-Agent aktivieren
                <Sparkles className="w-4 h-4" />
              </Link>
              <Link
                to={`/${i18n.language}/contact`}
                className="px-6 py-3 bg-white/20 backdrop-blur-sm text-white rounded-lg font-bold text-sm hover:bg-white/30 transition-all"
              >
                Persönliche Demo
              </Link>
            </div>
          </motion.div>
        </div>
      </section>
    </div>
  )
}

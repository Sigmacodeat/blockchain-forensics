/**
 * Use Case: Compliance & AML für Exchanges & Banken
 * SEO-Optimized Landing Page für Compliance-Abteilungen
 */

import React from 'react'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { 
  Shield, CheckCircle, AlertTriangle, Users, Globe, 
  TrendingUp, ArrowRight, Clock, FileText, Lock, Zap 
} from 'lucide-react'
import FAQSection from '@/components/FAQSection'
import { usePageMeta } from '@/hooks/usePageMeta'
import { useEnhancedSEO } from '@/hooks/useEnhancedSEO'

export default function UseCaseCompliance() {
  const { t, i18n } = useTranslation()

  useEnhancedSEO({
    title: 'AML-Compliance & KYT für Krypto-Exchanges | Automatisiert & FATF-konform',
    description: 'Real-Time Transaction Monitoring <100ms. 9 Sanctions Lists. Auto-SAR. Travel Rule compliant. 71% Kostenreduktion vs. manuelle Reviews.',
    keywords: ['AML Compliance', 'KYT Crypto', 'Transaction Monitoring', 'Sanctions Screening', 'FATF compliant', 'Travel Rule', 'Crypto Exchange Compliance'],
    og_image: '/og-images/use-case-compliance.png',
    og_image_width: 1200,
    og_image_height: 630,
    twitter_card: 'summary_large_image'
  })

  usePageMeta(
    'AML-Compliance & KYT für Exchanges',
    'Automatisierte AML-Compliance für Krypto-Exchanges. Real-Time Monitoring, FATF-konform, 71% Kostenreduktion.'
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
              <Shield className="w-4 h-4 text-blue-600 dark:text-blue-400" />
              <span className="text-sm font-medium text-blue-600 dark:text-blue-400">
                Für Compliance & AML
              </span>
            </div>
            
            <h1 className="text-3xl sm:text-4xl md:text-5xl lg:text-6xl font-bold mb-4 md:mb-6 bg-gradient-to-r from-blue-600 to-blue-800 bg-clip-text text-transparent">
              Automatisierte AML-Compliance
            </h1>
            
            <p className="text-base sm:text-lg md:text-xl text-slate-600 dark:text-slate-400 max-w-3xl mx-auto mb-6 md:mb-8 px-4">
              Real-Time Transaction Monitoring, Sanctions Screening und Risk Scoring für Krypto-Exchanges und Banken. FATF-compliant und vollautomatisch.
            </p>

            <div className="flex flex-wrap gap-4 justify-center">
              <Link
                to={`/${i18n.language}/universal-screening`}
                className="px-8 py-4 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-lg font-semibold hover:from-blue-700 hover:to-blue-800 transition-all shadow-lg flex items-center gap-2"
              >
                Screening starten
                <ArrowRight className="w-5 h-5" />
              </Link>
              <Link
                to={`/${i18n.language}/pricing`}
                className="px-8 py-4 bg-white dark:bg-slate-800 text-slate-900 dark:text-white rounded-lg font-semibold hover:shadow-lg transition-all border border-slate-200 dark:border-slate-700"
              >
                Preise ansehen
              </Link>
            </div>
          </motion.div>

          {/* Compliance Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 md:gap-6 max-w-5xl mx-auto px-4">
            {[
              { value: '< 100ms', label: 'Transaction Screening' },
              { value: '9', label: 'Sanctions Lists' },
              { value: '35+', label: 'Supported Chains' },
              { value: '99.9%', label: 'Accuracy' }
            ].map((stat, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.1 }}
                className="bg-white/80 dark:bg-slate-800/80 backdrop-blur-xl rounded-xl p-3 sm:p-4 md:p-6 text-center shadow-lg"
              >
                <div className="text-2xl sm:text-3xl font-bold text-blue-600 dark:text-blue-400 mb-2">
                  {stat.value}
                </div>
                <div className="text-xs sm:text-sm text-slate-600 dark:text-slate-400">
                  {stat.label}
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Compliance Challenges */}
      <section className="py-20 px-6 bg-white/50 dark:bg-slate-900/50">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-4xl font-bold text-center mb-16">
            Ihre Compliance-Herausforderungen - Unsere Lösungen
          </h2>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {[
              {
                challenge: 'KYT (Know-Your-Transaction)',
                solution: 'Real-Time Risk Scoring',
                description: 'Jede eingehende/ausgehende Transaktion wird in <100ms analysiert. Automatic flagging von High-Risk Transactions.',
                features: ['Real-Time Monitoring', 'Auto-Alerts bei High-Risk', 'Customizable Rules'],
                icon: Zap
              },
              {
                challenge: 'Sanctions Compliance',
                solution: 'Multi-Jurisdiction Screening',
                description: '9 Sanctions Lists gleichzeitig (OFAC, UN, EU, UK, CA, AU, CH, JP, SG). Automatic blocking von sanctioned addresses.',
                features: ['9 Jurisdictions', 'Auto-Update Lists', 'Instant Blocking'],
                icon: Shield
              },
              {
                challenge: 'VASP Verification',
                solution: 'Travel Rule Engine',
                description: 'FATF Travel Rule Compliance mit IVMS101 Format. Automatic VASP Directory lookups, OpenVASP/TRP support.',
                features: ['IVMS101 Format', 'OpenVASP Support', 'Auto-Verification'],
                icon: Users
              },
              {
                challenge: 'High-Risk Customers',
                solution: 'Customer Risk Profiling',
                description: 'Automatic risk scoring aller Kunden basierend auf Transaction Patterns, Counterparties, Geographic Risk.',
                features: ['Auto-Risk-Scoring', 'Behavioral Analysis', 'Continuous Monitoring'],
                icon: AlertTriangle
              },
              {
                challenge: 'Reporting & Audit',
                solution: 'Automated SAR Generation',
                description: 'Suspicious Activity Reports (SAR) werden automatisch generiert. Export für BaFin, FinCEN, FIU.',
                features: ['Auto-SAR-Generation', 'Regulator-Ready', 'Audit Trail'],
                icon: FileText
              },
              {
                challenge: 'Multi-Chain Complexity',
                solution: '35+ Chain Support',
                description: 'Einheitliches Screening für Bitcoin, Ethereum, USDT, USDC, Polygon, BSC, Arbitrum, Solana, und mehr.',
                features: ['35+ Chains', 'Unified API', 'Cross-Chain Tracing'],
                icon: Globe
              }
            ].map((item, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1 }}
                className="bg-white dark:bg-slate-800 rounded-xl p-4 sm:p-5 shadow-lg border border-slate-200/50 dark:border-slate-700/50"
              >
                <div className="flex items-start gap-3 mb-4">
                  <div className="p-2 sm:p-3 bg-blue-100 dark:bg-blue-900/30 rounded-lg flex-shrink-0">
                    <item.icon className="w-5 h-5 sm:w-6 sm:h-6 text-blue-600 dark:text-blue-400" />
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 dark:text-slate-400 mb-1">
                      Challenge:
                    </div>
                    <h3 className="font-bold text-base sm:text-lg mb-1">{item.challenge}</h3>
                    <div className="text-sm font-semibold text-blue-600 dark:text-blue-400">
                      → {item.solution}
                    </div>
                  </div>
                </div>

                <p className="text-sm text-slate-600 dark:text-slate-400 mb-4">
                  {item.description}
                </p>

                <div className="space-y-4 px-4">
                  {item.features.map((feature, j) => (
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

      {/* Compliance Workflow */}
      <section className="py-20 px-6">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-4xl font-bold text-center mb-16">
            Automatisierter Compliance-Workflow
          </h2>

          <div className="space-y-8 max-w-4xl mx-auto">
            {[
              {
                step: 'Transaction Received',
                description: 'Kunde sendet/empfängt Krypto-Transaktion',
                auto: 'Webhook triggert automatisches Screening',
                time: '< 1ms'
              },
              {
                step: 'Real-Time Screening',
                description: 'Address Screening (9 Sanctions Lists), Risk Scoring, VASP Verification',
                auto: 'System analysiert in Echtzeit',
                time: '< 100ms'
              },
              {
                step: 'Risk Assessment',
                description: 'ML-basiertes Risk Scoring: Safe, Low, Medium, High, Critical',
                auto: 'Auto-Classification',
                time: '< 50ms'
              },
              {
                step: 'Decision & Action',
                description: 'Safe → Approve, High/Critical → Block/Flag, Medium → Manual Review',
                auto: 'Automatic Approval/Blocking',
                time: '< 10ms'
              },
              {
                step: 'Reporting & Audit',
                description: 'Alle Decisions werden geloggt. SAR bei Suspicious Activity',
                auto: 'Auto-SAR-Generation',
                time: 'Instant'
              }
            ].map((step, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: -20 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1 }}
                className="flex gap-6 items-start"
              >
                <div className="flex-shrink-0">
                  <div className="w-10 h-10 sm:w-12 sm:h-12 bg-gradient-to-br from-blue-600 to-blue-700 rounded-full flex items-center justify-between text-white font-bold text-lg sm:text-xl">
                    {i + 1}
                  </div>
                </div>
                <div className="flex-1 bg-white dark:bg-slate-800 rounded-xl p-5 shadow-md border border-slate-200/50 dark:border-slate-700/50">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="font-bold text-base sm:text-lg">{step.step}</h3>
                    <span className="text-sm font-semibold text-blue-600 dark:text-blue-400">
                      ⏱️ {step.time}
                    </span>
                  </div>
                  <p className="text-slate-600 dark:text-slate-400 mb-3">
                    {step.description}
                  </p>
                  <div className="flex items-center gap-2 text-sm">
                    <Zap className="w-4 h-4 text-blue-500" />
                    <span className="font-semibold text-blue-600 dark:text-blue-400">
                      {step.auto}
                    </span>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ROI Calculator */}
      <section className="py-20 px-6 bg-white/50 dark:bg-slate-900/50">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-4xl font-bold text-center mb-16">
            ROI: Compliance-Team vs. Automation
          </h2>

          <div className="grid sm:grid-cols-2 md:grid-cols-3 gap-4 md:gap-8 px-4">
            <div className="bg-red-50 dark:bg-red-900/20 rounded-xl p-6 border border-red-200/50 dark:border-red-800/50">
              <h3 className="text-2xl font-bold text-red-600 dark:text-red-400 mb-6">
                ❌ Manuelles Compliance-Team
              </h3>
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span>3 Compliance Officers</span>
                  <span className="font-bold">€180.000/Jahr</span>
                </div>
                <div className="flex justify-between items-center">
                  <span>Forensik-Tools Lizenzen</span>
                  <span className="font-bold">€50.000/Jahr</span>
                </div>
                <div className="flex justify-between items-center">
                  <span>Manual Reviews</span>
                  <span className="font-bold">~500/Tag</span>
                </div>
                <div className="flex justify-between items-center">
                  <span>Processing Time</span>
                  <span className="font-bold">~2 Min/TX</span>
                </div>
                <div className="border-t pt-4 mt-4">
                  <div className="flex justify-between items-center text-xl font-bold">
                    <span>TOTAL COST:</span>
                    <span className="text-red-600 dark:text-red-400">€230.000/Jahr</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-green-50 dark:bg-green-900/20 rounded-2xl p-8">
              <h3 className="text-2xl font-bold text-green-600 dark:text-green-400 mb-6">
                ✅ Unsere Automation
              </h3>
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span>Business Plan</span>
                  <span className="font-bold">€6.000/Jahr</span>
                </div>
                <div className="flex justify-between items-center">
                  <span>1 Compliance Officer (Oversight)</span>
                  <span className="font-bold">€60.000/Jahr</span>
                </div>
                <div className="flex justify-between items-center">
                  <span>Auto-Reviews</span>
                  <span className="font-bold">Unbegrenzt</span>
                </div>
                <div className="flex justify-between items-center">
                  <span>Processing Time</span>
                  <span className="font-bold">{'<100ms/TX'}</span>
                </div>
                <div className="border-t pt-4 mt-4">
                  <div className="flex justify-between items-center text-xl font-bold">
                    <span>TOTAL COST:</span>
                    <span className="text-blue-600 dark:text-blue-400">€66.000/Jahr</span>
                  </div>
                  <div className="mt-4 p-4 bg-blue-100 dark:bg-blue-900/30 rounded-lg text-center">
                    <div className="text-3xl font-bold text-blue-600 dark:text-blue-400">
                      €164.000 gespart
                    </div>
                    <div className="text-sm text-blue-700 dark:text-blue-300">
                      = 71% Kostenreduktion
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* FAQ Section */}
      <div className="relative z-0 mt-10 md:mt-14">
      <FAQSection
        title="Häufig gestellte Fragen - Compliance & AML"
        description="Alle wichtigen Fragen zu automatisierter AML-Compliance für Krypto-Exchanges und Banken"
        categoryColor="blue"
        faqs={[
          {
            question: "Was ist KYT (Know-Your-Transaction) und warum brauche ich es?",
            answer: "KYT ist die kontinuierliche Überwachung ALLER Crypto-Transaktionen Ihrer Kunden in Echtzeit:\n\n🔍 Jede eingehende/ausgehende TX wird analysiert\n🔍 Sanctions Screening (9 Listen: OFAC, UN, EU, UK, etc.)\n🔍 Risk Scoring (Safe/Low/Medium/High/Critical)\n🔍 Automatisches Blocking bei High-Risk\n🔍 SAR-Generation bei Suspicious Activity\n\nOhne KYT riskieren Sie:\n⚠️ Regulatorische Strafen (€100.000-10M+)\n⚠️ Lizenz-Entzug\n⚠️ Reputationsschäden\n\nKYT ist PFLICHT für alle FATF-regulierten Krypto-Businesses."
          },
          {
            question: "Wie schnell ist Ihre Transaction-Screening-Engine?",
            answer: "Unsere Engine ist auf maximale Performance optimiert:\n\n⚡ Transaction Screening: <100ms\n⚡ Sanctions List Check: <50ms (9 Listen parallel)\n⚡ Risk Scoring: <30ms (ML-basiert)\n⚡ Decision & Action: <10ms\n⚡ GESAMT: <100ms pro Transaction\n\nDas bedeutet: Keine spürbaren Latenzen für Ihre Kunden, höherer Durchsatz und bessere User Experience für Ihr gesamtes Transaktions-Volumen."
          },
          {
            question: "Welche Sanctions Lists werden unterstützt?",
            answer: "Wir screenen gegen 9 internationale Sanctions Lists:\n\n🇺🇸 OFAC (USA): SDN, Non-SDN, Sectoral Sanctions\n🇪🇺 EU: Consolidated List\n🇬🇧 UK: HM Treasury Sanctions\n🇺🇳 UN: Security Council Sanctions\n🇨🇦 Canada: SEMA List\n🇦🇺 Australia: DFAT Sanctions\n🇨🇭 Switzerland: SECO Sanctions\n🇯🇵 Japan: METI List\n🇸🇬 Singapore: MAS Sanctions\n\nAlle Listen werden täglich aktualisiert. Bei neuen Sanctioned Entities werden alle bestehenden Kunden automatisch re-gescreent."
          },
          {
            question: "Ist Ihre Lösung FATF-compliant?",
            answer: "Ja, 100%! Wir erfüllen alle FATF-Empfehlungen:\n\n✅ Recommendation 10: Customer Due Diligence (CDD)\n✅ Recommendation 15: New Technologies Risk Assessment\n✅ Recommendation 16: Travel Rule (IVMS101 format)\n✅ Recommendation 20: Suspicious Transaction Reporting (STR/SAR)\n✅ Recommendation 21: Sanctions Screening\n\nUnsere Compliance-Features:\n📄 Audit Trails (jede Decision geloggt)\n📄 Auto-SAR-Generation\n📄 Regulator-Ready Reports\n📄 Travel Rule Messages (IVMS101)\n📄 Risk-Based Approach (RBA)\n\nWir wurden bereits von mehreren Regulatoren (BaFin, FCA, etc.) geprüft und approved."
          },
          {
            question: "Was kostet AML-Compliance-Automation?",
            answer: "Transparente, skalierbare Preise für jede Unternehmensgröße:\n\n💼 Business Plan: €499/Monat (bis 10.000 TX/Monat)\n🏛️ Enterprise: Ab €2.000/Monat (unbegrenzt)\n🌍 White-Label: Custom Pricing\n\nProfessionelle AML-Compliance zu Preisen, die auch mittelständische Exchanges nicht ausschließen. Plus: Sie sparen 71% Ihrer Compliance-Kosten durch Automation (weniger Officers nötig)."
          },
          {
            question: "Wie funktioniert die Travel Rule Implementation?",
            answer: "Wir unterstützen alle gängigen Travel Rule Protokolle:\n\n🔗 IVMS101 (Standard Data-Format)\n🔗 OpenVASP (Open-Source Protokoll)\n🔗 TRP (Travel Rule Protocol)\n🔗 Sygna Bridge (VASP-Netzwerk)\n🔗 Notabene (VASP-Discovery)\n\nUnser Workflow:\n1️⃣ Kunden-Transaction > Threshold (€1.000/€1.500)\n2️⃣ VASP-Discovery (automatisch)\n3️⃣ Travel Rule Message senden (IVMS101)\n4️⃣ Response empfangen & verarbeiten\n5️⃣ Compliance Decision (Approve/Reject)\n\nAlles vollautomatisch! <2 Sekunden zusätzliche Latenz."
          },
          {
            question: "Kann ich False Positives reduzieren?",
            answer: "Ja! Unsere ML-Engine lernt kontinuierlich:\n\n🤖 Machine Learning Risk Scoring (100+ Features)\n🤖 Customizable Rules per Customer-Segment\n🤖 Whitelisting (Trusted Entities)\n🤖 Feedback-Loop (False Positives markieren)\n🤖 A/B-Testing verschiedener Rule-Sets\n\nTypische False Positive Rates:\n⚠️ Manuelle Reviews: 15-25%\n✅ Unsere Engine: 2-5% (nach Training)\n\nDas bedeutet: 80% weniger False Positives = 80% weniger manuelle Arbeit für Ihr Compliance-Team!"
          },
          {
            question: "Bieten Sie SAR/STR-Auto-Generation an?",
            answer: "Ja! Unser System generiert automatisch SAR/STR-Reports:\n\n📄 Trigger: High-Risk TX oder Suspicious Patterns\n📄 Data Collection: Alle relevanten TX-Details\n📄 Risk Analysis: ML-basierte Suspicious-Score\n📄 Report-Generation: PDF/XML (regulator-format)\n📄 Review & Submit: Officer reviewt & submitted\n\nZeit gespart:\n⏱️ Manuell: 2-4h pro SAR\n⏱️ Mit uns: 15-30 Min (nur Review)\n\nSAR-Reports sind bereits vorausgefüllt mit allen nötigen Informationen (TX-History, Risk-Scores, Related Entities, etc.)."
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
            className="bg-gradient-to-r from-blue-600 to-blue-700 rounded-xl p-6 sm:p-8 md:p-12 text-white shadow-2xl mx-4"
          >
            <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold mb-4 sm:mb-6">
              Automatisieren Sie Ihre Compliance heute
            </h2>
            <p className="text-base sm:text-lg md:text-xl mb-6 sm:mb-8 opacity-90">
              Kostenlose Demo für Compliance-Teams. Siehe wie Sie 71% Kosten sparen können.
            </p>
            <div className="flex flex-wrap gap-4 justify-center">
              <Link
                to={`/${i18n.language}/register`}
                className="px-8 py-4 bg-white text-blue-600 rounded-lg font-semibold hover:shadow-xl transition-all flex items-center gap-2"
              >
                Demo anfragen
                <ArrowRight className="w-5 h-5" />
              </Link>
              <Link
                to={`/${i18n.language}/pricing`}
                className="px-8 py-4 bg-white/20 backdrop-blur-sm text-white rounded-lg font-semibold hover:bg-white/30 transition-all"
              >
                Preise ansehen
              </Link>
            </div>
          </motion.div>
        </div>
      </section>

      {/* SEO Content */}
      <section className="py-20 px-6 bg-white/50 dark:bg-slate-900/50">
        <div className="max-w-4xl mx-auto prose dark:prose-invert">
          <h2>AML-Compliance für Krypto-Exchanges: Ultimate Guide</h2>
          
          <p>
            Als Compliance-Abteilung einer Krypto-Exchange oder Bank stehen Sie vor der 
            Herausforderung, FATF-Compliance zu gewährleisten bei gleichzeitiger Kosteneffizienz. 
            Unsere automatisierte AML-Lösung reduziert Ihre Compliance-Kosten um 71%.
          </p>

          <h3>Was ist KYT (Know-Your-Transaction)?</h3>
          <p>
            KYT ist die kontinuierliche Überwachung aller Krypto-Transaktionen Ihrer Kunden. 
            Jede Transaction wird in Echtzeit gegen Sanctions Lists gescreent und Risk-gescoret. 
            High-Risk Transactions werden automatisch geflaggt oder geblockt.
          </p>

          <h3>Compliance-Features:</h3>
          <ul>
            <li><strong>Real-Time Screening:</strong> &lt;100ms Transaction Analysis</li>
            <li><strong>Multi-Sanctions:</strong> 9 Jurisdictions (OFAC, UN, EU, UK, etc.)</li>
            <li><strong>Travel Rule:</strong> FATF-compliant mit IVMS101 Format</li>
            <li><strong>Auto-SAR:</strong> Suspicious Activity Reports automatisch</li>
          </ul>

          <h3>Warum Automation statt manueller Reviews?</h3>
          <p>
            Manuelle Compliance-Reviews kosten durchschnittlich €230.000/Jahr (3 Officers + Tool-Lizenzen). 
            Unsere Automation kostet €66.000/Jahr (1 Officer + Platform) - eine Ersparnis von 71%. 
            Gleichzeitig ist die Accuracy höher (99.9% vs ~85% bei manuellen Reviews).
          </p>
        </div>
      </section>
    </div>
  )
}

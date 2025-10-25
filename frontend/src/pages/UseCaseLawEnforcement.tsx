/**
 * Use Case: Law Enforcement & Prosecution
 * SEO-Optimized Landing Page für Strafverfolgungsbehörden & Anwälte
 */

import React from 'react'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { 
  Scale, Shield, FileText, Search, Clock, TrendingUp, 
  CheckCircle, ArrowRight, Users, Globe, Lock, Zap 
} from 'lucide-react'
import FAQSection from '@/components/FAQSection'
import { usePageMeta } from '@/hooks/usePageMeta'
import { useEnhancedSEO } from '@/hooks/useEnhancedSEO'

export default function UseCaseLawEnforcement() {
  const { t, i18n } = useTranslation()

  useEnhancedSEO({
    title: 'Gerichtsverwertbare Bitcoin-Forensik für Strafverfolgung & Anwälte',
    description: 'Professionelle Blockchain-Analysen für Ransomware, Betrug, Geldwäsche. Court-admissible Evidence Reports in < 60s. 99% Court Acceptance Rate.',
    keywords: ['Bitcoin Forensik', 'Strafverfolgung Blockchain', 'Gerichtsverwertbare Evidence', 'Ransomware Investigation', 'Crypto Betrug', 'Geldwäsche', 'Court-admissible Reports'],
    og_image: '/og-images/use-case-law-enforcement.png',
    og_image_width: 1200,
    og_image_height: 630,
    twitter_card: 'summary_large_image'
  })

  usePageMeta(
    'Gerichtsverwertbare Bitcoin-Forensik',
    'Professionelle Blockchain-Analysen für Strafverfolgung. Court-admissible Evidence in unter 60 Sekunden.'
  )

  React.useEffect(() => {
    window.scrollTo({ top: 0, behavior: 'instant' })
  }, [])

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
            <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-blue-100 dark:bg-blue-900/30 rounded-full mb-4">
              <Scale className="w-3.5 h-3.5 text-blue-600 dark:text-blue-400" />
              <span className="text-xs font-medium text-blue-600 dark:text-blue-400">
                Für Strafverfolgung & Anwälte
              </span>
            </div>
            
            <h1 className="text-3xl sm:text-4xl md:text-5xl font-bold mb-3 md:mb-4 bg-gradient-to-r from-blue-600 to-blue-800 bg-clip-text text-transparent">
              Gerichtsverwertbare Bitcoin-Forensik
            </h1>
            
            <p className="text-sm sm:text-base md:text-lg text-slate-600 dark:text-slate-400 max-w-2xl mx-auto mb-4 md:mb-6 px-4">
              Professionelle Blockchain-Analysen für Ransomware, Betrug, Geldwäsche und Diebstahl. 
              Court-admissible Evidence Reports in unter 60 Sekunden.
            </p>

            <div className="flex flex-wrap gap-4 justify-center">
              <Link
                to={`/${i18n.language}/bitcoin-investigation`}
                className="px-6 py-3 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-lg font-semibold text-sm hover:from-blue-700 hover:to-blue-800 transition-all shadow-lg flex items-center gap-2"
              >
                Investigation starten
                <ArrowRight className="w-4 h-4" />
              </Link>
              <Link
                to={`/${i18n.language}/pricing`}
                className="px-6 py-3 bg-white dark:bg-slate-800 text-slate-900 dark:text-white rounded-lg font-semibold text-sm hover:shadow-lg transition-all border border-slate-200 dark:border-slate-700"
              >
                Preise ansehen
              </Link>
            </div>
          </motion.div>

          {/* Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-4xl mx-auto">
            {[
              { value: '< 60s', label: 'Investigation Zeit' },
              { value: '8+ Jahre', label: 'Historical Analysis' },
              { value: '15+', label: 'UTXO Heuristics' },
              { value: '99%', label: 'Court Acceptance' }
            ].map((stat, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.1 }}
                className="bg-white/80 dark:bg-slate-800/80 backdrop-blur-xl rounded-lg p-4 text-center shadow-lg"
              >
                <div className="text-2xl font-bold text-blue-600 dark:text-blue-400 mb-1">
                  {stat.value}
                </div>
                <div className="text-xs text-slate-600 dark:text-slate-400">
                  {stat.label}
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Use Cases */}
      <section className="py-20 px-6 bg-white/50 dark:bg-slate-900/50">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-4xl font-bold text-center mb-16">
            Typische Ermittlungsfälle
          </h2>

          <div className="grid md:grid-cols-2 gap-8">
            {[
              {
                title: 'Ransomware-Angriffe',
                icon: Lock,
                description: 'Verfolgen Sie Lösegeldzahlungen von der Zahlung bis zur Auszahlung. Identifizieren Sie Exit-Points zu Exchanges für KYC-Anfragen.',
                example: 'Fall: LockBit 3.0 - 45 BTC gestohlen → Investigation zeigt: 78.9 BTC zu Binance, 23.4 BTC dormant. Subpoena führt zu Verhaftung.',
                time: '30-45 Sekunden',
                features: ['Mixer-Demixing', 'Exit Point Detection', 'Dormant Funds Tracking']
              },
              {
                title: 'Krypto-Betrug & Theft',
                icon: Shield,
                description: 'Vollständige Vermögensverfolgung bei Diebstahl oder Betrug. Identifizieren Sie wo gestohlene Gelder hingingen.',
                example: 'Fall: Phishing-Theft - 125 ETH gestohlen → Trace zeigt: 78 ETH zu 3 Exchanges, 47 ETH über Bridge zu Polygon. Assets frozen.',
                time: '20-40 Sekunden',
                features: ['Cross-Chain Tracing', 'Asset Recovery', 'Freeze Coordination']
              },
              {
                title: 'Geldwäsche-Untersuchungen',
                icon: Search,
                description: 'Decken Sie komplexe Geldwäsche-Strukturen auf. Clustering zeigt gemeinsame Wallet-Eigentümerschaft.',
                example: 'Fall: Dark Web Market - 340 BTC über 3 Jahre → Clustering zeigt 15 Wallets, 8 Mixer-Nutzungen, Peel-Chain Pattern. 5 Verdächtige identifiziert.',
                time: '45-60 Sekunden',
                features: ['UTXO Clustering', 'Pattern Detection', 'Network Analysis']
              },
              {
                title: 'Terrorismus-Finanzierung',
                icon: Globe,
                description: 'Identifizieren Sie Finanzierungsströme zu terroristischen Organisationen. Sanctions-Screening inklusive.',
                example: 'Fall: ISIS-Finanzierung - 12 verdächtige Adressen → Vollständiger Trace zeigt 234 BTC-Netzwerk, 45 Sanctioned Entities, 3 Jurisdictions.',
                time: '40-60 Sekunden',
                features: ['Sanctions Screening', 'Network Mapping', 'Multi-Jurisdiction']
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
                <div className="flex items-start gap-3 sm:gap-4 mb-4 sm:mb-6">
                  <div className="p-2 sm:p-3 bg-blue-100 dark:bg-blue-900/30 rounded-lg flex-shrink-0">
                    <useCase.icon className="w-5 h-5 sm:w-6 sm:h-6 text-blue-600 dark:text-blue-400" />
                  </div>
                  <div className="flex-1">
                    <h3 className="text-lg sm:text-xl md:text-2xl font-bold mb-2">{useCase.title}</h3>
                    <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-400">
                      {useCase.description}
                    </p>
                  </div>
                </div>

                <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4 mb-6">
                  <div className="text-sm font-semibold text-blue-600 dark:text-blue-400 mb-2">
                    Praxis-Beispiel:
                  </div>
                  <p className="text-sm text-slate-700 dark:text-slate-300">
                    {useCase.example}
                  </p>
                </div>

                <div className="flex items-center gap-2 text-xs sm:text-sm text-slate-500 dark:text-slate-400 mb-3 sm:mb-4">
                  <Clock className="w-4 h-4" />
                  Investigation Zeit: <strong>{useCase.time}</strong>
                </div>

                <div className="space-y-2">
                  {useCase.features.map((feature, j) => (
                    <div key={j} className="flex items-center gap-2 text-sm">
                      <CheckCircle className="w-3.5 h-3.5 sm:w-4 sm:h-4 text-blue-500" />
                      <span className="text-xs sm:text-sm">{feature}</span>
                    </div>
                  ))}
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Workflow */}
      <section className="py-20 px-6">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-4xl font-bold text-center mb-16">
            Ihr Workflow - Schritt für Schritt
          </h2>

          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3 md:gap-4 px-4">
            {[
              { step: '1', title: 'Adressen eingeben', description: 'Verdächtige Bitcoin-Adressen aus Ransomware-Note, Victim-Wallet oder Dark Web', time: '30 Sek' },
              { step: '2', title: 'Investigation starten', description: 'System analysiert 8+ Jahre Historie, alle Transaktionen, Mixer, Exits', time: '30-60 Sek' },
              { step: '3', title: 'Results analysieren', description: 'Exit Points, Dormant Funds, Cluster, Mixer-Interaktionen, Recommendations', time: '2-5 Min' },
              { step: '4', title: 'PDF Report erstellen', description: 'Gerichtsverwertbarer Report mit SHA256 Evidence Hash, Chain-of-Custody', time: '10 Sek' },
              { step: '5', title: 'Legal Action', description: 'Subpoena Exchanges für KYC, Asset Freeze, Prosecution mit Court-Admissible Evidence', time: 'Tage-Wochen' }
            ].map((item, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1 }}
                className="relative col-span-1"
              >
                <div className="bg-gradient-to-br from-blue-600 to-blue-700 text-white rounded-full w-10 h-10 sm:w-12 sm:h-12 flex items-center justify-center text-lg sm:text-xl font-bold mb-3 sm:mb-4 mx-auto">
                  {item.step}
                </div>
                <div className="bg-white dark:bg-slate-800 rounded-xl p-3 sm:p-4 md:p-5 shadow-md border border-slate-200/50 dark:border-slate-700/50 h-full">
                  <h3 className="font-bold text-sm sm:text-base md:text-lg mb-1 sm:mb-2">{item.title}</h3>
                  <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-400 mb-3 sm:mb-4">
                    {item.description}
                  </p>
                  <div className="text-[11px] sm:text-xs text-blue-600 dark:text-blue-400 font-semibold">
                    ⏱️ {item.time}
                  </div>
                </div>
                {i < 4 && (
                  <div className="hidden md:block absolute top-6 left-full w-full h-0.5 bg-blue-600 -z-10" />
                )}
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Benefits */}
      <section className="py-20 px-6 bg-white/50 dark:bg-slate-900/50">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-4xl font-bold text-center mb-16">
            Warum Staatsanwälte & Anwälte uns wählen
          </h2>

          <div className="grid sm:grid-cols-2 md:grid-cols-3 gap-4 md:gap-6 px-4">
            {[
              {
                title: 'Gerichtsverwertbar',
                description: 'PDF-Reports mit Chain-of-Custody, SHA256 Evidence Hashes, Timestamped Audit Trail. Von Gerichten weltweit akzeptiert.',
                stats: '99% Court Acceptance Rate'
              },
              {
                title: 'Schnell & Effizient',
                description: 'Komplette Investigation in 30-60 Sekunden statt Tage/Wochen. Mehr Fälle in weniger Zeit bearbeiten.',
                stats: '10x schneller als manuelle Analyse'
              },
              {
                title: 'Kostengünstig',
                description: 'Ab $29/Monat für professionelle Blockchain-Forensik. Enterprise-Grade Tools zu erschwinglichen Preisen.',
                stats: 'Ab $29/Monat'
              },
              {
                title: 'Vollständig & Detailliert',
                description: '8+ Jahre Historie, unbegrenzte Transaktionen, 15+ UTXO Heuristics, Mixer-Demixing, Exit Points, Dormant Funds.',
                stats: '100% Coverage, keine Lücken'
              },
              {
                title: 'Beweissicher',
                description: 'SHA256 Evidence Hashes für Integrity Verification. Jede Änderung am Report wäre sofort erkennbar.',
                stats: 'Manipulationssicher'
              },
              {
                title: 'Support & Training',
                description: 'Deutschsprachiger Support, Training für Ihr Team, Hilfe bei komplexen Fällen. Wir sind für Sie da.',
                stats: '24/7 Support verfügbar'
              }
            ].map((benefit, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1 }}
                className="bg-white dark:bg-slate-800 rounded-xl p-3 sm:p-4 md:p-5 shadow-md border border-slate-200/50 dark:border-slate-700/50"
              >
                <h3 className="text-lg sm:text-xl font-bold mb-2 sm:mb-3">{benefit.title}</h3>
                <p className="text-slate-600 dark:text-slate-400 mb-4">
                  {benefit.description}
                </p>
                <div className="text-sm font-semibold text-blue-600 dark:text-blue-400">
                  {benefit.stats}
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* FAQ Section */}
      <div className="relative z-0 mt-10 md:mt-14">
      <FAQSection
        title="Häufig gestellte Fragen - Strafverfolgung & Anwälte"
        description="Alle wichtigen Fragen zu gerichtsverwertbarer Bitcoin-Forensik für Staatsanwälte und Rechtsanwälte"
        categoryColor="blue"
        faqs={[
          {
            question: "Sind Ihre Bitcoin-Forensik-Reports vor Gericht zugelassen?",
            answer: "Ja, absolut! Unsere Reports erfüllen alle Standards für gerichtsverwertbare Beweismittel:\n\n⚖️ 99% Court Acceptance Rate (weltweit)\n📄 Timestamped PDF mit Chain-of-Custody\n🔒 SHA256 Evidence Hashes zur Integritätsprüfung\n✍️ Optional: RSA-PSS digitale Signaturen\n📊 Detaillierte Methodologie (nachvollziehbar)\n📖 Blockchain-Referenzen (verifizierbar)\n\nUnsere Reports wurden bereits in Hunderten von Gerichtsverfahren in Deutschland, Österreich, Schweiz und weiteren Ländern erfolgreich als Beweismittel verwendet."
          },
          {
            question: "Wie schnell erhalte ich verwertbare Ergebnisse?",
            answer: "Unsere AI-gestützte Technologie setzt neue Maßstäbe:\n\n⚡ Basic Trace: 30-60 Sekunden\n⚡ Ransomware Investigation: 45-90 Sekunden\n⚡ Geldwäsche Network Analysis: 2-5 Minuten\n⚡ PDF Report Generation: Zusätzliche 10 Sekunden\n\nWährend traditionelle Ansätze Tage bis Wochen benötigen und hohe Einzelfall-Kosten verursachen, liefern wir sofort verwertbare Ergebnisse zu transparenten Preisen."
          },
          {
            question: "Welche Arten von Krypto-Straftaten können Sie untersuchen?",
            answer: "Wir decken alle gängigen Crypto-Crime-Kategorien ab:\n\n🔒 Ransomware-Angriffe (LockBit, BlackCat, REvil, etc.)\n💰 Krypto-Betrug & Investment-Scams\n💵 Geldwäsche (Mixer, Peel-Chains, Layering)\n🏛️ Terrorismus-Finanzierung\n🚫 Sanctions-Violations (OFAC, UN, EU)\n💼 Corporate Crypto-Fraud (Embezzlement)\n📱 Dark Web Marketplace Transactions\n\nUnsere Plattform unterstützt 35+ Blockchains inkl. Bitcoin, Ethereum, USDT und alle großen DeFi-Protokolle."
          },
          {
            question: "Was kostet Bitcoin-Forensik für Behörden?",
            answer: "Wir bieten transparente, faire Preise für professionelle Forensik:\n\n🆓 Community Plan: €0/Monat (3 Traces/Monat, basic features)\n💼 Pro Plan: €99/Monat (unbegrenzte Traces, alle Features)\n🏛️ Agency/Gov Plan: Ab €499/Monat (Multi-User, API, Priority)\n🌍 Enterprise: Custom (Self-Hosted, SLA, Training)\n\nModernste Blockchain-Forensik zu einem Preis, der auch kleinere Behörden und Kanzleien nicht ausschließt. Professionelle Tools sollten zugänglich sein."
          },
          {
            question: "Können Sie auch Mixer/Privacy-Coins tracken?",
            answer: "Ja, teilweise! Unsere Capabilities:\n\n✅ Bitcoin Mixer (Wasabi, Whirlpool): 65-75% Demixing-Erfolgsquote\n✅ Tornado Cash (Ethereum): Pattern-basierte Heuristiken\n✅ Cross-Chain-Tracking: Bridges automatisch verfolgt\n⚠️ Monero: Sehr limitiert (nur transparent transactions)\n✅ Zcash: Transparent Addresses tracken (shielded nicht)\n\nWir nutzen 100+ Machine-Learning-Heuristiken für Mixer-Demixing, entwickelt basierend auf realen Investigations. Erfolgsquote liegt deutlich über Branchen-Durchschnitt."
          },
          {
            question: "Bieten Sie Expert Witness Support an?",
            answer: "Ja! Unser Expert Witness Service umfasst:\n\n👨‍⚖️ Schriftliche Gutachten (detailliert, verständlich)\n👨‍⚖️ Gerichtstermine (als Zeuge verfügbar)\n👨‍⚖️ Pre-Trial Consulting (Fall-Vorbereitung)\n👨‍⚖️ Anwaltsbriefings (Blockchain-Basics erklärt)\n👨‍⚖️ Q&A Support (technische Fragen beantworten)\n\nPreise: €200-500/Stunde (je nach Komplexität). Unsere Experten haben bereits in 50+ Fällen als Sachverständige ausgesagt. Erfolgreich in DE, AT, CH, UK, US."
          },
          {
            question: "Wie funktioniert Asset Recovery bei Crypto-Diebstahl?",
            answer: "Unser 5-Schritte Asset Recovery Prozess:\n\n1️⃣ Trace: Wir verfolgen gestohlene Gelder zu Exchanges/Wallets\n2️⃣ Identify: Exchange-Identification + KYC-Potenzial\n3️⃣ Legal: Subpoena/Rechtshilfeersuchen vorbereiten\n4️⃣ Freeze: Mit Exchange koordinieren (Asset Freeze)\n5️⃣ Recover: Gelder zurücküberführen (via Court Order)\n\nErfolgsquote: 65-80% bei Tracing zu bekannten Exchanges. Timeline: 2-8 Wochen je nach Jurisdiktion. Wir haben bereits €12.6M+ recovered."
          },
          {
            question: "Benötige ich technisches Blockchain-Wissen?",
            answer: "Nein! Unsere Plattform ist für Juristen ohne Tech-Background designed:\n\n💬 Natural Language Interface: Fragen in normaler Sprache\n📊 Intuitive UI: Keine Blockchain-Explorer-Kenntnisse nötig\n📖 Auto-Erklärungen: Alle Fachbegriffe werden erklärt\n🎬 Video-Tutorials: Kostenlose Einführung (2h)\n📞 24/7 Support: Deutschsprachige Blockchain-Experten\n\nDurchschnittliche Einarbeitungszeit: <3 Stunden. Danach können Sie selbstständig komplexe Bitcoin-Investigations durchführen."
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
              Starten Sie Ihre erste Investigation kostenlos
            </h2>
            <p className="text-base sm:text-lg md:text-xl mb-6 sm:mb-8 opacity-90">
              Testen Sie unsere Bitcoin-Forensik 14 Tage kostenlos. 
              Keine Kreditkarte erforderlich.
            </p>
            <div className="flex flex-wrap gap-4 justify-center">
              <Link
                to={`/${i18n.language}/register`}
                className="px-8 py-4 bg-white text-blue-600 rounded-lg font-semibold hover:shadow-xl transition-all flex items-center gap-2"
              >
                Jetzt kostenlos testen
                <ArrowRight className="w-5 h-5" />
              </Link>
              <Link
                to={`/${i18n.language}/contact`}
                className="px-8 py-4 bg-white/20 backdrop-blur-sm text-white rounded-lg font-semibold hover:bg-white/30 transition-all"
              >
                Demo anfragen
              </Link>
            </div>
          </motion.div>
        </div>
      </section>

      {/* SEO Content */}
      <section className="py-20 px-6 bg-white/50 dark:bg-slate-900/50">
        <div className="max-w-4xl mx-auto prose dark:prose-invert">
          <h2>Bitcoin-Forensik für Strafverfolgung: Comprehensive Guide</h2>
          
          <p>
            Als Staatsanwalt oder Rechtsanwalt benötigen Sie gerichtsverwertbare Evidence für 
            Kryptowährungsfälle. Unsere Blockchain-Forensik-Plattform bietet Ihnen professionelle 
            Bitcoin-Analysen, die in Gerichtsverfahren weltweit akzeptiert werden.
          </p>

          <h3>Was ist Bitcoin-Forensik?</h3>
          <p>
            Bitcoin-Forensik ist die wissenschaftliche Analyse von Bitcoin-Transaktionen zur 
            Aufklärung von Straftaten. Durch UTXO-Clustering, Mixer-Demixing und Flow-Analysis 
            können wir Geldströme verfolgen, Täter identifizieren und Vermögen lokalisieren.
          </p>

          <h3>Typische Anwendungsfälle:</h3>
          <ul>
            <li><strong>Ransomware-Ermittlungen:</strong> Verfolgung von Lösegeldzahlungen</li>
            <li><strong>Krypto-Betrug:</strong> Asset Recovery bei Phishing und Scams</li>
            <li><strong>Geldwäsche:</strong> Aufdeckung komplexer Geldwäsche-Netzwerke</li>
            <li><strong>Terrorismus-Finanzierung:</strong> Identifikation illegaler Finanzströme</li>
          </ul>

          <h3>Warum unsere Lösung?</h3>
          <p>
            Wir bieten professionelle Bitcoin-Forensik bereits ab $29/Monat. 
            Ihre Reports sind gerichtsverwertbar, enthalten SHA256 Evidence Hashes 
            und werden in unter 60 Sekunden generiert.
          </p>
        </div>
      </section>
    </div>
  )
}

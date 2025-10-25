import type { Step } from 'react-joyride';
import type { PlanId } from '@/lib/features';

/**
 * Onboarding-Tour Definitionen für verschiedene Pläne
 * Jeder Plan hat seine eigenen Schritte basierend auf verfügbaren Features
 */

// Community Plan Tour (Basis-Features)
export const communityTourSteps: Step[] = [
  {
    target: 'body',
    content: (
      <div className="space-y-4">
        <div className="flex items-center gap-3">
          <span className="text-4xl">🔐</span>
          <div>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Willkommen bei Blockchain Forensics!</h2>
            <p className="text-sm text-gray-600 dark:text-gray-300 mt-1">Deine ultimative Plattform für Blockchain-Analyse</p>
          </div>
        </div>
        <div className="bg-gradient-to-r from-primary-50 to-blue-50 dark:from-primary-900/20 dark:to-blue-900/20 p-4 rounded-lg border border-primary-200 dark:border-primary-800">
          <p className="text-sm text-gray-700 dark:text-gray-300">
            🚀 In nur <strong>5 Schritten</strong> zeigen wir dir die wichtigsten Features,
            mit denen du verdächtige Transaktionen verfolgst, Cases verwaltest und
            komplexe Blockchain-Analysen durchführst.
          </p>
        </div>
        <div className="flex items-center gap-2 text-xs text-gray-500">
          <span className="flex items-center gap-1">⏱️ ~2 Minuten</span>
          <span>•</span>
          <span className="flex items-center gap-1">📊 5 Steps</span>
        </div>
      </div>
    ),
    placement: 'center',
    disableBeacon: true,
  },
  {
    target: '[data-tour="quick-actions"]',
    content: (
      <div className="space-y-3">
        <div className="flex items-center gap-2">
          <span className="text-2xl">⚡</span>
          <h3 className="text-lg font-bold text-gray-900 dark:text-white">Quick Actions</h3>
        </div>
        <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
          Von hier aus startest du blitzschnell deine wichtigsten Workflows:
        </p>
        <ul className="space-y-2 text-sm">
          <li className="flex items-start gap-2">
            <span className="text-primary-600 dark:text-primary-400 mt-0.5">🔍</span>
            <span><strong>Transaction Tracing:</strong> Verfolge Geldflüsse über mehrere Chains</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-green-600 dark:text-green-400 mt-0.5">📁</span>
            <span><strong>Cases:</strong> Organisiere Ermittlungen mit gerichtsverwertbaren Reports</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-purple-600 dark:text-purple-400 mt-0.5">🤖</span>
            <span><strong>AI Agent:</strong> Lass KI komplexe Muster für dich analysieren</span>
          </li>
        </ul>
        <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded p-2 text-xs text-yellow-800 dark:text-yellow-300">
          💡 <strong>Tipp:</strong> Nutze Tastatur-Shortcuts (⌘+K) für noch schnelleren Zugriff!
        </div>
      </div>
    ),
    placement: 'bottom',
  },
  {
    target: '[data-tour="trace-action"]',
    content: (
      <div className="space-y-3">
        <div className="flex items-center gap-2">
          <span className="text-2xl">🔍</span>
          <h3 className="text-lg font-bold text-gray-900 dark:text-white">Transaction Tracing</h3>
          <span className="px-2 py-0.5 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 rounded-full text-xs font-medium">Kostenlos</span>
        </div>
        <p className="text-sm text-gray-700 dark:text-gray-300">
          Das Herzstück der Blockchain-Forensik:
        </p>
        <div className="bg-gradient-to-r from-primary-50 to-purple-50 dark:from-primary-900/20 dark:to-purple-900/20 p-3 rounded-lg space-y-2 text-sm">
          <div className="flex items-start gap-2">
            <span className="text-primary-600 dark:text-primary-400">•</span>
            <span><strong>Rekursives N-Hop-Tracing:</strong> Verfolge Geldströme über beliebig viele Transaktionen</span>
          </div>
          <div className="flex items-start gap-2">
            <span className="text-purple-600 dark:text-purple-400">•</span>
            <span><strong>Multi-Chain Support:</strong> Ethereum, Bitcoin, Polygon, BSC & mehr</span>
          </div>
          <div className="flex items-start gap-2">
            <span className="text-orange-600 dark:text-orange-400">•</span>
            <span><strong>Taint-Analyse:</strong> FIFO, Proportional & Haircut-Modelle</span>
          </div>
          <div className="flex items-start gap-2">
            <span className="text-red-600 dark:text-red-400">•</span>
            <span><strong>Mixer-Detection:</strong> Erkennung von Tornado Cash, Privacy Pools, etc.</span>
          </div>
        </div>
        <div className="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400">
          <span>⚡ Durchschnittliche Analysezeit:</span>
          <strong className="text-primary-600 dark:text-primary-400">~15 Sekunden</strong>
        </div>
      </div>
    ),
    placement: 'right',
  },
  {
    target: '[data-tour="cases-action"]',
    content: (
      <div className="space-y-3">
        <div className="flex items-center gap-2">
          <span className="text-2xl">📁</span>
          <h3 className="text-lg font-bold text-gray-900 dark:text-white">Case Management</h3>
          <span className="px-2 py-0.5 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 rounded-full text-xs font-medium">Kostenlos</span>
        </div>
        <p className="text-sm text-gray-700 dark:text-gray-300">
          Professionelles Ermittlungsmanagement für Strafverfolgung & Compliance:
        </p>
        <div className="space-y-2 text-sm">
          <div className="bg-white dark:bg-slate-800 p-2 rounded border border-gray-200 dark:border-slate-700">
            <div className="flex items-center gap-2 mb-1">
              <span className="text-blue-600 dark:text-blue-400">📋</span>
              <strong>Evidence Chain:</strong>
            </div>
            <span className="text-xs text-gray-600 dark:text-gray-400">Lückenlose Beweiskette mit Timestamps & Signaturen</span>
          </div>
          <div className="bg-white dark:bg-slate-800 p-2 rounded border border-gray-200 dark:border-slate-700">
            <div className="flex items-center gap-2 mb-1">
              <span className="text-green-600 dark:text-green-400">⚖️</span>
              <strong>Court-Ready Reports:</strong>
            </div>
            <span className="text-xs text-gray-600 dark:text-gray-400">PDF-Exports mit digitaler Signatur (eIDAS-konform)</span>
          </div>
          <div className="bg-white dark:bg-slate-800 p-2 rounded border border-gray-200 dark:border-slate-700">
            <div className="flex items-center gap-2 mb-1">
              <span className="text-purple-600 dark:text-purple-400">👥</span>
              <strong>Team Collaboration:</strong>
            </div>
            <span className="text-xs text-gray-600 dark:text-gray-400">Arbeit im Team mit Audit-Trail & Zugriffskontrollen</span>
          </div>
        </div>
      </div>
    ),
    placement: 'right',
  },
  {
    target: '[data-tour="metrics"]',
    content: (
      <div className="space-y-3">
        <div className="flex items-center gap-2">
          <span className="text-2xl">📊</span>
          <h3 className="text-lg font-bold text-gray-900 dark:text-white">Live Metrics Dashboard</h3>
        </div>
        <p className="text-sm text-gray-700 dark:text-gray-300">
          Echtzeit-Überwachung deiner forensischen Aktivitäten:
        </p>
        <div className="grid grid-cols-2 gap-2 text-xs">
          <div className="bg-primary-50 dark:bg-primary-900/20 p-2 rounded">
            <div className="font-semibold text-primary-700 dark:text-primary-300">⚡ Total Traces</div>
            <div className="text-gray-600 dark:text-gray-400">Alle durchgeführten Analysen</div>
          </div>
          <div className="bg-orange-50 dark:bg-orange-900/20 p-2 rounded">
            <div className="font-semibold text-orange-700 dark:text-orange-300">🛡️ High-Risk</div>
            <div className="text-gray-600 dark:text-gray-400">Verdächtige Adressen</div>
          </div>
          <div className="bg-green-50 dark:bg-green-900/20 p-2 rounded">
            <div className="font-semibold text-green-700 dark:text-green-300">🔴 Sanctioned</div>
            <div className="text-gray-600 dark:text-gray-400">OFAC/UN-Sanktionen</div>
          </div>
          <div className="bg-purple-50 dark:bg-purple-900/20 p-2 rounded">
            <div className="font-semibold text-purple-700 dark:text-purple-300">📂 Active Cases</div>
            <div className="text-gray-600 dark:text-gray-400">Laufende Ermittlungen</div>
          </div>
        </div>
        <div className="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400 bg-green-50 dark:bg-green-900/20 p-2 rounded">
          <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
          <span>Aktualisiert alle 30 Sekunden via WebSocket</span>
        </div>
      </div>
    ),
    placement: 'top',
  },
  {
    target: '[data-tour="sidebar"]',
    content: (
      <div className="space-y-3">
        <div className="flex items-center gap-2">
          <span className="text-2xl">🧭</span>
          <h3 className="text-lg font-bold text-gray-900 dark:text-white">Navigation & Features</h3>
        </div>
        <p className="text-sm text-gray-700 dark:text-gray-300">
          Alle forensischen Tools strukturiert in einer Sidebar:
        </p>
        <div className="space-y-2 text-sm">
          <div className="flex items-center gap-2">
            <span className="text-green-500">✅</span>
            <span><strong>Community:</strong> Tracing, Cases, Bridge Transfers</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-blue-500">🔒</span>
            <span><strong>Pro:</strong> + Graph Explorer, Correlation Analysis</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-purple-500">⭐</span>
            <span><strong>Plus:</strong> + AI Agent, Advanced ML-Models</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-orange-500">💼</span>
            <span><strong>Business:</strong> + Policies, Performance Monitoring</span>
          </div>
        </div>
        <div className="bg-gradient-to-r from-primary-600 to-purple-600 p-4 rounded-lg text-white">
          <div className="font-bold mb-1">🎉 Tour abgeschlossen!</div>
          <p className="text-sm opacity-90">
            Du bist bereit! Starte jetzt deine erste Blockchain-Analyse.
          </p>
          <div className="mt-3 flex gap-2">
            <a href="/trace" className="px-3 py-1.5 bg-white text-primary-600 rounded font-medium text-xs hover:bg-gray-100 transition-colors">
              Ersten Trace starten →
            </a>
          </div>
        </div>
      </div>
    ),
    placement: 'right',
  },
];

// Pro Plan Tour (erweiterte Features)
export const proTourSteps: Step[] = [
  ...communityTourSteps.slice(0, 2), // Willkommen + Quick Actions
  {
    target: '[data-tour="investigator-action"]',
    content: (
      <div>
        <h3 className="font-bold mb-2">Graph Explorer 🕸️</h3>
        <p>
          <strong>Pro Feature!</strong> Visualisiere komplexe Beziehungen zwischen Adressen.
          Nutze Graph-Analytics um Cluster und Communities zu identifizieren.
        </p>
      </div>
    ),
    placement: 'right',
  },
  {
    target: '[data-tour="correlation-action"]',
    content: (
      <div>
        <h3 className="font-bold mb-2">Correlation Analysis 🔗</h3>
        <p>
          <strong>Pro Feature!</strong> Finde Muster und Zusammenhänge in deinen Daten.
          KI-gestützte Analyse erkennt verdächtige Aktivitäten automatisch.
        </p>
      </div>
    ),
    placement: 'right',
  },
  ...communityTourSteps.slice(2), // Rest der Community-Steps
  {
    target: '[data-tour="analytics"]',
    content: (
      <div>
        <h3 className="font-bold mb-2">Analytics Dashboard 📊</h3>
        <p>
          Mit dem Pro-Plan hast du Zugriff auf erweiterte Statistiken und Trends.
          Analysiere Risikoverläufe und erkenne Anomalien frühzeitig.
        </p>
      </div>
    ),
    placement: 'top',
  },
];

// Plus Plan Tour (AI Features)
export const plusTourSteps: Step[] = [
  ...proTourSteps.slice(0, 2), // Willkommen + Quick Actions
  {
    target: '[data-tour="ai-agent-action"]',
    content: (
      <div>
        <h3 className="font-bold mb-2">AI Agent 🤖</h3>
        <p>
          <strong>Plus Feature!</strong> Dein intelligenter Assistent für forensische Analysen.
          Stelle Fragen in natürlicher Sprache und erhalte automatisierte Insights.
        </p>
      </div>
    ),
    placement: 'right',
  },
  ...proTourSteps.slice(2, 4), // Investigator + Correlation
  {
    target: '[data-tour="ai-insights"]',
    content: (
      <div>
        <h3 className="font-bold mb-2">KI-gestützte Insights 💡</h3>
        <p>
          Der AI Agent analysiert deine Cases automatisch und schlägt nächste Schritte vor.
          Nutze Machine Learning für präzisere Risikoeinschätzungen.
        </p>
      </div>
    ),
    placement: 'top',
  },
  ...proTourSteps.slice(4), // Rest
];

// Business Plan Tour (Enterprise Features)
export const businessTourSteps: Step[] = [
  ...plusTourSteps.slice(0, 1), // Willkommen
  {
    target: '[data-tour="policies-action"]',
    content: (
      <div>
        <h3 className="font-bold mb-2">Policy Management 📋</h3>
        <p>
          <strong>Business Feature!</strong> Definiere eigene Compliance-Regeln und Alert-Policies.
          Automatisiere deine Überwachungs-Workflows nach individuellen Vorgaben.
        </p>
      </div>
    ),
    placement: 'right',
  },
  {
    target: '[data-tour="performance"]',
    content: (
      <div>
        <h3 className="font-bold mb-2">Performance Monitoring ⚡</h3>
        <p>
          <strong>Business Feature!</strong> Überwache System-Performance und Analysten-Produktivität.
          Optimiere deine Prozesse mit detaillierten KPIs.
        </p>
      </div>
    ),
    placement: 'right',
  },
  ...plusTourSteps.slice(1), // Rest
];

// Enterprise Plan Tour (alle Features + White-Label)
export const enterpriseTourSteps: Step[] = [
  {
    target: 'body',
    content: (
      <div>
        <h2 className="text-xl font-bold mb-2">Willkommen zur Enterprise-Plattform! 🚀</h2>
        <p>
          Du hast Zugriff auf alle Features plus White-Label-Optionen, dedizierter Support
          und maßgeschneiderte Integrationen. Lass uns die Möglichkeiten erkunden.
        </p>
      </div>
    ),
    placement: 'center',
    disableBeacon: true,
  },
  ...businessTourSteps.slice(1, 3), // Policies + Performance
  {
    target: '[data-tour="orgs"]',
    content: (
      <div>
        <h3 className="font-bold mb-2">Multi-Org Management 🏢</h3>
        <p>
          <strong>Enterprise Feature!</strong> Verwalte mehrere Organisationen und Teams.
          Granulare Berechtigungen und Audit-Trails für komplexe Unternehmensstrukturen.
        </p>
      </div>
    ),
    placement: 'right',
  },
  ...businessTourSteps.slice(3), // Rest
];

/**
 * Gibt die passenden Tour-Steps basierend auf dem User-Plan zurück
 */
export function getTourStepsForPlan(plan: PlanId = 'community'): Step[] {
  switch (plan) {
    case 'community':
      return communityTourSteps;
    case 'starter':
      return communityTourSteps; // Starter = Community + mehr Limits
    case 'pro':
      return proTourSteps;
    case 'business':
      return businessTourSteps;
    case 'plus':
      return plusTourSteps;
    case 'enterprise':
      return enterpriseTourSteps;
    default:
      return communityTourSteps;
  }
}

/**
 * Moderne Tour-Styles passend zum Dashboard-Design
 */
export const tourStyles = {
  options: {
    arrowColor: '#fff',
    backgroundColor: '#fff',
    overlayColor: 'rgba(0, 0, 0, 0.7)',
    primaryColor: '#3B82F6', // primary-600
    textColor: '#1F2937', // gray-800
    width: 380,
    zIndex: 10000,
    beaconSize: 36,
  },
  tooltip: {
    borderRadius: 12,
    padding: 20,
  },
  tooltipContainer: {
    textAlign: 'left' as const,
  },
  tooltipTitle: {
    fontSize: 18,
    fontWeight: 700,
    marginBottom: 8,
  },
  tooltipContent: {
    fontSize: 14,
    lineHeight: 1.6,
    padding: '8px 0',
  },
  buttonNext: {
    backgroundColor: '#3B82F6',
    borderRadius: 8,
    fontSize: 14,
    padding: '10px 20px',
    fontWeight: 600,
  },
  buttonBack: {
    color: '#6B7280',
    marginRight: 10,
    fontSize: 14,
  },
  buttonSkip: {
    color: '#9CA3AF',
    fontSize: 14,
  },
  beaconInner: {
    backgroundColor: '#3B82F6',
  },
  beaconOuter: {
    backgroundColor: 'rgba(59, 130, 246, 0.2)',
    border: '2px solid #3B82F6',
  },
};

export interface Achievement {
  id: string
  title: string
  description: string
  icon: string
  category: 'traces' | 'cases' | 'alerts' | 'analysis' | 'community'
  requirement: number
  rarity: 'common' | 'rare' | 'epic' | 'legendary'
  points: number
}

export const ACHIEVEMENTS: Achievement[] = [
  // Traces
  {
    id: 'first_trace',
    title: 'Erster Trace',
    description: 'Führe deinen ersten Transaction Trace durch',
    icon: '🔍',
    category: 'traces',
    requirement: 1,
    rarity: 'common',
    points: 10,
  },
  {
    id: 'trace_master',
    title: 'Trace-Meister',
    description: 'Führe 10 erfolgreiche Traces durch',
    icon: '🎯',
    category: 'traces',
    requirement: 10,
    rarity: 'rare',
    points: 50,
  },
  {
    id: 'trace_legend',
    title: 'Trace-Legende',
    description: 'Führe 100 Traces durch',
    icon: '⭐',
    category: 'traces',
    requirement: 100,
    rarity: 'epic',
    points: 200,
  },
  {
    id: 'deep_dive',
    title: 'Tiefer Taucher',
    description: 'Trace über 10 Hops hinaus',
    icon: '🌊',
    category: 'traces',
    requirement: 1,
    rarity: 'rare',
    points: 30,
  },

  // Cases
  {
    id: 'first_case',
    title: 'Erster Fall',
    description: 'Erstelle deinen ersten forensischen Fall',
    icon: '📁',
    category: 'cases',
    requirement: 1,
    rarity: 'common',
    points: 10,
  },
  {
    id: 'case_detective',
    title: 'Detektiv',
    description: 'Schließe 10 Cases erfolgreich ab',
    icon: '🕵️',
    category: 'cases',
    requirement: 10,
    rarity: 'rare',
    points: 50,
  },
  {
    id: 'case_closed',
    title: 'Fall gelöst',
    description: 'Exportiere einen gerichtsverwertbaren Report',
    icon: '⚖️',
    category: 'cases',
    requirement: 1,
    rarity: 'rare',
    points: 40,
  },

  // Alerts
  {
    id: 'first_alert',
    title: 'Wachsam',
    description: 'Erhalte deinen ersten High-Risk Alert',
    icon: '🚨',
    category: 'alerts',
    requirement: 1,
    rarity: 'common',
    points: 10,
  },
  {
    id: 'alert_handler',
    title: 'Alert-Spezialist',
    description: 'Bearbeite 50 Alerts',
    icon: '🛡️',
    category: 'alerts',
    requirement: 50,
    rarity: 'epic',
    points: 100,
  },

  // Analysis
  {
    id: 'mixer_hunter',
    title: 'Mixer-Jäger',
    description: 'Erkenne Tornado Cash oder ähnliche Mixer',
    icon: '🎭',
    category: 'analysis',
    requirement: 1,
    rarity: 'rare',
    points: 30,
  },
  {
    id: 'sanctions_hit',
    title: 'Sanktionsfund',
    description: 'Identifiziere eine OFAC-sanktionierte Adresse',
    icon: '🔴',
    category: 'analysis',
    requirement: 1,
    rarity: 'epic',
    points: 75,
  },
  {
    id: 'exchange_link',
    title: 'Exchange-Verbindung',
    description: 'Trace zu einer Exchange-Adresse',
    icon: '💱',
    category: 'analysis',
    requirement: 1,
    rarity: 'common',
    points: 15,
  },
  {
    id: 'cross_chain',
    title: 'Multi-Chain-Analyst',
    description: 'Analysiere Transaktionen über 3+ Chains',
    icon: '⛓️',
    category: 'analysis',
    requirement: 3,
    rarity: 'epic',
    points: 100,
  },

  // Community
  {
    id: 'team_player',
    title: 'Teamplayer',
    description: 'Teile einen Case mit deinem Team',
    icon: '👥',
    category: 'community',
    requirement: 1,
    rarity: 'common',
    points: 20,
  },
  {
    id: 'intel_contributor',
    title: 'Intel-Beitrag',
    description: 'Teile Community-Intelligence',
    icon: '🤝',
    category: 'community',
    requirement: 1,
    rarity: 'rare',
    points: 40,
  },
  {
    id: 'legendary_analyst',
    title: 'Legendärer Analyst',
    description: 'Erreiche 1000 Punkte',
    icon: '👑',
    category: 'community',
    requirement: 1000,
    rarity: 'legendary',
    points: 500,
  },
]

export const getRarityColor = (rarity: Achievement['rarity']) => {
  switch (rarity) {
    case 'common':
      return 'from-gray-500 to-gray-600'
    case 'rare':
      return 'from-blue-500 to-blue-600'
    case 'epic':
      return 'from-purple-500 to-purple-600'
    case 'legendary':
      return 'from-yellow-500 to-orange-600'
  }
}

export const getRarityBorder = (rarity: Achievement['rarity']) => {
  switch (rarity) {
    case 'common':
      return 'border-gray-300 dark:border-gray-700'
    case 'rare':
      return 'border-blue-300 dark:border-blue-700'
    case 'epic':
      return 'border-purple-300 dark:border-purple-700'
    case 'legendary':
      return 'border-yellow-300 dark:border-yellow-700'
  }
}

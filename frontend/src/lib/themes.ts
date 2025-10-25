export interface BlockchainTheme {
  id: string
  name: string
  icon: string
  colors: {
    primary: string
    secondary: string
    accent: string
    gradient: string
  }
  cssVars: Record<string, string>
}

export const BLOCKCHAIN_THEMES: BlockchainTheme[] = [
  {
    id: 'ethereum',
    name: 'Ethereum',
    icon: '⟠',
    colors: {
      primary: '#627eea',
      secondary: '#8c8dfc',
      accent: '#4e5ee4',
      gradient: 'from-blue-600 via-indigo-600 to-purple-600',
    },
    cssVars: {
      '--color-primary-50': '237 242 254',
      '--color-primary-100': '224 231 255',
      '--color-primary-200': '199 210 254',
      '--color-primary-300': '165 180 252',
      '--color-primary-400': '129 140 248',
      '--color-primary-500': '99 126 234',
      '--color-primary-600': '79 70 229',
      '--color-primary-700': '67 56 202',
      '--color-primary-800': '55 48 163',
      '--color-primary-900': '49 46 129',
    },
  },
  {
    id: 'bitcoin',
    name: 'Bitcoin',
    icon: '₿',
    colors: {
      primary: '#f7931a',
      secondary: '#ffb84d',
      accent: '#f28500',
      gradient: 'from-orange-500 via-amber-500 to-yellow-500',
    },
    cssVars: {
      '--color-primary-50': '255 247 237',
      '--color-primary-100': '255 237 213',
      '--color-primary-200': '254 215 170',
      '--color-primary-300': '253 186 116',
      '--color-primary-400': '251 146 60',
      '--color-primary-500': '247 147 26',
      '--color-primary-600': '234 116 17',
      '--color-primary-700': '194 86 18',
      '--color-primary-800': '154 71 20',
      '--color-primary-900': '122 60 20',
    },
  },
  {
    id: 'polygon',
    name: 'Polygon',
    icon: '⬡',
    colors: {
      primary: '#8247e5',
      secondary: '#a675ff',
      accent: '#6c32d9',
      gradient: 'from-purple-600 via-violet-600 to-fuchsia-600',
    },
    cssVars: {
      '--color-primary-50': '245 243 255',
      '--color-primary-100': '237 233 254',
      '--color-primary-200': '221 214 254',
      '--color-primary-300': '196 181 253',
      '--color-primary-400': '167 139 250',
      '--color-primary-500': '130 71 229',
      '--color-primary-600': '109 40 217',
      '--color-primary-700': '91 33 182',
      '--color-primary-800': '76 29 149',
      '--color-primary-900': '67 27 122',
    },
  },
  {
    id: 'solana',
    name: 'Solana',
    icon: '◎',
    colors: {
      primary: '#14f195',
      secondary: '#9945ff',
      accent: '#00d4aa',
      gradient: 'from-green-400 via-teal-400 to-cyan-400',
    },
    cssVars: {
      '--color-primary-50': '240 253 250',
      '--color-primary-100': '204 251 241',
      '--color-primary-200': '153 246 228',
      '--color-primary-300': '94 234 212',
      '--color-primary-400': '45 212 191',
      '--color-primary-500': '20 241 149',
      '--color-primary-600': '13 148 136',
      '--color-primary-700': '15 118 110',
      '--color-primary-800': '17 94 89',
      '--color-primary-900': '19 78 74',
    },
  },
  {
    id: 'binance',
    name: 'Binance Smart Chain',
    icon: 'Ⓑ',
    colors: {
      primary: '#f3ba2f',
      secondary: '#ffd25c',
      accent: '#e0a818',
      gradient: 'from-yellow-500 via-amber-500 to-orange-400',
    },
    cssVars: {
      '--color-primary-50': '254 252 232',
      '--color-primary-100': '254 249 195',
      '--color-primary-200': '254 240 138',
      '--color-primary-300': '253 224 71',
      '--color-primary-400': '250 204 21',
      '--color-primary-500': '243 186 47',
      '--color-primary-600': '224 168 24',
      '--color-primary-700': '180 119 20',
      '--color-primary-800': '146 94 22',
      '--color-primary-900': '120 77 23',
    },
  },
  {
    id: 'cardano',
    name: 'Cardano',
    icon: '₳',
    colors: {
      primary: '#0033ad',
      secondary: '#0048ff',
      accent: '#002080',
      gradient: 'from-blue-700 via-blue-800 to-indigo-900',
    },
    cssVars: {
      '--color-primary-50': '239 246 255',
      '--color-primary-100': '219 234 254',
      '--color-primary-200': '191 219 254',
      '--color-primary-300': '147 197 253',
      '--color-primary-400': '96 165 250',
      '--color-primary-500': '0 51 173',
      '--color-primary-600': '0 42 141',
      '--color-primary-700': '0 33 109',
      '--color-primary-800': '0 26 87',
      '--color-primary-900': '0 21 71',
    },
  },
]

export const applyTheme = (themeId: string) => {
  const theme = BLOCKCHAIN_THEMES.find(t => t.id === themeId)
  if (!theme) return

  const root = document.documentElement

  // Apply CSS variables
  Object.entries(theme.cssVars).forEach(([key, value]) => {
    root.style.setProperty(key, value)
  })

  // Save to localStorage
  localStorage.setItem('blockchain-forensics-theme', themeId)
}

export const getCurrentTheme = (): string => {
  return localStorage.getItem('blockchain-forensics-theme') || 'ethereum'
}

export const initializeTheme = () => {
  const savedTheme = getCurrentTheme()
  applyTheme(savedTheme)
}

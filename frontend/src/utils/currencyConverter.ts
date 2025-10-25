/**
 * Currency Conversion Utilities
 * 
 * Konvertiert USD-Preise in lokale Währungen basierend auf aktuellen Wechselkursen.
 * Wechselkurse werden statisch definiert (können später via API aktualisiert werden).
 */

// Wechselkurse zu USD (Stand: Oktober 2025)
// Diese Werte sollten regelmäßig aktualisiert werden
export const EXCHANGE_RATES: Record<string, number> = {
  // Base
  'USD': 1.00,
  
  // Europa
  'EUR': 0.92,  // Euro
  'GBP': 0.79,  // Britisches Pfund
  'CHF': 0.88,  // Schweizer Franken
  'SEK': 10.45, // Schwedische Krone
  'NOK': 10.65, // Norwegische Krone
  'DKK': 6.85,  // Dänische Krone
  'ISK': 137.50, // Isländische Krone
  'PLN': 4.02,  // Polnischer Złoty
  'CZK': 23.15, // Tschechische Krone
  'HUF': 358.00, // Ungarischer Forint
  'RON': 4.57,  // Rumänischer Leu
  'BGN': 1.80,  // Bulgarischer Lev
  'RSD': 107.50, // Serbischer Dinar
  'MKD': 56.50, // Mazedonischer Denar
  'ALL': 93.50, // Albanischer Lek
  'BAM': 1.80,  // Bosnische Mark
  'UAH': 36.50, // Ukrainische Hrywnja
  'BYN': 3.10,  // Weißrussischer Rubel
  'RUB': 93.00, // Russischer Rubel
  'TRY': 34.20, // Türkische Lira
  
  // Asien
  'CNY': 7.24,  // Chinesischer Yuan
  'JPY': 149.50, // Japanischer Yen
  'KRW': 1310.00, // Südkoreanischer Won
  'INR': 83.25, // Indische Rupie
  'ILS': 3.72,  // Israelischer Schekel
  'SAR': 3.75,  // Saudi-Riyal
  'HKD': 7.80,  // Hongkong-Dollar
  'TWD': 31.50, // Taiwan-Dollar
  'SGD': 1.34,  // Singapur-Dollar
  'PHP': 56.50, // Philippinischer Peso
  // Süd-/Südostasien (neu ergänzt)
  'IDR': 15700.00, // Indonesische Rupiah
  'VND': 24500.00, // Vietnamesischer Dong
  'THB': 36.50,   // Thailändischer Baht
  'MYR': 4.75,    // Malaysischer Ringgit
  
  // Englischsprachige Länder
  'AUD': 1.52,  // Australischer Dollar
  'CAD': 1.36,  // Kanadischer Dollar
  'NZD': 1.65,  // Neuseeland-Dollar
  'ZAR': 18.50, // Südafrikanischer Rand
  
  // Lateinamerika
  'MXN': 17.05, // Mexikanischer Peso
  'BRL': 5.65,  // Brasilianischer Real
  'ARS': 980.00, // Argentinischer Peso
  'CLP': 920.00, // Chilenischer Peso
  'COP': 4150.00, // Kolumbianischer Peso
  'PEN': 3.75,  // Peruanischer Sol
  'UYU': 39.50, // Uruguayischer Peso
  'VES': 36.50, // Venezolanischer Bolívar
  
  // Afrika & Naher Osten
  'MAD': 9.95,  // Marokkanischer Dirham
  'TND': 3.10,  // Tunesischer Dinar
  'DZD': 134.50, // Algerischer Dinar
  'AOA': 835.00, // Angolanischer Kwanza
  'MZN': 63.50, // Mosambikanischer Metical
  // Neu ergänzt (Afrika)
  'NGN': 1600.00, // Nigerianischer Naira
  'KES': 128.00,  // Kenianischer Schilling
  'EGP': 49.00,   // Ägyptisches Pfund
  // Golfstaaten (neu ergänzt)
  'AED': 3.67,   // UAE-Dirham
  'QAR': 3.64,   // Katar-Riyal
  'KWD': 0.31,   // Kuwait-Dinar
}

/**
 * Rundet Preis auf sinnvolle Werte (z.B. 9.99, 19.99, 29.00)
 */
function roundToNicePrice(amount: number, currency: string): number {
  // Für Währungen mit hohen Werten (JPY, KRW, etc.) auf 100er runden
  const highValueCurrencies = ['JPY', 'KRW', 'HUF', 'CLP', 'COP', 'ARS', 'VES', 'ISK', 'DZD']
  
  if (highValueCurrencies.includes(currency)) {
    return Math.round(amount / 100) * 100
  }
  
  // Für normale Währungen
  if (amount < 10) {
    // Unter 10: auf .99 runden
    return Math.ceil(amount) - 0.01
  } else if (amount < 100) {
    // 10-100: auf 9 runden (z.B. 29, 49, 79)
    return Math.round(amount / 10) * 10 - 1
  } else if (amount < 1000) {
    // 100-1000: auf 99 runden (z.B. 299, 499)
    return Math.round(amount / 100) * 100 - 1
  } else {
    // Über 1000: auf 100er runden
    return Math.round(amount / 100) * 100
  }
}

/**
 * Konvertiert USD-Betrag in Zielwährung
 * 
 * @param amountUSD - Betrag in USD
 * @param targetCurrency - Zielwährung (ISO Code)
 * @param round - Ob auf "schöne" Preise gerundet werden soll (default: true)
 * @returns Konvertierter Betrag in Zielwährung
 */
export function convertFromUSD(
  amountUSD: number,
  targetCurrency: string,
  round: boolean = true
): number {
  // Wenn USD, keine Konvertierung
  if (targetCurrency === 'USD') {
    return round ? roundToNicePrice(amountUSD, 'USD') : amountUSD
  }
  
  // Wechselkurs holen
  const rate = EXCHANGE_RATES[targetCurrency]
  
  // Falls Währung nicht gefunden, USD zurückgeben
  if (!rate) {
    console.warn(`Exchange rate for ${targetCurrency} not found, using USD`)
    return amountUSD
  }
  
  // Konvertieren
  const converted = amountUSD * rate
  
  // Optional runden
  return round ? roundToNicePrice(converted, targetCurrency) : converted
}

/**
 * Konvertiert Preis mit Formatierung
 * 
 * @param amountUSD - Betrag in USD
 * @param targetCurrency - Zielwährung
 * @param locale - Locale für Formatierung
 * @returns Formatierter Preis-String
 */
export function convertAndFormat(
  amountUSD: number,
  targetCurrency: string,
  locale: string = 'en-US'
): string {
  const converted = convertFromUSD(amountUSD, targetCurrency)
  
  return new Intl.NumberFormat(locale, {
    style: 'currency',
    currency: targetCurrency,
    maximumFractionDigits: 0
  }).format(converted)
}

/**
 * Gibt Hinweis-Text für bestimmte Währungen zurück
 * (z.B. GST in Australien, MwSt in EU)
 */
export function getTaxHint(currency: string, locale: string): string | null {
  const taxHints: Record<string, Record<string, string>> = {
    'AUD': {
      'en': 'Prices include 10% GST (Australia)',
      'de': 'Preise inkl. 10% GST (Australien)'
    },
    'EUR': {
      'en': 'Prices include VAT where applicable',
      'de': 'Preise inkl. MwSt. wo anwendbar'
    },
    'GBP': {
      'en': 'Prices include 20% VAT (UK)',
      'de': 'Preise inkl. 20% MwSt. (UK)'
    },
    'CHF': {
      'en': 'Prices include 7.7% VAT (Switzerland)',
      'de': 'Preise inkl. 7.7% MwSt. (Schweiz)'
    }
  }
  
  const hint = taxHints[currency]
  if (!hint) return null
  
  // Versuche locale-spezifische Version, sonst Englisch
  const lang = locale.split('-')[0]
  return hint[lang] || hint['en'] || null
}

/**
 * Prüft ob alle Währungen Wechselkurse haben
 */
export function validateCurrencyMap(currencyMap: Record<string, string>): {
  valid: boolean
  missing: string[]
} {
  const missing: string[] = []
  
  for (const currency of Object.values(currencyMap)) {
    if (!EXCHANGE_RATES[currency] && currency !== 'USD') {
      missing.push(currency)
    }
  }
  
  return {
    valid: missing.length === 0,
    missing
  }
}

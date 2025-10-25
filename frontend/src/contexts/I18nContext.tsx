/*
 * Internationalisierung Context für React
 * Implementiert Mehrsprachigkeit mit react-i18next
 */

import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react'
import { useTranslation, I18nextProvider } from 'react-i18next'
import i18nConfig, { resolveLocale } from '../i18n/config-optimized'

// Sprach-Interface
export interface Language {
  code: string
  name: string
  nativeName: string
  flag: string
}

// Währungszuordnung pro Sprache/Land
export const CURRENCY_MAP: Record<string, string> = {
  // Euro-Zone (19 Länder)
  'de': 'EUR', 'de-DE': 'EUR', 'fr': 'EUR', 'fr-FR': 'EUR', 'es': 'EUR', 'es-ES': 'EUR',
  'it': 'EUR', 'it-IT': 'EUR', 'nl': 'EUR', 'nl-NL': 'EUR', 'pt': 'EUR',
  'el': 'EUR', 'el-GR': 'EUR', 'ga': 'EUR', 'ga-IE': 'EUR', 'lb': 'EUR', 'lb-LU': 'EUR',
  'mt': 'EUR', 'mt-MT': 'EUR', 'et': 'EUR', 'et-EE': 'EUR', 'lv': 'EUR', 'lv-LV': 'EUR',
  'lt': 'EUR', 'lt-LT': 'EUR', 'sk': 'EUR', 'sk-SK': 'EUR', 'sl': 'EUR', 'sl-SI': 'EUR',
  'fi': 'EUR', 'fi-FI': 'EUR',
  // Europa (Nicht-EUR)
  'sv': 'SEK', 'sv-SE': 'SEK', // Schweden
  'da': 'DKK', 'da-DK': 'DKK', // Dänemark
  'nb': 'NOK', 'nn': 'NOK', 'nb-NO': 'NOK', 'nn-NO': 'NOK', // Norwegen
  'is': 'ISK', 'is-IS': 'ISK', // Island
  'pl': 'PLN', 'pl-PL': 'PLN', // Polen
  'cs': 'CZK', 'cs-CZ': 'CZK', // Tschechien
  'hu': 'HUF', 'hu-HU': 'HUF', // Ungarn
  'ro': 'RON', 'ro-RO': 'RON', // Rumänien
  'bg': 'BGN', 'bg-BG': 'BGN', // Bulgarien
  'sr': 'RSD', 'sr-RS': 'RSD', // Serbien
  'mk': 'MKD', 'mk-MK': 'MKD', // Nord-Mazedonien
  'sq': 'ALL', 'sq-AL': 'ALL', // Albanien
  'bs': 'BAM', 'bs-BA': 'BAM', // Bosnien
  'uk': 'UAH', 'uk-UA': 'UAH', // Ukraine
  'be': 'BYN', 'be-BY': 'BYN', // Weißrussland
  'ru': 'RUB', 'ru-RU': 'RUB', // Russland
  'tr': 'TRY', 'tr-TR': 'TRY', // Türkei
  'rm': 'CHF', 'rm-CH': 'CHF', // Schweiz (Rätoromanisch)
  // Asien
  'zh-CN': 'CNY', // China
  'ja': 'JPY', 'ja-JP': 'JPY', // Japan
  'ko': 'KRW', 'ko-KR': 'KRW', // Südkorea
  'hi': 'INR', 'hi-IN': 'INR', // Indien
  'he': 'ILS', 'he-IL': 'ILS', // Hebräisch (Israel)
  'ar': 'SAR', 'ar-SA': 'SAR', // Saudi-Arabien
  'zh-HK': 'HKD', 'zh-TW': 'TWD', // Hong Kong, Taiwan
  // Englisch & Default
  'en': 'USD',  // Englisch (USA)
  'en-US': 'USD', 'en-GB': 'GBP', 'en-AU': 'AUD', 'en-CA': 'CAD',
  'en-NZ': 'NZD', 'en-ZA': 'ZAR', 'en-SG': 'SGD', 'en-IE': 'EUR',
  'en-IN': 'INR', 'en-PH': 'PHP', 'en-HK': 'HKD',
  // Zusätzliche regionale Englisch-Varianten
  'en-NG': 'NGN', // Nigeria
  'en-KE': 'KES', // Kenia
  'en-EG': 'EGP', // Ägypten
  'en-AE': 'AED', // Vereinigte Arabische Emirate
  'en-QA': 'QAR', // Katar
  'en-KW': 'KWD', // Kuwait
  // Regionale Varianten
  'fr-CA': 'CAD', 'fr-BE': 'EUR', 'fr-CH': 'CHF', 'fr-LU': 'EUR',
  'fr-DZ': 'DZD', 'fr-MA': 'MAD', 'fr-TN': 'TND',
  'pt-BR': 'BRL', 'pt-PT': 'EUR', 'pt-AO': 'AOA', 'pt-MZ': 'MZN',
  'es-MX': 'MXN', 'es-419': 'USD', 'es-AR': 'ARS', 'es-CL': 'CLP',
  'es-CO': 'COP', 'es-PE': 'PEN', 'es-VE': 'VES', 'es-UY': 'UYU',
  'de-AT': 'EUR', 'de-CH': 'CHF',
  'it-CH': 'CHF', 'nl-BE': 'EUR',
  // SEA & weitere regionale Sprachcodes
  'id': 'IDR', 'id-ID': 'IDR', // Indonesien
  'vi': 'VND', 'vi-VN': 'VND', // Vietnam
  'th': 'THB', 'th-TH': 'THB', // Thailand
  // Arabisch regionale Varianten
  'ar-AE': 'AED', // Vereinigte Arabische Emirate
  'ar-QA': 'QAR', // Katar
  'ar-KW': 'KWD', // Kuwait
  // Malaysia (Malay ist ggf. nicht als Locale aktiv, aber Mapping vorbereiten)
  'ms': 'MYR', 'ms-MY': 'MYR',
}

// Locale-Mapping für Intl.NumberFormat
export const LOCALE_MAP: Record<string, string> = {
  'en': 'en-US', 'en-US': 'en-US', 'en-GB': 'en-GB', 'en-AU': 'en-AU', 'en-CA': 'en-CA',
  'en-NZ': 'en-NZ', 'en-ZA': 'en-ZA', 'en-SG': 'en-SG', 'en-IE': 'en-IE',
  'en-IN': 'en-IN', 'en-PH': 'en-PH', 'en-HK': 'en-HK',
  'de': 'de-DE', 'de-DE': 'de-DE', 'de-AT': 'de-AT', 'de-CH': 'de-CH',
  'fr': 'fr-FR', 'fr-FR': 'fr-FR', 'fr-CA': 'fr-CA', 'fr-BE': 'fr-BE', 'fr-CH': 'fr-CH',
  'fr-LU': 'fr-LU', 'fr-DZ': 'fr-DZ', 'fr-MA': 'fr-MA', 'fr-TN': 'fr-TN',
  'es': 'es-ES', 'es-ES': 'es-ES', 'es-MX': 'es-MX', 'es-AR': 'es-AR', 'es-CL': 'es-CL',
  'es-CO': 'es-CO', 'es-PE': 'es-PE', 'es-VE': 'es-VE', 'es-UY': 'es-UY', 'es-419': 'es-419',
  'it': 'it-IT', 'it-IT': 'it-IT', 'it-CH': 'it-CH',
  'pt': 'pt-PT', 'pt-PT': 'pt-PT', 'pt-BR': 'pt-BR', 'pt-AO': 'pt-AO', 'pt-MZ': 'pt-MZ',
  'nl': 'nl-NL', 'nl-NL': 'nl-NL', 'nl-BE': 'nl-BE',
  'pl': 'pl-PL', 'pl-PL': 'pl-PL', 'cs': 'cs-CZ', 'cs-CZ': 'cs-CZ', 'sk': 'sk-SK',
  'sk-SK': 'sk-SK', 'hu': 'hu-HU', 'hu-HU': 'hu-HU', 'ro': 'ro-RO', 'ro-RO': 'ro-RO',
  'bg': 'bg-BG', 'bg-BG': 'bg-BG', 'el': 'el-GR', 'el-GR': 'el-GR', 'sl': 'sl-SI',
  'sl-SI': 'sl-SI', 'sr': 'sr-RS', 'sr-RS': 'sr-RS', 'bs': 'bs-BA', 'bs-BA': 'bs-BA',
  'mk': 'mk-MK', 'mk-MK': 'mk-MK', 'sq': 'sq-AL', 'sq-AL': 'sq-AL', 'lt': 'lt-LT',
  'lt-LT': 'lt-LT', 'lv': 'lv-LV', 'lv-LV': 'lv-LV', 'et': 'et-EE', 'et-EE': 'et-EE',
  'fi': 'fi-FI', 'fi-FI': 'fi-FI', 'sv': 'sv-SE', 'sv-SE': 'sv-SE', 'da': 'da-DK',
  'da-DK': 'da-DK', 'nb': 'nb-NO', 'nb-NO': 'nb-NO', 'nn': 'nn-NO', 'nn-NO': 'nn-NO',
  'is': 'is-IS', 'is-IS': 'is-IS', 'ga': 'ga-IE', 'ga-IE': 'ga-IE', 'mt': 'mt-MT',
  'mt-MT': 'mt-MT', 'lb': 'lb-LU', 'lb-LU': 'lb-LU', 'rm': 'rm-CH', 'rm-CH': 'rm-CH',
  'uk': 'uk-UA', 'uk-UA': 'uk-UA', 'be': 'be-BY', 'be-BY': 'be-BY', 'ru': 'ru-RU',
  'ru-RU': 'ru-RU', 'tr': 'tr-TR', 'tr-TR': 'tr-TR', 'ar': 'ar-SA', 'ar-SA': 'ar-SA',
  'hi': 'hi-IN', 'hi-IN': 'hi-IN', 'zh-CN': 'zh-CN', 'ja': 'ja-JP', 'ja-JP': 'ja-JP',
  'ko': 'ko-KR', 'ko-KR': 'ko-KR', 'he': 'he-IL', 'he-IL': 'he-IL',
  'zh-HK': 'zh-HK', 'zh-TW': 'zh-TW',
  // Zusätzliche regionale Englisch-Locales
  'en-NG': 'en-NG', 'en-KE': 'en-KE', 'en-EG': 'en-EG',
  'en-AE': 'en-AE', 'en-QA': 'en-QA', 'en-KW': 'en-KW',
  // SEA Locales
  'id': 'id-ID', 'id-ID': 'id-ID',
  'vi': 'vi-VN', 'vi-VN': 'vi-VN',
  'th': 'th-TH', 'th-TH': 'th-TH',
  // Malay (Locale, falls verwendet)
  'ms': 'ms-MY', 'ms-MY': 'ms-MY',
  // Arabisch regionale Varianten
  'ar-AE': 'ar-AE', 'ar-QA': 'ar-QA', 'ar-KW': 'ar-KW',
}

// Verfügbare Sprachen - ALLE 42 mit korrekten Flags
export const LANGUAGES: Language[] = [
  { code: 'en', name: 'English', nativeName: 'English', flag: '🇺🇸' },
  { code: 'de', name: 'German', nativeName: 'Deutsch', flag: '🇩🇪' },
  { code: 'fr', name: 'French', nativeName: 'Français', flag: '🇫🇷' },
  { code: 'es', name: 'Spanish', nativeName: 'Español', flag: '🇪🇸' },
  { code: 'it', name: 'Italian', nativeName: 'Italiano', flag: '🇮🇹' },
  { code: 'pt', name: 'Portuguese', nativeName: 'Português', flag: '🇵🇹' },
  { code: 'nl', name: 'Dutch', nativeName: 'Nederlands', flag: '🇳🇱' },
  { code: 'pl', name: 'Polish', nativeName: 'Polski', flag: '🇵🇱' },
  { code: 'cs', name: 'Czech', nativeName: 'Čeština', flag: '🇨🇿' },
  { code: 'sk', name: 'Slovak', nativeName: 'Slovenčina', flag: '🇸🇰' },
  { code: 'hu', name: 'Hungarian', nativeName: 'Magyar', flag: '🇭🇺' },
  { code: 'ro', name: 'Romanian', nativeName: 'Română', flag: '🇷🇴' },
  { code: 'bg', name: 'Bulgarian', nativeName: 'Български', flag: '🇧🇬' },
  { code: 'el', name: 'Greek', nativeName: 'Ελληνικά', flag: '🇬🇷' },
  { code: 'sl', name: 'Slovenian', nativeName: 'Slovenščina', flag: '🇸🇮' },
  { code: 'sr', name: 'Serbian', nativeName: 'Српски', flag: '🇷🇸' },
  { code: 'bs', name: 'Bosnian', nativeName: 'Bosanski', flag: '🇧🇦' },
  { code: 'mk', name: 'Macedonian', nativeName: 'Македонски', flag: '🇲🇰' },
  { code: 'sq', name: 'Albanian', nativeName: 'Shqip', flag: '🇦🇱' },
  { code: 'lt', name: 'Lithuanian', nativeName: 'Lietuvių', flag: '🇱🇹' },
  { code: 'lv', name: 'Latvian', nativeName: 'Latviešu', flag: '🇱🇻' },
  { code: 'et', name: 'Estonian', nativeName: 'Eesti', flag: '🇪🇪' },
  { code: 'fi', name: 'Finnish', nativeName: 'Suomi', flag: '🇫🇮' },
  { code: 'sv', name: 'Swedish', nativeName: 'Svenska', flag: '🇸🇪' },
  { code: 'da', name: 'Danish', nativeName: 'Dansk', flag: '🇩🇰' },
  { code: 'nb', name: 'Norwegian Bokmål', nativeName: 'Norsk Bokmål', flag: '🇳🇴' },
  { code: 'nn', name: 'Norwegian Nynorsk', nativeName: 'Nynorsk', flag: '🇳🇴' },
  { code: 'is', name: 'Icelandic', nativeName: 'Íslenska', flag: '🇮🇸' },
  { code: 'ga', name: 'Irish', nativeName: 'Gaeilge', flag: '🇮🇪' },
  { code: 'mt', name: 'Maltese', nativeName: 'Malti', flag: '🇲🇹' },
  { code: 'lb', name: 'Luxembourgish', nativeName: 'Lëtzebuergesch', flag: '🇱🇺' },
  { code: 'rm', name: 'Romansh', nativeName: 'Rumantsch', flag: '🇨🇭' },
  { code: 'uk', name: 'Ukrainian', nativeName: 'Українська', flag: '🇺🇦' },
  { code: 'be', name: 'Belarusian', nativeName: 'Беларуская', flag: '🇧🇾' },
  { code: 'ru', name: 'Russian', nativeName: 'Русский', flag: '🇷🇺' },
  { code: 'tr', name: 'Turkish', nativeName: 'Türkçe', flag: '🇹🇷' },
  { code: 'ar', name: 'Arabic', nativeName: 'العربية', flag: '🇸🇦' },
  { code: 'hi', name: 'Hindi', nativeName: 'हिन्दी', flag: '🇮🇳' },
  { code: 'he', name: 'Hebrew', nativeName: 'עברית', flag: '🇮🇱' },
  { code: 'zh-CN', name: 'Chinese (Simplified)', nativeName: '简体中文', flag: '🇨🇳' },
  { code: 'ja', name: 'Japanese', nativeName: '日本語', flag: '🇯🇵' },
  { code: 'ko', name: 'Korean', nativeName: '한국어', flag: '🇰🇷' }
]

// Context Interface
interface I18nContextType {
  currentLanguage: string
  setLanguage: (language: string) => Promise<void>
  languages: Language[]
  isLoading: boolean
  t: (key: string, options?: any) => string
}

// I18n Context
const I18nContext = createContext<I18nContextType | undefined>(undefined)

// I18n Provider Component
interface I18nProviderProps {
  children: ReactNode
  defaultLanguage?: string
}

export const I18nProvider: React.FC<I18nProviderProps> = ({
  children,
  defaultLanguage = 'en'
}) => {
  const { i18n: i18nInstance } = useTranslation()
  const [currentLanguage, setCurrentLanguage] = useState(defaultLanguage)
  const [isLoading, setIsLoading] = useState(false)

  // Sprache beim Start setzen
  useEffect(() => {
    const initializeLanguage = async () => {
      setIsLoading(true)
      try {
        // Sprache aus localStorage oder Cookie laden
        const savedLanguage = localStorage.getItem('user_language') ||
                             document.cookie.split('; ')
                               .find(row => row.startsWith('user_language='))
                               ?.split('=')[1]

        const wanted = savedLanguage || defaultLanguage
        const resolved = resolveLocale(wanted) || defaultLanguage

        if (resolved !== i18nInstance.language) {
          await i18nInstance.changeLanguage(resolved)
          setCurrentLanguage(wanted)
        }
      } catch (error) {
        console.error('Fehler beim Initialisieren der Sprache:', error)
        await i18nInstance.changeLanguage(defaultLanguage)
        setCurrentLanguage(defaultLanguage)
      } finally {
        setIsLoading(false)
      }
    }

    initializeLanguage()
  }, [i18nInstance, defaultLanguage])

  // HTML lang-Attribut dynamisch setzen
  useEffect(() => {
    const lang = i18nInstance.language || currentLanguage || 'en'
    const html = document.documentElement
    const prev = html.getAttribute('lang')
    if (prev !== lang) {
      html.setAttribute('lang', lang)
    }

    // Text-Richtung für RTL-Sprachen setzen
    const rtlLangs = new Set(['ar', 'he', 'fa', 'ur'])
    const isRtl = rtlLangs.has(lang)
    const prevDir = html.getAttribute('dir')
    const nextDir = isRtl ? 'rtl' : 'ltr'
    if (prevDir !== nextDir) {
      html.setAttribute('dir', nextDir)
    }
  }, [i18nInstance.language, currentLanguage])

  // Sprache ändern
  const setLanguage = async (language: string) => {
    // Regionale Codes akzeptieren und auf Basissprache auflösen
    const resolved = resolveLocale(language)
    if (!resolved) {
      throw new Error(`Sprache '${language}' wird nicht unterstützt`)
    }

    setIsLoading(true)
    try {
      await i18nInstance.changeLanguage(resolved)
      setCurrentLanguage(language)

      // Sprache speichern
      localStorage.setItem('user_language', language)
      document.cookie = `user_language=${language}; path=/; max-age=${30 * 24 * 60 * 60}; samesite=lax`

      // Backend über Sprache-Änderung informieren
      try {
        await fetch('/api/v1/i18n/set-language', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ language }),
        })
      } catch (error) {
        console.error('Fehler beim Setzen der Sprache auf dem Server:', error)
      }
    } catch (error) {
      console.error('Fehler beim Ändern der Sprache:', error)
      throw error
    } finally {
      setIsLoading(false)
    }
  }

  const contextValue: I18nContextType = {
    currentLanguage,
    setLanguage,
    languages: LANGUAGES,
    isLoading,
    t: (key: string, options?: any) => {
      return String(i18nInstance.t(key, options))
    }
  }

  return (
    <I18nextProvider i18n={i18nInstance}>
      <I18nContext.Provider value={contextValue}>
        {children}
      </I18nContext.Provider>
    </I18nextProvider>
  )
}

// Hook für I18n Context
export const useI18n = (): I18nContextType => {
  const context = useContext(I18nContext)
  if (context === undefined) {
    throw new Error('useI18n must be used within an I18nProvider')
  }
  return context
}

// Hook für Übersetzungen (Shortcut)
export const useI18nTranslation = () => {
  const { t } = useI18n()
  return { t }
}

// Sprach-Auswahl-Komponente
interface LanguageSelectorProps {
  className?: string
  variant?: 'dropdown' | 'buttons'
  showFlags?: boolean
}

export const LanguageSelector: React.FC<LanguageSelectorProps> = ({
  className = '',
  variant = 'dropdown',
  showFlags = true
}) => {
  const { currentLanguage, setLanguage, languages } = useI18n()

  if (variant === 'dropdown') {
    return (
      <select
        value={currentLanguage}
        onChange={(e) => setLanguage(e.target.value)}
        className={`px-3 py-2 border rounded-md bg-background text-foreground ${className}`}
      >
        {languages.map(language => (
          <option key={language.code} value={language.code}>
            {showFlags ? `${language.flag} ` : ''}{language.nativeName}
          </option>
        ))}
      </select>
    )
  }

  return (
    <div className={`flex gap-1 ${className}`}>
      {languages.map(language => (
        <button
          key={language.code}
          onClick={() => setLanguage(language.code)}
          className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
            currentLanguage === language.code
              ? 'bg-primary text-primary-foreground'
              : 'bg-muted hover:bg-muted/80'
          }`}
          title={language.name}
        >
          {showFlags ? language.flag : language.nativeName}
        </button>
      ))}
    </div>
  )
}

// Übersetzungs-Komponente (für dynamische Schlüssel)
interface TransProps {
  i18nKey: string
  values?: Record<string, any>
  children?: (translatedText: string) => ReactNode
}

export const Trans: React.FC<TransProps> = ({ i18nKey, values, children }) => {
  const { t } = useI18n()

  const translatedText = t(i18nKey, values)

  if (children) {
    return <>{children(translatedText)}</>
  }

  return <>{translatedText}</>
}

// Nummern-Formatierung für verschiedene Sprachen
export const formatNumber = (number: number, language?: string): string => {
  return new Intl.NumberFormat(language || 'en-US').format(number)
}

// Währungs-Formatierung für verschiedene Sprachen (AUTO-DETECTION)
export const formatCurrency = (amount: number, currency?: string, language?: string): string => {
  const lang = language || 'en'
  const locale = LOCALE_MAP[lang] || 'en-US'
  const curr = currency || CURRENCY_MAP[lang] || 'USD'
  
  return new Intl.NumberFormat(locale, {
    style: 'currency',
    currency: curr,
  }).format(amount)
}

// Hole Währung für aktuelle Sprache
export const getCurrencyForLanguage = (language: string): string => {
  return CURRENCY_MAP[language] || 'USD'
}

// Datums-Formatierung für verschiedene Sprachen
export const formatDate = (date: Date | string, language?: string): string => {
  const dateObj = typeof date === 'string' ? new Date(date) : date
  return new Intl.DateTimeFormat(language || 'en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  }).format(dateObj)
}

// Relativer Zeitstempel für verschiedene Sprachen
export const formatRelativeTime = (date: Date | string, language?: string): string => {
  const dateObj = typeof date === 'string' ? new Date(date) : date
  const now = new Date()
  const diffInSeconds = Math.floor((now.getTime() - dateObj.getTime()) / 1000)

  const rtf = new Intl.RelativeTimeFormat(language || 'en-US', { numeric: 'auto' })

  if (diffInSeconds < 60) {
    return rtf.format(-diffInSeconds, 'second')
  } else if (diffInSeconds < 3600) {
    return rtf.format(-Math.floor(diffInSeconds / 60), 'minute')
  } else if (diffInSeconds < 86400) {
    return rtf.format(-Math.floor(diffInSeconds / 3600), 'hour')
  } else {
    return rtf.format(-Math.floor(diffInSeconds / 86400), 'day')
  }
}

/*
 * i18next Konfiguration für React - Performance-optimiert
 * Lazy Loading und Code Splitting für bessere Bundle-Größe
 */

import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'
import LanguageDetector from 'i18next-browser-languagedetector'

// Kernsprachen - diese werden immer im Hauptbundle geladen
const CORE_LANGUAGES = ['en', 'de', 'fr', 'es', 'it', 'pt', 'nl']

// Regionale Locale-Aliase (z. B. en-GB -> en)
const REGIONAL_ALIASES: Record<string, string> = {
  // Englisch
  'en-GB': 'en', 'en-US': 'en', 'en-AU': 'en', 'en-CA': 'en', 'en-NZ': 'en',
  'en-ZA': 'en', 'en-SG': 'en', 'en-IE': 'en', 'en-IN': 'en', 'en-PH': 'en', 'en-HK': 'en',
  // Spanisch
  'es-ES': 'es', 'es-MX': 'es', 'es-AR': 'es', 'es-CL': 'es', 'es-CO': 'es',
  'es-PE': 'es', 'es-VE': 'es', 'es-UY': 'es', 'es-419': 'es',
  // Portugiesisch
  'pt-PT': 'pt', 'pt-BR': 'pt', 'pt-AO': 'pt', 'pt-MZ': 'pt',
  // Französisch
  'fr-FR': 'fr', 'fr-CA': 'fr', 'fr-BE': 'fr', 'fr-CH': 'fr', 'fr-LU': 'fr',
  'fr-DZ': 'fr', 'fr-MA': 'fr', 'fr-TN': 'fr',
  // Deutsch
  'de-DE': 'de', 'de-AT': 'de', 'de-CH': 'de',
  // Italienisch
  'it-IT': 'it', 'it-CH': 'it',
  // Niederländisch
  'nl-NL': 'nl', 'nl-BE': 'nl',
  // Weitere Europäische
  'pl-PL': 'pl', 'cs-CZ': 'cs', 'sk-SK': 'sk', 'hu-HU': 'hu', 'ro-RO': 'ro',
  'bg-BG': 'bg', 'el-GR': 'el', 'sl-SI': 'sl', 'sr-RS': 'sr', 'bs-BA': 'bs',
  'mk-MK': 'mk', 'sq-AL': 'sq', 'lt-LT': 'lt', 'lv-LV': 'lv', 'et-EE': 'et',
  'fi-FI': 'fi', 'sv-SE': 'sv', 'da-DK': 'da', 'nb-NO': 'nb', 'nn-NO': 'nn',
  'is-IS': 'is', 'ga-IE': 'ga', 'mt-MT': 'mt', 'lb-LU': 'lb', 'rm-CH': 'rm',
  'uk-UA': 'uk', 'be-BY': 'be', 'ru-RU': 'ru', 'tr-TR': 'tr',
  // Asiatisch
  'ar-SA': 'ar', 'hi-IN': 'hi', 'ja-JP': 'ja', 'ko-KR': 'ko', 'zh-HK': 'zh-CN',
  // Taiwan soll eigenes Locale verwenden
  'zh-TW': 'zh-TW',
  // Malay (Malaysia) auf ms mappen
  'ms-MY': 'ms',
  'fa-IR': 'fa', 'ur-PK': 'ur', 'id-ID': 'id', 'vi-VN': 'vi', 'th-TH': 'th', 'bn-BD': 'bn',
  // Hebräisch
  'he-IL': 'he'
}

// Verfügbare Sprachen (Lazy Loading Cache)
const AVAILABLE_LANGUAGES = new Set([
  'ar', 'be', 'bg', 'bs', 'cs', 'da', 'de', 'el', 'en', 'es', 'et', 'fi', 'fr', 'ga',
  'hi', 'hu', 'is', 'it', 'ja', 'ko', 'he', 'lb', 'lt', 'lv', 'mk', 'mt', 'nb', 'nl',
  'nn', 'pl', 'pt', 'rm', 'ro', 'ru', 'sk', 'sl', 'sq', 'sr', 'sv', 'tr', 'uk', 'zh-CN', 'zh-TW', 'fa',
  'ur', 'id', 'vi', 'th', 'bn', 'ms'
])

// Cache für geladene Sprachressourcen
const languageCache = new Map<string, any>()

// Lazy Loading Funktion für Sprachressourcen
async function loadLanguageResources(lang: string): Promise<any> {
  // Prüfen ob bereits geladen
  if (languageCache.has(lang)) {
    return languageCache.get(lang)
  }

  try {
    // Dynamischer Import für besseres Code Splitting
    const module = await import(`../locales/${lang}.json`)
    languageCache.set(lang, module.default)
    return module.default
  } catch (error) {
    console.warn(`Failed to load language resources for ${lang}:`, error)
    // Fallback zu Englisch wenn Sprache nicht gefunden wird
    if (lang !== 'en') {
      return loadLanguageResources('en')
    }
    throw error
  }
}

// Leichtgewichtiges Custom-Backend für i18next, das die JSON-Dateien aus ../locales via dynamic import lädt
const CustomBackend = {
  type: 'backend' as const,
  init() {
    // keine spezielle Initialisierung nötig
  },
  // i18next ruft read(lang, ns, cb) auf, um Ressourcen zu laden
  async read(language: string, namespace: string, callback: (error: any, resources?: any) => void) {
    try {
      const translations = await loadLanguageResources(language)
      // Namespace ist 'translation'; liefere das rohe Objekt zurück
      callback(null, translations)
    } catch (err) {
      callback(err)
    }
  },
}

// Ressourcen-Loader für i18next
const resourcesLoader = {
  async load(languages: string[], namespaces: string[]) {
    const resources: Record<string, any> = {}

    for (const lang of languages) {
      // Für Kernsprachen: Sofort laden (synchrone Imports)
      if (CORE_LANGUAGES.includes(lang)) {
        try {
          const module = await import(`../locales/${lang}.json`)
          resources[lang] = { translation: module.default }
        } catch (error) {
          console.warn(`Failed to load core language ${lang}:`, error)
        }
      }
      // Für andere Sprachen: Lazy Loading
      else {
        resources[lang] = { translation: {} } // Placeholder
      }
    }

    return resources
  },

  async reload(languages: string[], namespaces: string[]) {
    for (const lang of languages) {
      if (!CORE_LANGUAGES.includes(lang)) {
        try {
          const translations = await loadLanguageResources(lang)
          i18n.addResourceBundle(lang, 'translation', translations, true, true)
        } catch (error) {
          console.warn(`Failed to reload language ${lang}:`, error)
        }
      }
    }
  }
}

// Locale-Auflösung: akzeptiert regionale Codes und fällt auf Basissprache zurück
export const resolveLocale = (lng: string | undefined): string | undefined => {
  if (!lng) return undefined
  if (AVAILABLE_LANGUAGES.has(lng)) return lng
  if (REGIONAL_ALIASES[lng]) return REGIONAL_ALIASES[lng]
  const base = lng.split('-')[0]
  if (AVAILABLE_LANGUAGES.has(base)) return base
  return undefined
}

// i18next initialisieren mit optimierter Konfiguration
i18n
  // react-i18next integrieren
  .use(initReactI18next)
  // Sprach-Detektor hinzufügen
  .use(LanguageDetector)
  // Custom Backend registrieren (verhindert Warnung und lädt Ressourcen korrekt)
  .use(CustomBackend)
  // Konfiguration
  .init({
    // Sprache
    lng: 'en', // Standardsprache
    fallbackLng: 'en', // Fallback-Sprache

    // Namespaces
    defaultNS: 'translation',
    ns: ['translation'],

    // Debug-Modus (nur in Entwicklung)
    debug: process.env.NODE_ENV === 'development',

    // Interpolation
    interpolation: {
      escapeValue: false, // React escaped bereits
      formatSeparator: ',',
    },

    // Sprach-Detektion - optimiert für Performance
    detection: {
      order: ['localStorage', 'cookie', 'navigator', 'htmlTag'],
      lookupLocalStorage: 'user_language',
      lookupCookie: 'user_language',
      caches: ['localStorage', 'cookie'],
    },

    // Kein zusätzliches Backend-Optionsobjekt notwendig, da CustomBackend registriert ist

    // React-Optionen - optimiert
    react: {
      useSuspense: false,
      bindI18n: 'languageChanged loaded',
      bindI18nStore: 'added removed',
      transEmptyNodeValue: '',
      transSupportBasicHtmlNodes: true,
      transKeepBasicHtmlNodesFor: ['br', 'strong', 'i', 'em'],
      // Performance-Optimierung: Weniger Re-renders
      transWrapTextNodes: '',
    },

    // Performance-Optimierungen
    load: 'languageOnly', // Nur Sprache laden, nicht alle Ressourcen
    preload: CORE_LANGUAGES, // Nur Kernsprachen vorladen
    keySeparator: '.', // Flachere Schlüssel für bessere Performance
    nsSeparator: ':',
    pluralSeparator: '_',
    contextSeparator: '_',

    // Sprachen-Whitelist (ersetzt checkWhitelist des Detectors)
    supportedLngs: Array.from(AVAILABLE_LANGUAGES),
    // Erlaube regionale Varianten und mappe auf Basissprachen (z. B. en-GB -> en)
    nonExplicitSupportedLngs: true,

    // Cache-Optimierungen
    saveMissing: false, // Nicht fehlende Schlüssel speichern
    saveMissingTo: 'fallback', // Bei fehlenden Schlüsseln nicht auf Server speichern
  })

// RTL-Unterstützung: ar, he, fa → dir="rtl"
function applyDirection(lang: string) {
  if (typeof document === 'undefined') return
  const rtl = ['ar', 'he', 'fa', 'ur']
  const base = lang.split('-')[0]
  document.documentElement.setAttribute('dir', rtl.includes(base) ? 'rtl' : 'ltr')
}

// Sprache beim Start setzen - optimiert
const setInitialLanguage = async () => {
  try {
    // Aus localStorage oder Cookie laden
    const savedLanguage = localStorage.getItem('user_language') ||
                         document.cookie.split('; ')
                           .find(row => row.startsWith('user_language='))
                           ?.split('=')[1]

    const candidate = resolveLocale(savedLanguage || undefined)
    if (candidate) {
      // Für Kernsprachen: Sofort wechseln
      if (CORE_LANGUAGES.includes(candidate)) {
        await i18n.changeLanguage(candidate)
        applyDirection(candidate)
      } else {
        // Sprache setzen aber Ressourcen erst bei Bedarf laden
        i18n.changeLanguage(candidate)
        applyDirection(candidate)
      }
    } else {
      // Automatische Sprach-Erkennung versuchen (nur wenn nötig)
      const detected = i18n.services.languageDetector.detect()
      const detectedFirst = Array.isArray(detected) ? detected[0] : detected
      const resolved = resolveLocale(detectedFirst)

      if (resolved && resolved !== i18n.language) {
        // Für Kernsprachen: Sofort wechseln
        if (CORE_LANGUAGES.includes(resolved)) {
          await i18n.changeLanguage(resolved)
          applyDirection(resolved)
        } else {
          i18n.changeLanguage(resolved)
          applyDirection(resolved)
        }
      }
    }
  } catch (error) {
    console.error('Fehler beim Setzen der initialen Sprache:', error)
  }
}

// Initiale Sprache setzen
setInitialLanguage()

// Reagiere auf Sprachwechsel (zur Laufzeit)
if (typeof window !== 'undefined') {
  i18n.on('languageChanged', (lng: string) => {
    try { applyDirection(lng) } catch {}
  })
}

export default i18n

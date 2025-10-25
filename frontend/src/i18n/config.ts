/*
 * i18next Konfiguration für React
 */

import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'
import LanguageDetector from 'i18next-browser-languagedetector'

// Übersetzungs-Ressourcen - ALLE 42 Sprachen
import arTranslations from '../locales/ar.json'
import beTranslations from '../locales/be.json'
import bgTranslations from '../locales/bg.json'
import bsTranslations from '../locales/bs.json'
import csTranslations from '../locales/cs.json'
import daTranslations from '../locales/da.json'
import deTranslations from '../locales/de.json'
import elTranslations from '../locales/el.json'
import enTranslations from '../locales/en.json'
import esTranslations from '../locales/es.json'
import etTranslations from '../locales/et.json'
import fiTranslations from '../locales/fi.json'
import frTranslations from '../locales/fr.json'
import gaTranslations from '../locales/ga.json'
import hiTranslations from '../locales/hi.json'
import huTranslations from '../locales/hu.json'
import isTranslations from '../locales/is.json'
import itTranslations from '../locales/it.json'
import jaTranslations from '../locales/ja.json'
import koTranslations from '../locales/ko.json'
import heTranslations from '../locales/he.json'
import lbTranslations from '../locales/lb.json'
import ltTranslations from '../locales/lt.json'
import lvTranslations from '../locales/lv.json'
import mkTranslations from '../locales/mk.json'
import mtTranslations from '../locales/mt.json'
import nbTranslations from '../locales/nb.json'
import nlTranslations from '../locales/nl.json'
import nnTranslations from '../locales/nn.json'
import plTranslations from '../locales/pl.json'
import ptTranslations from '../locales/pt.json'
import rmTranslations from '../locales/rm.json'
import roTranslations from '../locales/ro.json'
import ruTranslations from '../locales/ru.json'
import skTranslations from '../locales/sk.json'
import slTranslations from '../locales/sl.json'
import sqTranslations from '../locales/sq.json'
import srTranslations from '../locales/sr.json'
import svTranslations from '../locales/sv.json'
import trTranslations from '../locales/tr.json'
import ukTranslations from '../locales/uk.json'
import zhCNTranslations from '../locales/zh-CN.json'

// Die Ressourcen - ALLE 42 Sprachen
const resources = {
  ar: { translation: arTranslations },
  be: { translation: beTranslations },
  bg: { translation: bgTranslations },
  bs: { translation: bsTranslations },
  cs: { translation: csTranslations },
  da: { translation: daTranslations },
  de: { translation: deTranslations },
  el: { translation: elTranslations },
  en: { translation: enTranslations },
  es: { translation: esTranslations },
  et: { translation: etTranslations },
  fi: { translation: fiTranslations },
  fr: { translation: frTranslations },
  ga: { translation: gaTranslations },
  hi: { translation: hiTranslations },
  hu: { translation: huTranslations },
  is: { translation: isTranslations },
  it: { translation: itTranslations },
  ja: { translation: jaTranslations },
  ko: { translation: koTranslations },
  he: { translation: heTranslations },
  lb: { translation: lbTranslations },
  lt: { translation: ltTranslations },
  lv: { translation: lvTranslations },
  mk: { translation: mkTranslations },
  mt: { translation: mtTranslations },
  nb: { translation: nbTranslations },
  nl: { translation: nlTranslations },
  nn: { translation: nnTranslations },
  pl: { translation: plTranslations },
  pt: { translation: ptTranslations },
  rm: { translation: rmTranslations },
  ro: { translation: roTranslations },
  ru: { translation: ruTranslations },
  sk: { translation: skTranslations },
  sl: { translation: slTranslations },
  sq: { translation: sqTranslations },
  sr: { translation: srTranslations },
  sv: { translation: svTranslations },
  tr: { translation: trTranslations },
  uk: { translation: ukTranslations },
  'zh-CN': { translation: zhCNTranslations }
}

// Regionale Locale-Aliase (z. B. en-GB -> en)
const REGIONAL_ALIASES: Record<string, string> = {
  'en-GB': 'en',
  'en-US': 'en',
  'en-AU': 'en',
  'en-CA': 'en',
  'en-NZ': 'en',
  'en-ZA': 'en',
  'en-SG': 'en',
  'en-IE': 'en',
  'en-IN': 'en',
  'en-PH': 'en',
  'en-HK': 'en',
  'es-ES': 'es',
  'es-MX': 'es',
  'es-AR': 'es',
  'es-CL': 'es',
  'es-CO': 'es',
  'es-PE': 'es',
  'es-VE': 'es',
  'es-UY': 'es',
  'es-419': 'es',
  'pt-PT': 'pt',
  'pt-BR': 'pt',
  'pt-AO': 'pt',
  'pt-MZ': 'pt',
  'fr-FR': 'fr',
  'fr-CA': 'fr',
  'fr-BE': 'fr',
  'fr-CH': 'fr',
  'fr-LU': 'fr',
  'fr-DZ': 'fr',
  'fr-MA': 'fr',
  'fr-TN': 'fr',
  'de-AT': 'de',
  'de-CH': 'de',
  'it-CH': 'it',
  'nl-BE': 'nl',
  'zh-TW': 'zh-CN'
  , 'zh-HK': 'zh-CN',
  'he-IL': 'he'
}

// Locale-Auflösung: akzeptiert regionale Codes und fällt auf Basissprache zurück
export const resolveLocale = (lng: string | undefined): string | undefined => {
  if (!lng) return undefined
  if ((resources as any)[lng]) return lng
  if (REGIONAL_ALIASES[lng]) return REGIONAL_ALIASES[lng]
  const base = lng.split('-')[0]
  if ((resources as any)[base]) return base
  return undefined
}

// i18next initialisieren
i18n
  // react-i18next integrieren
  .use(initReactI18next)
  // Sprach-Detektor hinzufügen
  .use(LanguageDetector)
  // Konfiguration
  .init({
    resources,

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

    // Sprach-Detektion
    detection: {
      order: ['localStorage', 'cookie', 'navigator', 'htmlTag'],
      lookupLocalStorage: 'user_language',
      lookupCookie: 'user_language',
      caches: ['localStorage', 'cookie'],
    },

    // React-Optionen
    react: {
      useSuspense: false,
      bindI18n: 'languageChanged loaded',
      bindI18nStore: 'added removed',
      transEmptyNodeValue: '',
      transSupportBasicHtmlNodes: true,
      transKeepBasicHtmlNodesFor: ['br', 'strong', 'i', 'em'],
    },
  })

// Sprache beim Start setzen
const setInitialLanguage = async () => {
  try {
    // Aus localStorage oder Cookie laden
    const savedLanguage = localStorage.getItem('user_language') ||
                         document.cookie.split('; ')
                           .find(row => row.startsWith('user_language='))
                           ?.split('=')[1]

    const candidate = resolveLocale(savedLanguage || undefined)
    if (candidate) {
      await i18n.changeLanguage(candidate)
    } else {
      // Automatische Sprach-Erkennung versuchen
      const detected = i18n.services.languageDetector.detect()
      const detectedFirst = Array.isArray(detected) ? detected[0] : detected
      const resolved = resolveLocale(detectedFirst)
      if (resolved) {
        await i18n.changeLanguage(resolved)
      }
    }
  } catch (error) {
    console.error('Fehler beim Setzen der initialen Sprache:', error)
  }
}

// Initiale Sprache setzen
setInitialLanguage()

export default i18n

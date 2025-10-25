import React from 'react'
import { Helmet } from 'react-helmet-async'
import { useLocation } from 'react-router-dom'
import { useTranslation } from 'react-i18next'

interface SEOHeadProps {
  title?: string
  description?: string
  keywords?: string[]
  image?: string
  type?: 'website' | 'article'
  canonical?: string
  noindex?: boolean
}

/**
 * SEO Head Component
 * ===================
 * Manages all SEO meta tags including:
 * - Title & Description
 * - Open Graph (Facebook, LinkedIn)
 * - Twitter Cards
 * - Canonical URLs
 * - hreflang tags for multi-language
 * - Structured Data (JSON-LD)
 */
export default function SEOHead({
  title,
  description,
  keywords = [],
  image,
  type = 'website',
  canonical,
  noindex = false,
}: SEOHeadProps) {
  const location = useLocation()
  const { i18n } = useTranslation()
  
  // Default values
  const siteTitle = 'SIGMACODE | Enterprise Blockchain Intelligence'
  const siteDescription = 'AI-driven blockchain forensics platform for compliance, investigations, and risk monitoring. Trace transactions across 100+ blockchains with real-time sanctions screening.'
  const siteUrl = typeof window !== 'undefined' ? window.location.origin : 'https://sigmacode.io'
  const currentUrl = `${siteUrl}${location.pathname}`
  const currentLang = i18n.language || 'en'
  
  // Multi-Language OG-Image Support - ALLE 43 Sprachen!
  // Wählt automatisch das richtige OG-Image basierend auf der Sprache
  const supportedOgLanguages = [
    // Tier 1: Global & West-Europa
    'en', 'de', 'es', 'fr', 'it', 'pt', 'nl',
    // Tier 2: Ost-Europa
    'pl', 'cs', 'ru', 'uk', 'ro', 'bg', 'hu', 'sk',
    // Tier 3: Nord-Europa
    'sv', 'da', 'fi', 'no', 'is',
    // Tier 4: Balkan
    'sr', 'hr', 'bs', 'sl', 'mk', 'sq',
    // Tier 5: Baltikum & Weitere Europa
    'lt', 'lv', 'et', 'el', 'tr',
    // Tier 6: Asien
    'ja', 'zh', 'ko', 'hi', 'th', 'vi', 'id', 'ur', 'bn',
    // Tier 7: Naher Osten
    'ar', 'he', 'fa',
    // Tier 8: Weitere
    'be', 'ga', 'lb', 'mt'
  ]
  const ogLang = supportedOgLanguages.includes(currentLang) ? currentLang : 'en'
  const defaultImage = `${siteUrl}/og-images/og-image-${ogLang}.svg`
  
  // Computed values
  const pageTitle = title ? `${title} | ${siteTitle}` : siteTitle
  const pageDescription = description || siteDescription
  const pageImage = image || defaultImage
  const pageCanonical = canonical || currentUrl
  
  // Available languages for hreflang
  const languages = ['en', 'de', 'es', 'fr', 'it', 'pt', 'nl', 'pl', 'cs', 'ru', 'sv', 'da', 'fi', 'fa', 'ur', 'id', 'vi', 'th', 'bn']
  
  // Keywords
  const defaultKeywords = [
    'blockchain forensics',
    'crypto compliance',
    'transaction tracing',
    'chainalysis alternative',
    'blockchain analytics',
    'crypto investigation',
    'sanctions screening',
    'AML compliance',
    'KYT',
    'crypto intelligence',
  ]
  const pageKeywords = [...defaultKeywords, ...keywords].join(', ')
  
  return (
    <Helmet>
      {/* Basic Meta Tags */}
      <title>{pageTitle}</title>
      <meta name="description" content={pageDescription} />
      <meta name="keywords" content={pageKeywords} />
      <meta name="language" content={currentLang} />
      
      {/* Robots */}
      {noindex && <meta name="robots" content="noindex, nofollow" />}
      
      {/* Canonical URL */}
      <link rel="canonical" href={pageCanonical} />
      
      {/* hreflang tags for multi-language */}
      {languages.map((lang) => {
        const hrefLangUrl = currentUrl.replace(`/${currentLang}/`, `/${lang}/`)
        return <link key={lang} rel="alternate" hrefLang={lang} href={hrefLangUrl} />
      })}
      <link rel="alternate" hrefLang="x-default" href={currentUrl.replace(`/${currentLang}/`, '/en/')} />
      
      {/* Open Graph (Facebook, LinkedIn, WhatsApp) */}
      <meta property="og:type" content={type} />
      <meta property="og:title" content={pageTitle} />
      <meta property="og:description" content={pageDescription} />
      <meta property="og:url" content={currentUrl} />
      <meta property="og:image" content={pageImage} />
      <meta property="og:image:width" content="1200" />
      <meta property="og:image:height" content="630" />
      <meta property="og:site_name" content="SIGMACODE" />
      <meta property="og:locale" content={currentLang === 'en' ? 'en_US' : `${currentLang}_${currentLang.toUpperCase()}`} />
      
      {/* Twitter Card */}
      <meta name="twitter:card" content="summary_large_image" />
      <meta name="twitter:title" content={pageTitle} />
      <meta name="twitter:description" content={pageDescription} />
      <meta name="twitter:image" content={pageImage} />
      <meta name="twitter:site" content="@sigmacode" />
      <meta name="twitter:creator" content="@sigmacode" />
      
      {/* Additional Meta Tags */}
      <meta name="author" content="SIGMACODE" />
      <meta name="copyright" content="© 2025 SIGMACODE Blockchain Forensics" />
      <meta name="rating" content="general" />
      <meta name="revisit-after" content="7 days" />
      
      {/* Geo Tags */}
      <meta name="geo.region" content="AT-9" />
      <meta name="geo.placename" content="Vienna" />
      <meta name="geo.position" content="48.2082;16.3738" />
      <meta name="ICBM" content="48.2082, 16.3738" />
    </Helmet>
  )
}

// Predefined SEO configs for common pages
export const SEO_CONFIGS = {
  home: {
    title: 'Enterprise Blockchain Intelligence Platform',
    description: 'AI-driven compliance, investigations, and risk monitoring across 100+ blockchains. Real-time sanctions screening (OFAC/UN/EU), transaction tracing, and forensic analysis.',
    keywords: ['blockchain forensics platform', 'crypto compliance software', 'enterprise blockchain analytics', 'chainalysis competitor', 'multi-chain tracing'],
  },
  features: {
    title: 'Features | Transaction Tracing, AI Analysis & Case Management',
    description: 'Comprehensive blockchain forensic tools: Multi-chain tracing, real-time alerts, sanctions screening, graph analytics, AI-powered investigation, and case management.',
    keywords: ['transaction tracing', 'blockchain forensics tools', 'crypto investigation features', 'sanctions screening', 'graph analytics'],
  },
  pricing: {
    title: 'Pricing | From Free to Enterprise Plans',
    description: 'Flexible pricing from Community (free) to Enterprise. Pro plan at $159/mo includes 20 blockchains, case management, and forensic reports. 95% cheaper than Chainalysis.',
    keywords: ['blockchain forensics pricing', 'chainalysis pricing alternative', 'crypto compliance cost', 'affordable blockchain analytics'],
  },
  chatbot: {
    title: 'AI Chatbot for Web3 | Voice, Crypto Payments & Forensics',
    description: 'Revolutionary Web3 chatbot with voice input (43 languages), crypto payments (30+ coins), real-time risk scoring, and blockchain forensics integration.',
    keywords: ['web3 chatbot', 'blockchain ai assistant', 'crypto payment chatbot', 'voice-enabled crypto chat'],
  },
  login: {
    title: 'Login | Access Your Forensic Dashboard',
    description: 'Login to your SIGMACODE account and access enterprise-grade blockchain forensic tools, transaction tracing, and compliance monitoring.',
    keywords: ['blockchain forensics login', 'crypto compliance dashboard', 'secure forensic platform'],
    noindex: true,
  },
  dashboard: {
    title: 'Dashboard | Blockchain Forensics Workspace',
    description: 'Your centralized forensic workspace with live metrics, quick actions, and access to all investigation tools across 100+ blockchains.',
    keywords: ['forensic dashboard', 'blockchain workspace', 'investigation tools'],
    noindex: true,
  },
  trace: {
    title: 'Transaction Tracing | Multi-Chain Blockchain Forensics',
    description: 'Trace cryptocurrency transactions across 100+ blockchains. Forward & backward tracing with bridge detection, mixing service identification, and risk scoring.',
    keywords: ['transaction tracing', 'crypto transaction tracking', 'blockchain transaction analysis', 'forward backward tracing'],
  },
  investigator: {
    title: 'Graph Investigator | Visual Blockchain Analysis',
    description: 'Interactive graph-based investigation tool with entity resolution, wallet clustering, and visual relationship mapping for complex blockchain forensic cases.',
    keywords: ['graph analytics', 'blockchain graph analysis', 'entity resolution', 'wallet clustering'],
  },
  cases: {
    title: 'Case Management | Organize Blockchain Investigations',
    description: 'Professional case management with evidence chain-of-custody, eIDAS signatures, PDF export, and collaborative investigation workflows.',
    keywords: ['case management', 'forensic cases', 'evidence management', 'investigation workflow'],
  },
}

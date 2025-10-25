import { useEffect } from 'react'
import { useLocation } from 'react-router-dom'
import { useI18n } from '@/contexts/I18nContext'

export interface SEOConfig {
  // Basic
  title: string
  description: string
  keywords?: string[]
  
  // Open Graph (Facebook, LinkedIn)
  og_type?: 'website' | 'article' | 'product'
  og_title?: string
  og_description?: string
  og_image?: string
  og_image_alt?: string
  og_image_width?: number
  og_image_height?: number
  
  // Twitter Cards
  twitter_card?: 'summary' | 'summary_large_image' | 'player'
  twitter_title?: string
  twitter_description?: string
  twitter_image?: string
  twitter_creator?: string
  
  // Advanced
  canonical?: string
  robots?: 'index,follow' | 'noindex,nofollow'
  author?: string
  publish_date?: string
  modified_date?: string
}

export function useEnhancedSEO(config: SEOConfig) {
  const location = useLocation()
  const { currentLanguage } = useI18n()
  const lang = currentLanguage || 'en'
  
  useEffect(() => {
    const origin = window.location.origin
    const currentUrl = `${origin}${location.pathname}${location.search}`
    
    // === 1. BASIC META ===
    document.title = config.title
    updateMetaTag('description', config.description)
    
    if (config.keywords && config.keywords.length > 0) {
      updateMetaTag('keywords', config.keywords.join(', '))
    }
    
    if (config.author) {
      updateMetaTag('author', config.author)
    }
    
    // === 2. OPEN GRAPH (Critical für Social Shares!) ===
    updateMetaTag('og:type', config.og_type || 'website', 'property')
    updateMetaTag('og:title', config.og_title || config.title, 'property')
    updateMetaTag('og:description', config.og_description || config.description, 'property')
    updateMetaTag('og:url', currentUrl, 'property')
    updateMetaTag('og:site_name', 'SIGMACODE Blockchain Forensics', 'property')
    updateMetaTag('og:locale', lang.replace('-', '_'), 'property')
    
    // OG Image (wichtig für CTR!)
    const ogImage = config.og_image || '/og-default.png'
    updateMetaTag('og:image', `${origin}${ogImage}`, 'property')
    
    if (config.og_image_alt) {
      updateMetaTag('og:image:alt', config.og_image_alt, 'property')
    }
    if (config.og_image_width) {
      updateMetaTag('og:image:width', String(config.og_image_width), 'property')
    }
    if (config.og_image_height) {
      updateMetaTag('og:image:height', String(config.og_image_height), 'property')
    }
    
    // === 3. TWITTER CARDS (Critical für Twitter/X Shares!) ===
    updateMetaTag('twitter:card', config.twitter_card || 'summary_large_image')
    updateMetaTag('twitter:site', '@sigmacode')
    updateMetaTag('twitter:creator', config.twitter_creator || '@sigmacode')
    updateMetaTag('twitter:title', config.twitter_title || config.title)
    updateMetaTag('twitter:description', config.twitter_description || config.description)
    
    const twitterImage = config.twitter_image || config.og_image || '/twitter-card.png'
    updateMetaTag('twitter:image', `${origin}${twitterImage}`)
    
    // === 4. CANONICAL URL (Prevent Duplicate Content!) ===
    const canonicalUrl = config.canonical || currentUrl.split('?')[0]  // Remove query params
    updateLinkTag('canonical', canonicalUrl)
    
    // === 5. HREFLANG (43 Sprachen!) ===
    const supportedLanguages = ['en', 'de', 'es', 'fr', 'it', 'pt', 'zh', 'ja', 'ko', 'ar']
    supportedLanguages.forEach(langCode => {
      updateLinkTag(
        'alternate',
        `${origin}/${langCode}${location.pathname}`,
        { hreflang: langCode }
      )
    })
    
    // x-default für Auto-Detection
    updateLinkTag('alternate', `${origin}/en${location.pathname}`, { hreflang: 'x-default' })
    
    // === 6. ROBOTS ===
    updateMetaTag('robots', config.robots || 'index,follow')
    
    // === 7. MOBILE OPTIMIZATION ===
    updateMetaTag('viewport', 'width=device-width, initial-scale=1, maximum-scale=5')
    updateMetaTag('theme-color', '#6366f1')  // Primary brand color
    updateMetaTag('apple-mobile-web-app-capable', 'yes')
    updateMetaTag('apple-mobile-web-app-status-bar-style', 'black-translucent')
    
    // === 8. PERFORMANCE HINTS ===
    updateLinkTag('preconnect', 'https://fonts.googleapis.com')
    updateLinkTag('preconnect', 'https://fonts.gstatic.com', { crossorigin: 'anonymous' })
    updateLinkTag('dns-prefetch', import.meta.env.VITE_API_URL || 'http://localhost:8000')
    
    // === 9. ARTICLE META (if article) ===
    if (config.og_type === 'article') {
      if (config.publish_date) {
        updateMetaTag('article:published_time', config.publish_date, 'property')
      }
      if (config.modified_date) {
        updateMetaTag('article:modified_time', config.modified_date, 'property')
      }
      if (config.author) {
        updateMetaTag('article:author', config.author, 'property')
      }
    }
    
  }, [config, location, lang])
}

function updateMetaTag(name: string, content: string, attribute: 'name' | 'property' = 'name') {
  let meta = document.querySelector(`meta[${attribute}="${name}"]`) as HTMLMetaElement
  
  if (!meta) {
    meta = document.createElement('meta')
    meta.setAttribute(attribute, name)
    document.head.appendChild(meta)
  }
  
  meta.content = content
}

function updateLinkTag(rel: string, href: string, attrs: Record<string, string> = {}) {
  const selector = `link[rel="${rel}"]${attrs.hreflang ? `[hreflang="${attrs.hreflang}"]` : ''}`
  let link = document.querySelector(selector) as HTMLLinkElement
  
  if (!link) {
    link = document.createElement('link')
    link.rel = rel
    Object.entries(attrs).forEach(([k, v]) => link.setAttribute(k, v))
    document.head.appendChild(link)
  }
  
  link.href = href
}

import React, { useEffect, useRef } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { track, pageview } from '@/lib/analytics'
import { useI18n } from '@/contexts/I18nContext'

export default function ChatbotLandingPage() {
  const { t, i18n } = useTranslation()
  const { currentLanguage } = useI18n()
  const location = useLocation()
  const heroRef = useRef<HTMLDivElement>(null)
  const featuresRef = useRef<HTMLDivElement>(null)
  const howItWorksRef = useRef<HTMLDivElement>(null)
  const pricingRef = useRef<HTMLDivElement>(null)

  // Schema.org JSON-LD
  const schemaOrg = {
    '@context': 'https://schema.org',
    '@type': 'SoftwareApplication',
    name: 'SIGMACODE AI Chatbot for Web3',
    applicationCategory: 'BusinessApplication',
    operatingSystem: 'Web',
    inLanguage: currentLanguage,
    offers: [
      {
        '@type': 'Offer',
        price: '0',
        priceCurrency: 'USD',
        name: 'Community Plan'
      },
      {
        '@type': 'Offer',
        price: '99',
        priceCurrency: 'USD',
        name: 'Plus Plan'
      },
      {
        '@type': 'Offer',
        price: '299',
        priceCurrency: 'USD',
        name: 'Pro Plan'
      },
      {
        '@type': 'Offer',
        price: '999',
        priceCurrency: 'USD',
        name: 'Enterprise Plan'
      }
    ],
    aggregateRating: {
      '@type': 'AggregateRating',
      ratingValue: '4.8',
      reviewCount: '127'
    },
    featureList: [
      'Voice Input (43 Languages)',
      'Crypto Payments (30+ Coins)',
      'Blockchain Forensics',
      'Real-Time Risk Scoring',
      'White Label',
      'WebSocket Support'
    ]
  }

  // SEO Meta-Tags setzen
  useEffect(() => {
    const origin = window.location.origin
    const canonicalUrl = `https://forensics.ai/${currentLanguage}/chatbot`
    const url = `${origin}${location.pathname}`
    const localizedOg = `https://forensics.ai/og-chatbot-${currentLanguage}.png`
    const defaultOg = 'https://forensics.ai/og-chatbot.png'

    // Title (lokalisiert mit Default)
    const metaTitle = t('chatbot.meta.title', { defaultValue: 'AI Chatbot für Web3 | Voice, Crypto-Payments & Blockchain-Forensik' })
    document.title = metaTitle

    // Meta Description
    const setOrCreateMeta = (name: string, content: string, property?: boolean) => {
      const attr = property ? 'property' : 'name'
      let meta = document.querySelector(`meta[${attr}="${name}"]`) as HTMLMetaElement
      if (!meta) {
        meta = document.createElement('meta')
        meta.setAttribute(attr, name)
        document.head.appendChild(meta)
      }
      meta.content = content
    }

    const metaDescription = t('chatbot.meta.description', { defaultValue: 'Der einzige AI-Chatbot mit Voice-Input (43 Sprachen), Crypto-Payments (30+ Coins) und integrierter Blockchain-Forensik. Ab $0/Monat. White-Label verfügbar.' })
    setOrCreateMeta('description', metaDescription)
    setOrCreateMeta('keywords', t('chatbot.meta.keywords', { defaultValue: 'chatbot, web3, crypto, blockchain, ai, voice input, crypto payments, forensics, white label' }))
    
    // Open Graph
    setOrCreateMeta('og:type', 'website', true)
    setOrCreateMeta('og:title', t('chatbot.meta.ogTitle', { defaultValue: 'AI Chatbot für Web3 | SIGMACODE' }), true)
    setOrCreateMeta('og:description', t('chatbot.meta.ogDescription', { defaultValue: 'Voice-Input, Crypto-Payments, Real-Time Risk-Scoring und Blockchain-Forensik in einem Widget.' }), true)
    setOrCreateMeta('og:url', canonicalUrl, true)
    // Try locale OG first (CDN/asset may or may not exist); keep default as safe fallback
    setOrCreateMeta('og:image', localizedOg, true)
    
    // Twitter Card
    setOrCreateMeta('twitter:card', 'summary_large_image')
    setOrCreateMeta('twitter:title', t('chatbot.meta.twitterTitle', { defaultValue: 'AI Chatbot für Web3' }))
    setOrCreateMeta('twitter:description', t('chatbot.meta.twitterDescription', { defaultValue: 'Voice-Input, Crypto-Payments & Blockchain-Forensik in einem Widget.' }))
    setOrCreateMeta('twitter:image', localizedOg)

    // Schema.org JSON-LD
    const schemaId = 'chatbot-schema'
    let script = document.head.querySelector(`script[data-schema="${schemaId}"]`) as HTMLScriptElement
    if (!script) {
      script = document.createElement('script')
      script.type = 'application/ld+json'
      script.setAttribute('data-schema', schemaId)
      document.head.appendChild(script)
    }
    script.text = JSON.stringify(schemaOrg)

    // Canonical link
    const setOrCreateLink = (rel: string, href: string, hreflang?: string) => {
      const selector = hreflang ? `link[rel="${rel}"][hreflang="${hreflang}"]` : `link[rel="${rel}"]`
      let link = document.head.querySelector(selector) as HTMLLinkElement | null
      if (!link) {
        link = document.createElement('link')
        link.rel = rel
        if (hreflang) link.hreflang = hreflang
        document.head.appendChild(link)
      }
      link.href = href
    }

    setOrCreateLink('canonical', canonicalUrl)
    // hreflang: alle unterstützten Sprachen + x-default
    const supported = (i18n?.options?.supportedLngs as string[] | undefined) || [currentLanguage]
    const uniqueLangs = Array.from(new Set((supported || []).filter((l) => typeof l === 'string' && l !== 'cimode')))
    uniqueLangs.forEach((lng) => {
      setOrCreateLink('alternate', `https://forensics.ai/${lng}/chatbot`, lng)
    })
    setOrCreateLink('alternate', 'https://forensics.ai/en/chatbot', 'x-default')

    return () => {
      // Cleanup: remove schema on unmount
      const s = document.head.querySelector(`script[data-schema="${schemaId}"]`)
      if (s) s.remove()
    }
  }, [currentLanguage, schemaOrg, location.pathname])

  // Pageview tracking
  useEffect(() => {
    pageview()
    track('chatbot_landing_view', { path: location.pathname })
  }, [])

  // Section view tracking mit Intersection Observer
  useEffect(() => {
    const observerOptions = {
      root: null,
      rootMargin: '0px',
      threshold: 0.5 // 50% sichtbar
    }

    const observerCallback = (entries: IntersectionObserverEntry[]) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          const sectionName = entry.target.getAttribute('data-section')
          if (sectionName) {
            track('section_view', { section: sectionName, page: 'chatbot_landing' })
          }
        }
      })
    }

    const observer = new IntersectionObserver(observerCallback, observerOptions)

    const refs = [heroRef, featuresRef, howItWorksRef, pricingRef]
    refs.forEach((ref) => {
      if (ref.current) observer.observe(ref.current)
    })

    return () => {
      refs.forEach((ref) => {
        if (ref.current) observer.unobserve(ref.current)
      })
    }
  }, [])

  // Analytics helper
  const trackCTA = (action: string, label: string, extra: Record<string, any> = {}) => {
    track('cta_click', { action, label, page: 'chatbot_landing', ...extra })
  }

  return (
    <div className="bg-background text-foreground">
      <section id="hero" ref={heroRef} data-section="hero" className="relative overflow-hidden">
        <div className="absolute inset-0 -z-10 bg-gradient-to-b from-primary/10 via-transparent to-transparent" />
        <div className="container mx-auto max-w-6xl px-4 sm:px-6 pt-20 sm:pt-28 pb-14 sm:pb-20">
          <div className="grid md:grid-cols-2 gap-10 items-center">
            <div>
              <div className="inline-flex items-center gap-2 rounded-full border border-primary/30 bg-primary/10 px-3 py-1 text-xs font-medium text-primary mb-4">
                <span className="inline-block h-2 w-2 rounded-full bg-primary animate-pulse" />
                {t('chatbot.hero.badge', { defaultValue: 'AI Chatbot • Web3 Ready • 43 Sprachen' })}
              </div>
              <h1 className="text-3xl sm:text-5xl font-extrabold tracking-tight leading-tight">
                {t('chatbot.hero.title', { defaultValue: 'Der Chatbot für Web3 mit Blockchain‑Superpowers' })}
              </h1>
              <p className="mt-4 text-base sm:text-lg text-muted-foreground max-w-xl">
                {t('chatbot.hero.subtitle', { defaultValue: 'Voice‑Input, Crypto‑Payments, Real‑Time Risk‑Scoring und integrierte Blockchain‑Forensik. Alles in einem leistungsstarken, einfach zu integrierenden Widget.' })}
              </p>
              <div className="mt-6 flex flex-wrap gap-3">
                <Link 
                  to="../register" 
                  relative="path" 
                  className="inline-flex items-center justify-center rounded-lg bg-primary px-5 py-3 text-white font-semibold shadow-md hover:shadow-lg"
                  onClick={() => trackCTA('click_register', 'hero_cta_primary', { plan: 'free' })}
                >
                  {t('chatbot.cta.startFree', { defaultValue: 'Kostenlos starten' })}
                </Link>
                <a 
                  href="#pricing" 
                  className="inline-flex items-center justify-center rounded-lg border border-border px-5 py-3 font-semibold hover:border-primary/50 hover:text-primary"
                  onClick={() => trackCTA('click_pricing', 'hero_cta_secondary')}
                >
                  {t('chatbot.cta.viewPricing', { defaultValue: 'Preise ansehen' })}
                </a>
              </div>
              <div className="mt-6 grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs text-muted-foreground">
                <div className="rounded-md border border-border/60 px-3 py-2">{t('chatbot.hero.pill.languages', { defaultValue: '43 Sprachen' })}</div>
                <div className="rounded-md border border-border/60 px-3 py-2">{t('chatbot.hero.pill.payments', { defaultValue: 'Crypto‑Payments' })}</div>
                <div className="rounded-md border border-border/60 px-3 py-2">{t('chatbot.hero.pill.risk', { defaultValue: 'Risk‑Scoring' })}</div>
                <div className="rounded-md border border-border/60 px-3 py-2">{t('chatbot.hero.pill.whitelabel', { defaultValue: 'White‑Label' })}</div>
              </div>
            </div>
            <div>
              <div className="relative rounded-2xl border border-primary/30 bg-gradient-to-br from-primary/10 via-background to-background p-1">
                <div className="rounded-xl bg-background/70 backdrop-blur p-4 h-[520px] flex items-center justify-center">
                  <div className="text-center">
                    <div className="text-sm text-muted-foreground mb-3">{t('chatbot.hero.demo', { defaultValue: 'Live‑Demo' })}</div>
                    <div className="rounded-xl border border-dashed border-border p-6">
                      <div className="text-muted-foreground">{t('chatbot.hero.demoHint', { defaultValue: 'Das Chat‑Widget ist global aktiv. Öffne es unten rechts und starte eine Unterhaltung.' })}</div>
                      <div className="mt-3 text-xs text-muted-foreground">{t('chatbot.hero.demoTip', { defaultValue: 'Tipp: Frage nach „Voice‑Input“, „Crypto‑Payment“, „Risk‑Score“.' })}</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section id="features" ref={featuresRef} data-section="features" className="py-14 sm:py-20">
        <div className="container mx-auto max-w-6xl px-4 sm:px-6">
          <h2 className="text-2xl sm:text-3xl font-bold tracking-tight">{t('chatbot.features.title', { defaultValue: 'Alles, was moderne Teams brauchen' })}</h2>
          <p className="mt-2 text-muted-foreground max-w-2xl">{t('chatbot.features.subtitle', { defaultValue: 'Einzigartige Kombination aus AI‑Automation und Blockchain‑Funktionen.' })}
          </p>
          <div className="mt-8 grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {[
              { title: t('chatbot.features.cards.voiceTitle', { defaultValue: 'Voice‑Input (43 Sprachen)' }), desc: t('chatbot.features.cards.voiceDesc', { defaultValue: 'Hands‑Free Chat im Browser – ideal für Mobile und internationale Nutzer.' }) },
              { title: t('chatbot.features.cards.paymentsTitle', { defaultValue: 'Crypto‑Payments (30+ Coins)' }), desc: t('chatbot.features.cards.paymentsDesc', { defaultValue: 'Akzeptiere Zahlungen direkt im Chat – inklusive QR‑Code & Echtzeit‑Status.' }) },
              { title: t('chatbot.features.cards.forensicsTitle', { defaultValue: 'Blockchain‑Forensik' }), desc: t('chatbot.features.cards.forensicsDesc', { defaultValue: 'Address‑Lookup, Transaction‑Tracing und Forensic‑Export – integriert.' }) },
              { title: t('chatbot.features.cards.riskTitle', { defaultValue: 'Risk‑Scoring <100ms' }), desc: t('chatbot.features.cards.riskDesc', { defaultValue: 'Sanctions/Mixer/High‑Risk Detection in Echtzeit per WebSocket.' }) },
              { title: t('chatbot.features.cards.whitelabelTitle', { defaultValue: 'White‑Label' }), desc: t('chatbot.features.cards.whitelabelDesc', { defaultValue: 'Eigenes Branding und Domain – nahtlos in deine Anwendung integrierbar.' }) },
              { title: t('chatbot.features.cards.analyticsTitle', { defaultValue: 'Analytics & A/B' }), desc: t('chatbot.features.cards.analyticsDesc', { defaultValue: 'Conversion‑Optimierung mit Events, Funnels und Experimenten.' }) },
            ].map((f) => (
              <div key={f.title} className="rounded-xl border border-border bg-background p-5 hover:border-primary/40 transition-colors">
                <div className="text-base font-semibold">{f.title}</div>
                <div className="mt-1.5 text-sm text-muted-foreground">{f.desc}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section id="how-it-works" ref={howItWorksRef} data-section="how-it-works" className="py-14 sm:py-20">
        <div className="container mx-auto max-w-6xl px-4 sm:px-6">
          <div className="grid lg:grid-cols-2 gap-10 items-center">
            <div>
              <h3 className="text-xl sm:text-2xl font-bold">{t('chatbot.how.title', { defaultValue: 'Wie es funktioniert' })}</h3>
              <ol className="mt-4 space-y-3 text-sm">
                <li className="rounded-lg border border-border p-3"><span className="font-semibold">{t('chatbot.how.step1.title', { defaultValue: 'Sign‑Up' })}</span> – {t('chatbot.how.step1.desc', { defaultValue: 'Account anlegen, API‑Key erhalten.' })}</li>
                <li className="rounded-lg border border-border p-3"><span className="font-semibold">{t('chatbot.how.step2.title', { defaultValue: 'Einbinden' })}</span> – {t('chatbot.how.step2.desc', { defaultValue: '1 Script‑Tag in deine Seite, Konfiguration optional.' })}</li>
                <li className="rounded-lg border border-border p-3"><span className="font-semibold">{t('chatbot.how.step3.title', { defaultValue: 'Starten' })}</span> – {t('chatbot.how.step3.desc', { defaultValue: 'Chat läuft sofort, Voice/Payments/AI ready.' })}</li>
              </ol>
              <div className="mt-5 text-xs text-muted-foreground">
                {t('chatbot.how.example', { defaultValue: 'Beispiel:' })}
                <pre className="mt-2 rounded-lg border border-border p-3 overflow-x-auto text-[11px]"><code>{`<script src="https://chat.forensics.ai/widget.js"></script>
<script>
  ForensicsChatbot.init({ apiKey: 'YOUR_API_KEY', language: 'de', theme: 'dark' })
</script>`}</code></pre>
              </div>
            </div>
            <div>
              <div className="rounded-xl border border-primary/30 bg-gradient-to-br from-primary/10 via-background to-background p-1">
                <div className="rounded-lg bg-background/70 backdrop-blur p-4">
                  <div className="grid grid-cols-2 gap-3 text-xs">
                    <div className="rounded-md border border-border/60 p-3"><div className="text-muted-foreground">Sanctions‑Check</div><div className="font-semibold">OFAC/EU/UK/UN</div></div>
                    <div className="rounded-md border border-border/60 p-3"><div className="text-muted-foreground">Chains</div><div className="font-semibold">35+ Chains</div></div>
                    <div className="rounded-md border border-border/60 p-3"><div className="text-muted-foreground">Payments</div><div className="font-semibold">30+ Coins</div></div>
                    <div className="rounded-md border border-border/60 p-3"><div className="text-muted-foreground">Latency</div><div className="font-semibold">&lt; 100ms</div></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section id="pricing" ref={pricingRef} data-section="pricing" className="py-14 sm:py-20">
        <div className="container mx-auto max-w-6xl px-4 sm:px-6">
          <h2 className="text-2xl sm:text-3xl font-bold tracking-tight">{t('chatbot.pricing.title', { defaultValue: 'Preise' })}</h2>
          <p className="mt-2 text-muted-foreground max-w-2xl">{t('chatbot.pricing.subtitle', { defaultValue: 'Fair, transparent und skalierbar. Monatlich kündbar.' })}</p>
          <div className="mt-8 grid md:grid-cols-2 lg:grid-cols-4 gap-5">
            {[
              { name: t('chatbot.pricing.tiers.community.name', { defaultValue: 'Community' }), price: 'FREE', features: [t('chatbot.pricing.tiers.community.f1', { defaultValue: '1.000 Nachrichten' }), t('chatbot.pricing.tiers.community.f2', { defaultValue: 'Basic AI' }), t('chatbot.pricing.tiers.community.f3', { defaultValue: 'Basis‑Analytics' })], cta: t('chatbot.pricing.tiers.community.cta', { defaultValue: 'Start Free' }), href: '../register', plan: 'community' },
              { name: t('chatbot.pricing.tiers.plus.name', { defaultValue: 'Plus' }), price: '$99', features: [t('chatbot.pricing.tiers.plus.f1', { defaultValue: '50k Nachrichten' }), t('chatbot.pricing.tiers.plus.f2', { defaultValue: 'Voice (43)' }), t('chatbot.pricing.tiers.plus.f3', { defaultValue: 'Mehrsprachig' })], cta: t('chatbot.pricing.tiers.plus.cta', { defaultValue: 'Upgrade' }), href: '../register', plan: 'plus' },
              { name: t('chatbot.pricing.tiers.pro.name', { defaultValue: 'Pro' }), price: '$299', features: [t('chatbot.pricing.tiers.pro.f1', { defaultValue: 'Unlimited' }), t('chatbot.pricing.tiers.pro.f2', { defaultValue: 'Crypto‑Payments' }), t('chatbot.pricing.tiers.pro.f3', { defaultValue: 'Forensik‑Tools' })], cta: t('chatbot.pricing.tiers.pro.cta', { defaultValue: 'Get Pro' }), href: '../register', plan: 'pro' },
              { name: t('chatbot.pricing.tiers.enterprise.name', { defaultValue: 'Enterprise' }), price: '$999', features: [t('chatbot.pricing.tiers.enterprise.f1', { defaultValue: 'White‑Label' }), t('chatbot.pricing.tiers.enterprise.f2', { defaultValue: 'Custom‑Domain' }), t('chatbot.pricing.tiers.enterprise.f3', { defaultValue: 'SLA 99.9%' })], cta: t('chatbot.pricing.tiers.enterprise.cta', { defaultValue: 'Contact' }), href: '../about', plan: 'enterprise' },
            ].map((p) => (
              <div key={p.name} className="rounded-xl border border-border bg-background p-5 flex flex-col">
                <div className="text-sm text-muted-foreground">{p.name}</div>
                <div className="mt-1 text-3xl font-extrabold">{p.price}<span className="text-base font-semibold text-muted-foreground">/mo</span></div>
                <ul className="mt-3 space-y-2 text-sm text-muted-foreground">
                  {p.features.map((f) => (<li key={f} className="flex items-center gap-2"><span className="h-1.5 w-1.5 rounded-full bg-primary" />{f}</li>))}
                </ul>
                <a 
                  href={p.href} 
                  className="mt-5 inline-flex items-center justify-center rounded-lg bg-primary px-4 py-2.5 text-white font-semibold hover:shadow-lg"
                  onClick={() => trackCTA('click_plan', p.cta, { plan: p.plan, price: p.price })}
                >{p.cta}</a>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="py-12">
        <div className="container mx-auto max-w-6xl px-4 sm:px-6 text-center">
          <h3 className="text-xl sm:text-2xl font-bold">{t('chatbot.final.title', { defaultValue: 'Bereit loszulegen?' })}</h3>
          <p className="mt-2 text-sm text-muted-foreground">{t('chatbot.final.subtitle', { defaultValue: 'Starte kostenlos in 30 Sekunden. Keine Kreditkarte nötig.' })}</p>
          <div className="mt-5">
            <Link 
              to="../register" 
              relative="path" 
              className="inline-flex items-center justify-center rounded-lg bg-primary px-6 py-3 text-white font-semibold shadow-md hover:shadow-lg"
              onClick={() => trackCTA('click_register', 'final_cta', { plan: 'free' })}
            >
              {t('chatbot.final.cta', { defaultValue: 'Jetzt kostenlos starten' })}
            </Link>
          </div>
        </div>
      </section>
    </div>
  )
}

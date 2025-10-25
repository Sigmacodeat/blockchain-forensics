import React from 'react'
import { useTranslation } from 'react-i18next'
import { usePageMeta } from '@/hooks/usePageMeta'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Building2, Mail, Phone, Globe } from 'lucide-react'
import LinkLocalized from '@/components/LinkLocalized'

/**
 * Impressum (DE) / Legal Notice - PFLICHT für Deutschland, Österreich, Schweiz
 * § 5 TMG (Telemediengesetz) - Anbieterkennzeichnung
 */
export default function ImpressumPage() {
  const { t, i18n } = useTranslation()
  const lang = i18n.language || 'en'
  
  usePageMeta(
    t('legal.impressum.seo.title', 'Impressum | SIGMACODE'),
    t('legal.impressum.seo.description', 'Rechtliche Informationen und Anbieterkennzeichnung gemäß § 5 TMG')
  )

  // Nur für DE, AT, CH anzeigen (Rechtspflicht)
  if (!['de', 'de-DE', 'de-AT', 'de-CH'].includes(lang)) {
    return (
      <div className="min-h-screen bg-background">
        <div className="container mx-auto max-w-4xl px-4 py-16">
          <Card>
            <CardHeader>
              <CardTitle>{t('legal.impressum.notice_de_only.title', 'Legal Notice')}</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground">
                {t('legal.impressum.notice_de_only.desc', 'Diese Seite ist nur für deutschsprachige Länder erforderlich. Bitte siehe stattdessen Datenschutz und AGB.')} {' '}
                <LinkLocalized to="/legal/privacy" className="text-primary underline">Privacy Policy</LinkLocalized> {' '}
                {t('common.and', 'und')} {' '}
                <LinkLocalized to="/legal/terms" className="text-primary underline">Terms of Service</LinkLocalized>.
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto max-w-4xl px-4 py-16">
        <div className="mb-8">
          <h1 className="text-4xl font-bold mb-4">{t('legal.impressum.title', 'Impressum')}</h1>
          <p className="text-muted-foreground">{t('legal.impressum.lead', 'Angaben gemäß § 5 TMG (Telemediengesetz)')}</p>
        </div>

        {/* Structured Data (JSON-LD) */}
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{
            __html: JSON.stringify({
              '@context': 'https://schema.org',
              '@type': 'NGO',
              name: 'Verein Metanetwork',
              legalName: 'Verein Metanetwork',
              identifier: {
                '@type': 'PropertyValue',
                name: 'ZVR',
                value: '123456789'
              },
              url: 'https://metanetwork.at',
              email: 'info@metanetwork.at',
              telephone: '+43 1 234 5678',
              address: {
                '@type': 'PostalAddress',
                streetAddress: 'Stephansplatz 1',
                postalCode: '1010',
                addressLocality: 'Wien',
                addressCountry: 'AT'
              },
              sameAs: ['https://metanetwork.at']
            })
          }}
        />

        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Building2 className="h-5 w-5" />
                {t('legal.impressum.sections.provider.title', 'Anbieter')}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <p className="font-semibold">{t('legal.impressum.sections.provider.name', 'Verein Metanetwork')}</p>
              <p>{t('legal.impressum.sections.provider.street', 'Stephansplatz 1')}</p>
              <p>{t('legal.impressum.sections.provider.postal', '1010 Wien')}</p>
              <p>{t('legal.impressum.sections.provider.country', 'Österreich')}</p>
              <div className="pt-4 space-y-1 text-sm text-muted-foreground">
                <p><strong>{t('legal.impressum.sections.provider.zvr', 'ZVR‑Zahl')}:</strong> 123456789</p>
                <p><strong>{t('legal.impressum.sections.provider.representatives', 'Vertretungsbefugte')}:</strong> Alex Beispiel (Obmann/Obfrau), Chris Muster (Kassier)</p>
              </div>
            </CardContent>
          </Card>

          {/* Kontakt */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Mail className="h-5 w-5" />
                {t('legal.impressum.sections.contact.title', 'Kontakt')}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <div className="flex items-center gap-2">
                <Mail className="h-4 w-4 text-muted-foreground" />
                <a href="mailto:info@metanetwork.at" className="text-primary hover:underline">info@metanetwork.at</a>
              </div>
              <div className="flex items-center gap-2">
                <Phone className="h-4 w-4 text-muted-foreground" />
                <a href="tel:+4312345678" className="text-primary hover:underline">+43 1 234 5678</a>
              </div>
              <div className="flex items-center gap-2">
                <Globe className="h-4 w-4 text-muted-foreground" />
                <a href="https://metanetwork.at" className="text-primary hover:underline">www.metanetwork.at</a>
              </div>
            </CardContent>
          </Card>

          {/* Verantwortlich für den Inhalt */}
          <Card>
            <CardHeader>
              <CardTitle>{t('legal.impressum.sections.content_resp.title', 'Verantwortlich für den Inhalt nach § 55 Abs. 2 RStV')}</CardTitle>
            </CardHeader>
            <CardContent>
              <p>Alex Beispiel</p>
              <p>{t('legal.impressum.sections.provider.name', 'Verein Metanetwork')}</p>
              <p>{`${t('legal.impressum.sections.provider.street', 'Stephansplatz 1')}, ${t('legal.impressum.sections.provider.postal', '1010 Wien')}, ${t('legal.impressum.sections.provider.country', 'Österreich')}`}</p>
            </CardContent>
          </Card>

          {/* EU-Streitschlichtung */}
          <Card>
            <CardHeader>
              <CardTitle>{t('legal.impressum.sections.odr.title', 'EU‑Streitschlichtung')}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              <p>{t('legal.impressum.sections.odr.desc', 'Die Europäische Kommission stellt eine Plattform zur Online‑Streitbeilegung (OS) bereit:')}</p>
              <a 
                href={t('legal.impressum.sections.odr.link', 'https://ec.europa.eu/consumers/odr')}
                target="_blank" 
                rel="noopener noreferrer"
                className="text-primary hover:underline block"
              >
                {t('legal.impressum.sections.odr.link', 'https://ec.europa.eu/consumers/odr')}
              </a>
              <p className="pt-2">{t('legal.impressum.sections.odr.foot', 'Unsere E‑Mail‑Adresse finden Sie oben im Impressum.')}</p>
            </CardContent>
          </Card>

          {/* Verbraucherstreitbeilegung */}
          <Card>
            <CardHeader>
              <CardTitle>{t('legal.impressum.sections.consumer.title', 'Verbraucherstreitbeilegung / Universalschlichtungsstelle')}</CardTitle>
            </CardHeader>
            <CardContent className="text-sm">
              <p>{t('legal.impressum.sections.consumer.desc', 'Wir sind nicht bereit oder verpflichtet, an Streitbeilegungsverfahren vor einer Verbraucherschlichtungsstelle teilzunehmen.')}</p>
            </CardContent>
          </Card>

          {/* Haftungsausschluss */}
          <Card>
            <CardHeader>
              <CardTitle>{t('legal.impressum.sections.liability_content.title', 'Haftung für Inhalte')}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              <p>{t('legal.impressum.sections.liability_content.p1')}</p>
              <p>{t('legal.impressum.sections.liability_content.p2')}</p>
            </CardContent>
          </Card>

          {/* Haftung für Links */}
          <Card>
            <CardHeader>
              <CardTitle>{t('legal.impressum.sections.liability_links.title', 'Haftung für Links')}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              <p>{t('legal.impressum.sections.liability_links.p1')}</p>
              <p>{t('legal.impressum.sections.liability_links.p2')}</p>
            </CardContent>
          </Card>

          {/* Urheberrecht */}
          <Card>
            <CardHeader>
              <CardTitle>{t('legal.impressum.sections.copyright.title', 'Urheberrecht')}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              <p>{t('legal.impressum.sections.copyright.p1')}</p>
              <p>{t('legal.impressum.sections.copyright.p2')}</p>
            </CardContent>
          </Card>

          <div className="text-xs text-muted-foreground pt-4">
            <p>
              {t('legal.impressum.sections.source.title', 'Quelle')}: {t('legal.impressum.sections.source.desc', 'Erstellt mit Hilfe eines Impressum‑Generators.')}
            </p>
            <p className="mt-2">Stand: {new Date().toLocaleDateString('de-DE')}</p>
          </div>
        </div>
      </div>
    </div>
  )
}

import React from 'react'
import { Helmet } from 'react-helmet-async'
import { useTranslation } from 'react-i18next'

export default function BusinessplanPage() {
  const { t } = useTranslation()
  return (
    <div className="container mx-auto max-w-4xl px-4 sm:px-6 py-10">
      <Helmet>
        <title>{t('navigation.businessplan', { defaultValue: 'Businessplan & Förderung' })} · SIGMACODE</title>
        <meta name="description" content={t('seo.businessplan.description', { defaultValue: 'Unser Businessplan, Förderstrategie und Roadmap für die Blockchain-Forensics Plattform.' }) as string} />
      </Helmet>

      <h1 className="text-2xl sm:text-3xl font-bold tracking-tight">{t('navigation.businessplan', { defaultValue: 'Businessplan & Förderung' })}</h1>
      <p className="mt-3 text-muted-foreground">
        {t('businessplan.intro', { defaultValue: 'Hier findest du eine Zusammenfassung unserer Strategie, Roadmap und Förderpläne. Für vollständige Details kontaktiere uns bitte direkt.' })}
      </p>

      <div className="mt-8 space-y-4 text-sm leading-6">
        <p>
          {t('businessplan.summary.1', { defaultValue: 'Die Plattform fokussiert auf Forensik, Compliance und Investigation mit Echtzeit-Analysen, Graph-Modellen und AI-Agenten.' })}
        </p>
        <p>
          {t('businessplan.summary.2', { defaultValue: 'Roadmap-Highlights: Multi-Chain-Tracing, Risk-Scoring, Intelligence-Netzwerk, Compliance-Module, Reports & Automatisierung.' })}
        </p>
        <p>
          {t('businessplan.summary.3', { defaultValue: 'Förderstrategie umfasst Innovationsförderungen und Partnerschaften mit öffentlichen Institutionen und Unternehmen.' })}
        </p>
      </div>

      <div className="mt-10">
        <a
          href={"mailto:hello@sigmacode.io?subject=" + encodeURIComponent('Businessplan & Förderung – Anfrage')}
          className="inline-flex items-center px-4 py-2 rounded-md bg-primary text-primary-foreground hover:opacity-95"
        >
          {t('businessplan.cta.contact', { defaultValue: 'Kontakt aufnehmen' })}
        </a>
      </div>
    </div>
  )
}

import React from 'react'
import { useTranslation } from 'react-i18next'
import { useI18n } from '@/contexts/I18nContext'
import LinkLocalized from '@/components/LinkLocalized'
import { Button } from '@/components/ui/button'
import { Home, ArrowLeft, Search } from 'lucide-react'

export default function NotFoundPage() {
  const { t } = useTranslation()
  const { currentLanguage } = useI18n()

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <div className="max-w-2xl w-full text-center">
        <div className="mb-8">
          <h1 className="text-9xl font-bold text-primary/20 mb-4">404</h1>
          <h2 className="text-3xl md:text-4xl font-bold text-foreground mb-4">
            {t('error.404.title', 'Seite nicht gefunden')}
          </h2>
          <p className="text-lg text-muted-foreground mb-8">
            {t('error.404.description', 'Die von Ihnen gesuchte Seite existiert nicht oder wurde verschoben.')}
          </p>
        </div>
        
        <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
          <LinkLocalized to="/">
            <Button size="lg" className="gap-2">
              <Home className="w-5 h-5" />
              {t('error.404.home', 'Zur Startseite')}
            </Button>
          </LinkLocalized>
          
          <Button 
            variant="outline" 
            size="lg" 
            onClick={() => window.history.back()}
            className="gap-2"
          >
            <ArrowLeft className="w-5 h-5" />
            {t('error.404.back', 'Zurück')}
          </Button>
        </div>

        <div className="mt-12 p-6 bg-muted/50 rounded-lg">
          <Search className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
          <h3 className="font-semibold mb-2">{t('error.404.help.title', 'Benötigen Sie Hilfe?')}</h3>
          <p className="text-sm text-muted-foreground">
            {t('error.404.help.description', 'Besuchen Sie unsere Hauptseite oder kontaktieren Sie den Support.')}
          </p>
        </div>
      </div>
    </div>
  )
}

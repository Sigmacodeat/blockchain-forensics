import WebKpis from '@/components/analytics/WebKpis'
import { useTranslation } from 'react-i18next'

export default function WebAnalyticsPage() {
  const { t } = useTranslation()
  return (
    <div className="max-w-6xl mx-auto p-4 sm:p-6 lg:p-8">
      <h1 className="text-2xl font-bold mb-6">{t('web_analytics.title', 'Web Analytics')}</h1>
      <WebKpis />
    </div>
  )
}

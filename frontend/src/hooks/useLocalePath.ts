import { useTranslation } from 'react-i18next'

export function useLocalePath() {
  const { i18n } = useTranslation()
  const lang = i18n.language || 'en'
  return (path: string) => {
    const normalized = path.startsWith('/') ? path : `/${path}`
    const stripped = normalized.replace(/^\/[a-zA-Z]{2}(?:-[A-Z]{2})?\b/, '') || '/'
    return `/${lang}${stripped}`
  }
}

import { useEffect } from 'react'

/**
 * Setzt den Seitentitel und optional die Meta-Description ohne zusätzliche Libraries.
 * Titel wird beim Unmount auf den vorherigen Wert zurückgesetzt.
 * Wenn keine vorhandene Description-Meta vorhanden ist, wird sie temporär angelegt.
 */
export function usePageMeta(title: string, description?: string) {
  useEffect(() => {
    const prevTitle = document.title
    document.title = title

    let created = false
    let meta = document.querySelector('meta[name="description"]') as HTMLMetaElement | null
    if (!meta) {
      meta = document.createElement('meta')
      meta.name = 'description'
      created = true
    }
    if (meta) {
      meta.content = description || ''
      if (created) document.head.appendChild(meta)
    }

    return () => {
      document.title = prevTitle
      if (created && meta && meta.parentNode) {
        meta.parentNode.removeChild(meta)
      }
    }
  }, [title, description])
}

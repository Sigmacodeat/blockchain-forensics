import { useEffect } from 'react'

/**
 * Fügt ein JSON-LD Script-Tag für strukturierte Daten hinzu.
 * Wenn mehrere Hooks verwendet werden, werden mehrere Script-Tags hinzugefügt.
 */
export function useJsonLd(id: string, data: Record<string, any>) {
  useEffect(() => {
    const script = document.createElement('script')
    script.type = 'application/ld+json'
    script.id = id
    script.text = JSON.stringify(data)
    document.head.appendChild(script)

    return () => {
      if (script && script.parentNode) script.parentNode.removeChild(script)
    }
  }, [id, data])
}

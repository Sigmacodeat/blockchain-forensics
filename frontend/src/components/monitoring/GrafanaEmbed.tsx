import React from 'react'

interface GrafanaEmbedProps {
  src: string
  title?: string
  height?: number | string
  className?: string
}

export default function GrafanaEmbed({ src, title = 'Monitoring Dashboard', height = 900, className = '' }: GrafanaEmbedProps) {
  return (
    <section aria-label={title} className={className}>
      <div className="sr-only" aria-live="polite">{title}</div>
      <iframe
        title={title}
        src={src}
        className="w-full rounded-lg border border-gray-300 dark:border-slate-700 bg-white dark:bg-slate-900 shadow-md"
        style={{ height: typeof height === 'number' ? `${height}px` : height }}
        loading="lazy"
        referrerPolicy="no-referrer"
        allow="fullscreen"
      />
    </section>
  )
}

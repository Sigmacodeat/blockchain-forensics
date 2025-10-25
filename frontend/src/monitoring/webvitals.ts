type Metric = {
  name: string
  id: string
  value: number
  rating?: string
}

function hasAnalyticsConsent(): boolean {
  try {
    const raw = localStorage.getItem('cookie_consent')
    if (!raw) return false
    const val = JSON.parse(raw)
    return !!val && val.version === 1 && val.analytics === true
  } catch {
    return false
  }
}

function send(metric: Metric) {
  // Respect consent at send-time as well
  if (!hasAnalyticsConsent()) return
  try {
    const body = JSON.stringify({
      name: metric.name,
      id: metric.id,
      value: metric.value,
      rating: (metric as any).rating,
      navigationType: (typeof performance !== 'undefined' && performance.getEntriesByType
        ? (performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming | undefined)?.type
        : undefined),
      ts: Date.now(),
    })
    const configured = (import.meta as any)?.env?.VITE_WEBVITALS_ENDPOINT
    const endpoint = typeof configured === 'string' && configured.length > 0 ? configured : '/api/v1/metrics/webvitals'

    // Prefer sendBeacon if available; fall back to fetch if it returns false
    if (typeof navigator !== 'undefined' && typeof navigator.sendBeacon === 'function') {
      try {
        const blob = new Blob([body], { type: 'application/json' })
        const ok = navigator.sendBeacon(endpoint, blob)
        if (ok) return
        // if sendBeacon refused, fall through to fetch
      } catch {
        // fall through to fetch
      }
    }

    // Fallback: fetch with keepalive when available
    if (typeof fetch === 'function') {
      fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-Path': typeof location !== 'undefined' ? location.pathname : '/' },
        body,
        // keepalive can throw in some environments; guard it
        ...(typeof Request !== 'undefined' ? { keepalive: true as any } : {}),
      }).catch(() => {})
    }
  } catch {
    // noop
  }
}

export async function initWebVitals() {
  try {
    const mod: any = await import(/* @vite-ignore */ 'web-vitals')
    mod.onCLS?.(send)
    mod.onFID?.(send)
    mod.onLCP?.(send)
    mod.onINP?.(send)
    mod.onTTFB?.(send)
  } catch {
    // web-vitals not installed or failed to load; silently ignore
  }
}

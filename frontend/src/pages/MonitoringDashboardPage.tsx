import React from 'react'
import GrafanaEmbed from '@/components/monitoring/GrafanaEmbed'

// Prefer an explicit URL from env. Fallback to constructing from base URL and a default dashboard UID.
const DASHBOARD_URL =
  (import.meta as any).env?.VITE_GRAFANA_DASHBOARD_URL ||
  (() => {
    const base = (import.meta as any).env?.VITE_GRAFANA_URL || 'http://localhost:3000'
    // Default to the main system dashboard we provision with panels including Webhooks
    // Change UID/path if your Grafana assigns a different one.
    const path = '/d/main/blockchain-forensics-complete-system-metrics'
    const params = '?orgId=1&refresh=10s&kiosk=tv'
    return `${base}${path}${params}`
  })()

export default function MonitoringDashboardPage() {
  return (
    <div className="max-w-[1600px] mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <header className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900" id="monitoring-dashboard-title">
          Monitoring Dashboard
        </h1>
        <p className="text-gray-600" id="monitoring-dashboard-desc">
          Live-Metriken und Alerts aus Prometheus/Grafana. Die Ansicht ist tastaturbedienbar und für Screenreader optimiert.
        </p>
      </header>
      <GrafanaEmbed src={DASHBOARD_URL} title="Grafana Monitoring" height={1000} className="outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500" />
    </div>
  )
}

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import {
  TrendingUp,
  Activity,
  Radio,
  Zap,
  BarChart3,
  Eye,
  Sparkles,
  Clock,
  ArrowUpRight,
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import GrafanaEmbed from '@/components/monitoring/GrafanaEmbed';

const DASHBOARDS = [
  {
    id: 'system',
    title: 'System Metrics',
    description: 'Vollständige Übersicht über Requests, Latenz, Fehlerquoten und Infrastruktur',
    url: (import.meta as any).env?.VITE_GRAFANA_SYSTEM_URL || 'http://localhost:3001/d/main/blockchain-forensics-complete-system-metrics?orgId=1&refresh=10s&kiosk=tv',
    icon: Activity,
    gradient: 'from-blue-500 to-cyan-500',
    badge: 'Core',
  },
  {
    id: 'agent',
    title: 'Agent Metrics',
    description: 'Metriken des Agenten-/AI-Layers (Tools, Requests, Latenzen, Fehlerquoten)',
    url: (import.meta as any).env?.VITE_GRAFANA_AGENT_URL || 'http://localhost:3001/d/agent/agent?orgId=1&refresh=10s&kiosk=tv',
    icon: Sparkles,
    gradient: 'from-primary-500 to-purple-500',
    badge: 'AI',
  },
  {
    id: 'webhooks',
    title: 'Webhooks Dashboard',
    description: 'Spezifische Metriken für Listener (Requests, Signaturen) und Worker (Processed, DLQ)',
    url: (import.meta as any).env?.VITE_GRAFANA_WEBHOOKS_URL || 'http://localhost:3001/d/webhooks-node/webhooks-node-overview?orgId=1&refresh=10s&kiosk=tv',
    icon: Radio,
    gradient: 'from-green-500 to-emerald-500',
    badge: 'Events',
  },
  {
    id: 'webvitals',
    title: 'Web Vitals',
    description: 'Performance-Metriken wie LCP, FID und CLS für die Web-App',
    url: (import.meta as any).env?.VITE_GRAFANA_WEBVITALS_URL || 'http://localhost:3001/d/webvitals/web-vitals?orgId=1&refresh=10s&kiosk=tv',
    icon: Zap,
    gradient: 'from-orange-500 to-red-500',
    badge: 'Performance',
  },
];

export default function DashboardsOverviewPage() {
  const [activeTab, setActiveTab] = useState('system');
  const { t } = useTranslation();

  const activeDashboard = DASHBOARDS.find((d) => d.id === activeTab);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-slate-100 dark:from-slate-950 dark:via-slate-900 dark:to-slate-950">
      <div className="container mx-auto max-w-[1800px] px-4 sm:px-6 lg:px-8 py-8">
        {/* Skip to content */}
        <a
          href="#dashboard-content"
          className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-primary-600 focus:text-white focus:rounded-md"
        >
          Zum Dashboard springen
        </a>

        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <div className="flex items-center gap-4 mb-4">
            <div className="p-3 bg-gradient-to-br from-primary-500 to-blue-500 rounded-xl shadow-lg">
              <TrendingUp className="w-8 h-8 text-white" />
            </div>
            <div>
              <h1 className="text-3xl md:text-4xl font-bold text-gray-900 dark:text-white">
                Monitoring Dashboards
              </h1>
              <p className="text-gray-600 dark:text-gray-400 mt-1">
                Live-Übersicht aller System-, Agent- und Performance-Metriken
              </p>
            </div>
          </div>

          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
            <Card className="border-none shadow-md bg-white/80 dark:bg-slate-800/80 backdrop-blur-sm">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Aktive Dashboards</p>
                    <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">{DASHBOARDS.length}</p>
                  </div>
                  <div className="p-3 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-lg">
                    <BarChart3 className="w-6 h-6 text-white" />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="border-none shadow-md bg-white/80 dark:bg-slate-800/80 backdrop-blur-sm">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Aktualisierung</p>
                    <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1 flex items-center gap-2">
                      10s
                      <span className="inline-flex h-2 w-2 rounded-full bg-green-500 animate-pulse" />
                    </p>
                  </div>
                  <div className="p-3 bg-gradient-to-br from-green-500 to-emerald-500 rounded-lg">
                    <Clock className="w-6 h-6 text-white" />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="border-none shadow-md bg-white/80 dark:bg-slate-800/80 backdrop-blur-sm">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Status</p>
                    <p className="text-2xl font-bold text-green-600 dark:text-green-400 mt-1">Operational</p>
                  </div>
                  <div className="p-3 bg-gradient-to-br from-primary-500 to-purple-500 rounded-lg">
                    <Eye className="w-6 h-6 text-white" />
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </motion.div>

        {/* Tab Navigation */}
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="mb-8"
        >
          <div
            role="tablist"
            aria-label="Dashboard-Auswahl"
            className="flex flex-wrap gap-3"
          >
            {DASHBOARDS.map((dashboard, index) => {
              const Icon = dashboard.icon;
              const isActive = activeTab === dashboard.id;

              return (
                <motion.button
                  key={dashboard.id}
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: 0.05 * index }}
                  role="tab"
                  aria-selected={isActive}
                  aria-controls={`panel-${dashboard.id}`}
                  id={`tab-${dashboard.id}`}
                  onClick={() => setActiveTab(dashboard.id)}
                  className={`
                    group relative overflow-hidden
                    px-6 py-4 rounded-xl font-medium transition-all duration-300
                    focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:ring-offset-2
                    dark:focus-visible:ring-offset-slate-900
                    ${
                      isActive
                        ? 'bg-gradient-to-r shadow-lg scale-105 text-white'
                        : 'bg-white dark:bg-slate-800 text-gray-700 dark:text-gray-300 hover:shadow-md hover:scale-102 border border-gray-200 dark:border-slate-700'
                    }
                  `}
                  style={{
                    background: isActive
                      ? undefined
                      : undefined,
                  }}
                >
                  {/* Gradient Background for active state */}
                  {isActive && (
                    <div
                      className={`absolute inset-0 bg-gradient-to-r ${dashboard.gradient} opacity-100`}
                    />
                  )}

                  <div className="relative flex items-center gap-3">
                    <Icon className={`w-5 h-5 ${
                      isActive ? 'text-white' : 'text-gray-600 dark:text-gray-400'
                    }`} />
                    <span className="font-semibold">{dashboard.title}</span>
                    <Badge
                      variant={isActive ? 'secondary' : 'outline'}
                      className={`ml-2 ${
                        isActive
                          ? 'bg-white/20 text-white border-white/30'
                          : 'border-gray-300 dark:border-slate-600'
                      }`}
                    >
                      {dashboard.badge}
                    </Badge>
                  </div>

                  {/* Hover effect */}
                  {!isActive && (
                    <div className="absolute inset-0 bg-gradient-to-r opacity-0 group-hover:opacity-5 transition-opacity" />
                  )}
                </motion.button>
              );
            })}
          </div>
        </motion.div>

        {/* Dashboard Content */}
        <AnimatePresence mode="wait">
          {activeDashboard && (
            <motion.div
              key={activeTab}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3 }}
              role="tabpanel"
              id={`panel-${activeTab}`}
              aria-labelledby={`tab-${activeTab}`}
              className="focus:outline-none"
            >
              {/* Dashboard Header Card */}
              <Card className="mb-6 border-none shadow-lg bg-white/80 dark:bg-slate-800/80 backdrop-blur-sm">
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-4">
                      <div
                        className={`p-3 bg-gradient-to-br ${activeDashboard.gradient} rounded-xl shadow-md`}
                      >
                        <activeDashboard.icon className="w-6 h-6 text-white" />
                      </div>
                      <div>
                        <CardTitle className="text-2xl text-gray-900 dark:text-white">
                          {activeDashboard.title}
                        </CardTitle>
                        <CardDescription className="text-base mt-1 text-gray-600 dark:text-gray-400">
                          {activeDashboard.description}
                        </CardDescription>
                      </div>
                    </div>
                    <a
                      href={activeDashboard.url.replace('&kiosk=tv', '')}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300 transition-colors"
                      aria-label="In Grafana öffnen"
                    >
                      <span>In Grafana öffnen</span>
                      <ArrowUpRight className="w-4 h-4" />
                    </a>
                  </div>
                </CardHeader>
              </Card>

              {/* Grafana Embed */}
              <div id="dashboard-content" className="relative">
                <div className="absolute inset-0 bg-gradient-to-br from-primary-500/5 to-blue-500/5 dark:from-primary-500/10 dark:to-blue-500/10 rounded-lg -z-10" />
                <GrafanaEmbed
                  src={activeDashboard.url}
                  title={activeDashboard.title}
                  height={1000}
                  className="rounded-lg overflow-hidden shadow-xl border border-gray-200 dark:border-slate-700"
                />
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}

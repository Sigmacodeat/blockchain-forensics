import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { useTranslation } from 'react-i18next';
import { hasFeature, canAccessRoute } from '@/lib/features';
import {
  LayoutDashboard,
  Activity,
  TrendingUp,
  BarChart3,
  Shield,
  Users,
  Eye,
  Zap,
  Radio,
  Target,
  GitBranch,
  Brain,
  Network,
  Globe,
  Settings,
  Lock,
  AlertTriangle,
  Database,
  FileText,
  ChevronRight,
  Sparkles,
  Search,
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

interface DashboardItem {
  id: string;
  title: string;
  description: string;
  route: string;
  icon: any;
  category: 'forensics' | 'analytics' | 'admin';
  plan?: string;
  badge?: string;
  roles?: string[];
}

// Alle Dashboards mit korrekten Routes (abgeglichen mit ROUTE_GATES)
const DASHBOARDS: DashboardItem[] = [
  // ========================================
  // FORENSIK-DASHBOARDS (User - Bitcoin Forensics)
  // ========================================
  {
    id: 'trace',
    title: 'Transaction Tracing',
    description: 'Bitcoin/Ethereum Transaktionen verfolgen & analysieren',
    route: '/trace',
    icon: Radio,
    category: 'forensics',
  },
  {
    id: 'cases',
    title: 'Cases Management',
    description: 'Ermittlungs-Fälle & Beweismittel verwalten',
    route: '/cases',
    icon: FileText,
    category: 'forensics',
  },
  {
    id: 'investigator',
    title: 'Graph Explorer',
    description: 'Interaktive Netzwerk-Visualisierung & Analyse',
    route: '/investigator',
    icon: Network,
    category: 'forensics',
    badge: 'Pro+',
  },
  {
    id: 'correlation',
    title: 'Correlation Analysis',
    description: 'Muster-Erkennung & Verhaltensanalyse',
    route: '/correlation',
    icon: GitBranch,
    category: 'forensics',
    badge: 'Pro+',
  },
  {
    id: 'ai-agent',
    title: 'AI Forensics Agent',
    description: 'KI-gestützte Forensik mit Natural Language',
    route: '/ai-agent',
    icon: Brain,
    category: 'forensics',
    badge: 'Plus+',
  },
  {
    id: 'bridge-transfers',
    title: 'Bridge Transfers',
    description: 'Cross-Chain Bridge-Transaktionen analysieren',
    route: '/bridge-transfers',
    icon: GitBranch,
    category: 'forensics',
  },

  // ========================================
  // ANALYTICS-DASHBOARDS (Pro/Business - Data Analysis)
  // ========================================
  {
    id: 'analytics',
    title: 'Graph Analytics',
    description: 'Netzwerk-Statistiken & Graph-Metriken',
    route: '/analytics',
    icon: BarChart3,
    category: 'analytics',
    badge: 'Pro+',
  },
  {
    id: 'performance',
    title: 'Performance Metrics',
    description: 'System-Performance & API-Latenz',
    route: '/performance',
    icon: Zap,
    category: 'analytics',
    badge: 'Business+',
  },
  {
    id: 'dashboards-grafana',
    title: 'Grafana Dashboards',
    description: 'System, Agent, Webhooks & Web Vitals',
    route: '/dashboards',
    icon: TrendingUp,
    category: 'analytics',
    badge: 'Pro+',
  },
  {
    id: 'intelligence',
    title: 'Intelligence Network',
    description: 'Bedrohungs-Daten & Community Reports',
    route: '/intelligence-network',
    icon: Shield,
    category: 'analytics',
    badge: 'Pro+',
  },

  // ========================================
  // ADMIN-DASHBOARDS (Admin only - System & Marketing)
  // ========================================
  {
    id: 'monitoring',
    title: 'System Monitoring',
    description: 'Echtzeit-Überwachung & Alerts',
    route: '/monitoring/dashboard',
    icon: Activity,
    category: 'admin',
    roles: ['admin'],
  },
  {
    id: 'web-analytics',
    title: 'User Analytics',
    description: 'User-Bewegungen, Funnels & Marketing',
    route: '/web-analytics',
    icon: Eye,
    category: 'admin',
    roles: ['admin'],
  },
  {
    id: 'onboarding',
    title: 'Onboarding Analytics',
    description: 'Onboarding-Funnel & Drop-off Analyse',
    route: '/admin/onboarding-analytics',
    icon: Users,
    category: 'admin',
    roles: ['admin'],
  },
  {
    id: 'security',
    title: 'Security & Compliance',
    description: 'Security Audits & Compliance Reports',
    route: '/security',
    icon: Lock,
    category: 'admin',
    roles: ['admin', 'auditor'],
  },
  {
    id: 'admin',
    title: 'Admin Panel',
    description: 'User-Verwaltung & System-Config',
    route: '/admin',
    icon: Settings,
    category: 'admin',
    roles: ['admin'],
  },
  {
    id: 'orgs',
    title: 'Organizations',
    description: 'Multi-Tenant Organisation Management',
    route: '/orgs',
    icon: Globe,
    category: 'admin',
    roles: ['admin'],
  },
];

export default function DashboardHub() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { t } = useTranslation();
  const [selectedCategory, setSelectedCategory] = useState<'all' | 'forensics' | 'analytics' | 'admin'>('all');

  // Filter Admin-Kategorie für normale User KOMPLETT aus
  const categories = [
    { id: 'all', label: 'Alle', icon: LayoutDashboard },
    { id: 'forensics', label: 'Forensik', icon: Search },
    { id: 'analytics', label: 'Analytics', icon: BarChart3 },
    // Admin-Kategorie NUR für Admins sichtbar
    ...(user?.role === 'admin' ? [{ id: 'admin' as const, label: 'Admin', icon: Settings }] : []),
  ] as const;

  // Filter Dashboards basierend auf Zugriff
  const accessibleDashboards = DASHBOARDS.filter((dashboard) => {
    // Kein User = keine Dashboards
    if (!user) return false;
    
    // Admin-Dashboards: Role-Check
    if (dashboard.roles) {
      return user.role && dashboard.roles.includes(user.role);
    }
    
    // User-Dashboards: Route-basierte Zugriffskontrolle (IMMER prüfen!)
    return canAccessRoute(user, dashboard.route);
  });

  // Filter nach Kategorie
  const filteredDashboards =
    selectedCategory === 'all'
      ? accessibleDashboards
      : accessibleDashboards.filter((d) => d.category === selectedCategory);

  const handleNavigate = (route: string) => {
    navigate(route);
  };

  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'forensics':
        return 'from-primary-500 to-blue-500';
      case 'analytics':
        return 'from-green-500 to-emerald-500';
      case 'admin':
        return 'from-orange-500 to-red-500';
      default:
        return 'from-gray-500 to-slate-500';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-950">
      <div className="container mx-auto max-w-7xl px-4 sm:px-6 py-8">
        {/* Skip to content */}
        <a
          href="#dashboard-grid"
          className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-primary-600 focus:text-white focus:rounded-md"
        >
          Zu Dashboards springen
        </a>

        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <div className="flex items-center gap-4 mb-4">
            <div className="p-3 bg-gradient-to-br from-primary-500 to-blue-500 rounded-xl shadow-lg">
              <LayoutDashboard className="w-8 h-8 text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
                Dashboard Hub
              </h1>
              <p className="text-gray-600 dark:text-gray-300">
                Zentrale Übersicht aller Forensik-, Analytics- und Admin-Dashboards
              </p>
            </div>
          </div>

          {/* User Info */}
          <div className="flex items-center gap-4 text-sm text-gray-600 dark:text-gray-400">
            <div className="flex items-center gap-2">
              <Users className="w-4 h-4" />
              <span>{user?.username || 'Guest'}</span>
            </div>
            <div className="flex items-center gap-2">
              <Sparkles className="w-4 h-4" />
              <span>Plan: {(user as any)?.subscription_plan || 'Community'}</span>
            </div>
            <div className="flex items-center gap-2">
              <Target className="w-4 h-4" />
              <span>{filteredDashboards.length} Dashboards verfügbar</span>
            </div>
          </div>
        </motion.div>

        {/* Category Filter */}
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="mb-8"
        >
          <div className="flex flex-wrap gap-3">
            {categories.map((category) => {
              const Icon = category.icon;
              const isActive = selectedCategory === category.id;
              const count = category.id === 'all'
                ? accessibleDashboards.length
                : accessibleDashboards.filter((d) => d.category === category.id).length;

              return (
                <button
                  key={category.id}
                  onClick={() => setSelectedCategory(category.id)}
                  className={`
                    flex items-center gap-2 px-4 py-3 rounded-xl font-medium transition-all
                    ${
                      isActive
                        ? 'bg-gradient-to-r from-primary-500 to-blue-500 text-white shadow-lg scale-105'
                        : 'bg-white dark:bg-slate-800 text-gray-700 dark:text-gray-300 hover:shadow-md hover:scale-102'
                    }
                  `}
                  aria-pressed={isActive}
                >
                  <Icon className="w-5 h-5" />
                  <span>{category.label}</span>
                  <Badge
                    variant={isActive ? 'secondary' : 'outline'}
                    className={isActive ? 'bg-white/20 text-white border-white/30' : ''}
                  >
                    {count}
                  </Badge>
                </button>
              );
            })}
          </div>
        </motion.div>

        {/* Dashboard Grid */}
        <motion.div
          id="dashboard-grid"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
        >
          {filteredDashboards.map((dashboard, index) => {
            const Icon = dashboard.icon;
            return (
              <motion.div
                key={dashboard.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.05 * index }}
              >
                <Card
                  className="h-full hover:shadow-xl transition-all duration-300 cursor-pointer group hover:scale-105 relative overflow-hidden"
                  onClick={() => handleNavigate(dashboard.route)}
                  role="button"
                  tabIndex={0}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault();
                      handleNavigate(dashboard.route);
                    }
                  }}
                  aria-label={`${dashboard.title} öffnen`}
                >
                  {/* Gradient Background */}
                  <div
                    className={`absolute inset-0 bg-gradient-to-br ${getCategoryColor(
                      dashboard.category
                    )} opacity-5 group-hover:opacity-10 transition-opacity`}
                  />

                  <CardHeader className="relative">
                    <div className="flex items-start justify-between mb-3">
                      <div className="p-3 bg-gradient-to-br from-white to-gray-50 dark:from-slate-800 dark:to-slate-900 rounded-xl shadow-sm group-hover:shadow-md transition-shadow">
                        <Icon className="w-6 h-6 text-primary-600 dark:text-primary-400" />
                      </div>
                      {dashboard.badge && (
                        <Badge variant="secondary" className="font-semibold">
                          {dashboard.badge}
                        </Badge>
                      )}
                    </div>
                    <CardTitle className="text-xl group-hover:text-primary-600 dark:group-hover:text-primary-400 transition-colors">
                      {dashboard.title}
                    </CardTitle>
                    <CardDescription className="text-sm line-clamp-2">
                      {dashboard.description}
                    </CardDescription>
                  </CardHeader>

                  <CardContent className="relative">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400">
                        {dashboard.category === 'forensics' && (
                          <Badge variant="outline" className="text-xs">
                            Forensik
                          </Badge>
                        )}
                        {dashboard.category === 'analytics' && (
                          <Badge variant="outline" className="text-xs">
                            Analytics
                          </Badge>
                        )}
                        {dashboard.category === 'admin' && (
                          <Badge variant="outline" className="text-xs border-orange-300 text-orange-600">
                            Admin
                          </Badge>
                        )}
                      </div>
                      <ChevronRight className="w-5 h-5 text-gray-400 group-hover:text-primary-600 group-hover:translate-x-1 transition-all" />
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            );
          })}
        </motion.div>

        {/* Empty State */}
        {filteredDashboards.length === 0 && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="text-center py-16"
          >
            <AlertTriangle className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-gray-700 dark:text-gray-300 mb-2">
              Keine Dashboards verfügbar
            </h3>
            <p className="text-gray-600 dark:text-gray-400 max-w-md mx-auto mb-4">
              Für diese Kategorie sind keine Dashboards verfügbar oder Sie haben keinen Zugriff.
            </p>
            {user?.role !== 'admin' && (
              <a
                href="/pricing"
                className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-primary-500 to-blue-500 text-white rounded-lg hover:shadow-lg transition-all"
              >
                <Sparkles className="w-5 h-5" />
                Plan upgraden für mehr Features
              </a>
            )}
          </motion.div>
        )}

        {/* Quick Stats */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-6"
        >
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-gray-600 dark:text-gray-400">
                Forensik-Tools
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-primary-600">
                {accessibleDashboards.filter((d) => d.category === 'forensics').length}
              </div>
              <p className="text-xs text-gray-500 mt-1">Bitcoin & Ethereum Analyse</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-gray-600 dark:text-gray-400">
                Analytics
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-green-600">
                {accessibleDashboards.filter((d) => d.category === 'analytics').length}
              </div>
              <p className="text-xs text-gray-500 mt-1">Daten & Performance</p>
            </CardContent>
          </Card>

          {/* Admin-Stats nur für Admins anzeigen */}
          {user?.role === 'admin' && (
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  Admin-Tools
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold text-orange-600">
                  {accessibleDashboards.filter((d) => d.category === 'admin').length}
                </div>
                <p className="text-xs text-gray-500 mt-1">System & User-Management</p>
              </CardContent>
            </Card>
          )}
        </motion.div>
      </div>
    </div>
  );
}

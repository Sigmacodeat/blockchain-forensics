import { ReactNode, useState, useEffect, useRef, useMemo } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { 
  Activity, 
  Search, 
  Bot, 
  BarChart3, 
  Settings, 
  User, 
  LogOut, 
  ChevronDown, 
  Route, 
  Brain, 
  Gauge, 
  X, 
  Menu, 
  FileText, 
  LayoutDashboard, 
  FolderOpen, 
  GitBranch, 
  Radar, 
  Network, 
  TrendingUp, 
  Globe, 
  Building2, 
  Shield, 
  Bell, 
  Sparkles, 
  Wrench, 
  Key, 
  Users, 
  CreditCard, 
  Gift, 
  ShieldCheck 
} from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'
import { useI18n } from '@/contexts/I18nContext'
import { canAccessRoute, type PlanId } from '@/lib/features'
import CreditBadge from '@/components/CreditBadge'
import ProductSwitcher from '@/components/ProductSwitcher'
import { ThemeToggle } from '@/contexts/ThemeContext'
import { pageview, identify, track } from '@/lib/analytics'
import { openCookieConsent } from '@/components/legal/CookieConsent'
import ChatWidget from '@/components/chat/ChatWidget'
import { PageTransition } from '@/components/PageTransition'

interface LayoutProps {
  children: ReactNode
}

export default function Layout({ children }: LayoutProps) {
  const location = useLocation()
  const navigate = useNavigate()
  const { user, logout } = useAuth()
  const { t } = useTranslation()
  const { currentLanguage } = useI18n()
  const isRTL = useMemo(() => ['ar', 'he'].includes(currentLanguage), [currentLanguage])
  const [showUserMenu, setShowUserMenu] = useState(false)
  const userMenuRef = useRef<HTMLDivElement | null>(null)
  const userMenuButtonRef = useRef<HTMLButtonElement | null>(null)
  const logoutBtnRef = useRef<HTMLButtonElement | null>(null)
  const navRef = useRef<HTMLDivElement | null>(null)
  const [isPaletteOpen, setPaletteOpen] = useState(false)
  const [paletteQuery, setPaletteQuery] = useState('')
  const [paletteIndex, setPaletteIndex] = useState(0)
  const paletteInputRef = useRef<HTMLInputElement | null>(null)
  const paletteRef = useRef<HTMLDivElement | null>(null)
  const paletteButtonRef = useRef<HTMLButtonElement | null>(null)
  const [recentPalette, setRecentPalette] = useState<Array<{ path: string; label: string }>>(() => {
    try {
      const raw = localStorage.getItem('palette_recent')
      return raw ? JSON.parse(raw) : []
    } catch { return [] }
  })
  const liveRegionRef = useRef<HTMLDivElement | null>(null)
  const [announcement, setAnnouncement] = useState('')
  const [hasScrolled, setHasScrolled] = useState(false)
  const [debouncedQuery, setDebouncedQuery] = useState('')
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const userMenuId = 'dashboard-user-menu'
  const userMenuButtonId = 'dashboard-user-button'
  const hoverTimerUser = useRef<number | null>(null)
  const prefersReducedMotion = useMemo(() =>
    typeof window !== 'undefined' && window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches
  , [])

  // Helper: build i18n nav key from path
  const navKeyFromPath = (p: string) => {
    if (!p || p === '/') return '__'
    return `_${p.replace(/^\//, '').replace(/\//g, '_')}_`
  }

  // Debounce: verhindert Burst-Imports bei schnellem Hover
  const prefetchTimerRef = useRef<number | null>(null)
  const prefetchRouteDebounced = (path: string) => {
    if (prefetchTimerRef.current) window.clearTimeout(prefetchTimerRef.current)
    prefetchTimerRef.current = window.setTimeout(() => prefetchRoute(path), 60)
  }

  // Helper: navigate from command palette with tracking
  const navigateFromPalette = (item: { path: string; label: string }, method: 'enter' | 'click' | 'recent') => {
    track('command_palette_navigate', { path: item.path, label: item.label, method })
    setPaletteOpen(false)
    addRecent({ path: item.path, label: item.label })
    const hasLang = /^\/[a-z]{2}(?:-[A-Z]{2})?\//.test(item.path)
    navigate(hasLang ? item.path : withLang(item.path))
  }

  // Helper: close palette with tracking
  const togglePalette = () => {
    track('command_palette_toggle', { open: false })
    setPaletteOpen(false)
  }

  // Sprache aus Pfad extrahieren (z.B. /de/...)
  const currentLang = (() => {
    const m = location.pathname.match(/^\/([a-z]{2}(?:-[A-Z]{2})?)/)
    return m ? m[1] : 'en'
  })()

  const withLang = (path: string) => `/${currentLang}${path === '/' ? '' : path}`

  const isActive = (path: string) => {
    const hasLang = /^\/[a-z]{2}(?:-[A-Z]{2})?\//.test(path)
    const full = hasLang ? path : withLang(path)
    if (path === '/') return location.pathname === full
    return location.pathname === full || location.pathname.startsWith(full + '/')
  }

  // Prüfen ob wir auf einer Dashboard/Forensik-Seite sind (KEIN Marketing-ChatWidget)
  const isDashboardArea = useMemo(() => {
    const cleanPath = location.pathname.replace(/^\/[a-z]{2}(-[A-Z]{2})?/, '') || '/'
    const dashboardRoutes = [
      '/dashboard', '/forensics', '/trace', '/investigator', '/correlation',
      '/cases', '/bridge-transfers', '/performance', '/analytics', '/web-analytics',
      '/orgs', '/policies', '/monitoring', '/ai-agent', '/admin', '/settings',
      '/wallet-scanner', '/bitcoin-investigation', '/vasp-compliance', '/advanced-indirect-risk'
    ]
    return dashboardRoutes.some(route => cleanPath === route || cleanPath.startsWith(route + '/'))
  }, [location.pathname])

  useEffect(() => {
    pageview(user?.username)
    setShowUserMenu(false)
    setPaletteOpen(false)
    const label = (Object.fromEntries(navItems.map((n) => [n.path, n.label])) as Record<string, string>)[location.pathname]
    setAnnouncement(label || location.pathname)
  }, [location.pathname])

  useEffect(() => {
    if (user?.username) identify(user.username)
  }, [user?.username])

  // Announce route changes for screen readers
  useEffect(() => {
    const label = document.title || location.pathname
    if (liveRegionRef.current) {
      liveRegionRef.current.textContent = `Seite geladen: ${label}`
    }
  }, [location.pathname])

  // Scroll-Schatten
  useEffect(() => {
    function onScroll() {
      setHasScrolled(window.scrollY > 0)
    }
    onScroll()
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  // Schließe die mobile Sidebar bei Routenwechsel (Robustheit)
  useEffect(() => {
    if (sidebarOpen) setSidebarOpen(false)
  }, [location.pathname])

  // Cleanup hover timers on unmount
  useEffect(() => () => {
    if (hoverTimerUser.current) window.clearTimeout(hoverTimerUser.current)
    if (prefetchTimerRef.current) window.clearTimeout(prefetchTimerRef.current)
  }, [])

  // Scroll-lock when user menu is open
  useEffect(() => {
    if (showUserMenu) {
      const root = document.documentElement
      const prev = root.style.overflow
      root.style.overflow = 'hidden'
      return () => { root.style.overflow = prev }
    }
  }, [showUserMenu])

  // Debounce der Palette-Suche
  useEffect(() => {
    const id = setTimeout(() => setDebouncedQuery(paletteQuery), 200)
    return () => clearTimeout(id)
  }, [paletteQuery])

  useEffect(() => {
    function onDocClick(e: MouseEvent) {
      const target = e.target as Node
      if (userMenuRef.current && !userMenuRef.current.contains(target)) {
        setShowUserMenu(false)
      }
      if (isPaletteOpen && paletteRef.current && !paletteRef.current.contains(target)) {
        setPaletteOpen(false)
      }
    }
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape') { setShowUserMenu(false); if (isPaletteOpen) { setPaletteOpen(false); requestAnimationFrame(() => paletteButtonRef.current?.focus()) } }
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault()
        setPaletteOpen((v) => {
          const next = !v
          track('command_palette_toggle', { open: next })
          return next
        })
      }
    }
    document.addEventListener('mousedown', onDocClick)
    document.addEventListener('keydown', onKey)
    return () => {
      document.removeEventListener('mousedown', onDocClick)
      document.removeEventListener('keydown', onKey)
    }
  }, [])

  useEffect(() => {
    if (showUserMenu) {
      // Fokus erstes Element im Menü
      requestAnimationFrame(() => logoutBtnRef.current?.focus())
    } else {
      // Fokus zurück auf den Toggle-Button
      requestAnimationFrame(() => userMenuButtonRef.current?.focus())
    }
  }, [showUserMenu])

  useEffect(() => {
    if (isPaletteOpen) {
      requestAnimationFrame(() => paletteInputRef.current?.focus())
      // Scroll-Lock aktivieren
      const root = document.documentElement
      const prev = root.style.overflow
      root.style.overflow = 'hidden'
      track('command_palette_open', {})
      return () => { root.style.overflow = prev }
    } else {
      setPaletteQuery('')
      setPaletteIndex(0)
      // falls über Button geöffnet: Fokus zurückgeben
      requestAnimationFrame(() => paletteButtonRef.current?.focus())
    }
  }, [isPaletteOpen])

  const navItems = useMemo(() => [
    // HAUPT-DASHBOARD (Zentrale Übersicht)
    { path: `/${currentLanguage}/dashboard`, label: 'Dashboard Hub', icon: LayoutDashboard, minPlan: 'community' as PlanId },
    { path: `/${currentLanguage}/forensics`, label: 'Forensics Hub', icon: LayoutDashboard, minPlan: 'community' as PlanId },
    
    // KUNDEN-NAVIGATION (Forensik)
    { path: `/${currentLanguage}/trace`, label: 'Transaction Tracing', icon: Radar, minPlan: 'community' as PlanId },  // ✅ Ab Community!
    { path: `/${currentLanguage}/cases`, label: 'Cases', icon: FolderOpen, minPlan: 'community' as PlanId },
    { path: `/${currentLanguage}/news-cases`, label: 'News Cases', icon: FolderOpen, minPlan: 'pro' as PlanId },
    { path: `/${currentLanguage}/bridge-transfers`, label: 'Bridge Transfers', icon: GitBranch, minPlan: 'community' as PlanId },
    { path: `/${currentLanguage}/trace/tools`, label: 'Trace Tools', icon: Wrench, minPlan: 'starter' as PlanId },
    { path: `/${currentLanguage}/investigator`, label: 'Graph Explorer', icon: Network, minPlan: 'pro' as PlanId },
    { path: `/${currentLanguage}/correlation`, label: 'Korrelations-Analyse', icon: Brain, minPlan: 'pro' as PlanId },
    { path: `/${currentLanguage}/patterns`, label: 'Pattern Detection', icon: Route, minPlan: 'pro' as PlanId },
    { path: `/${currentLanguage}/privacy-demixing`, label: 'Privacy Demixing', icon: Route, minPlan: 'pro' as PlanId },
    { path: `/${currentLanguage}/dashboards`, label: 'Dashboards', icon: TrendingUp, minPlan: 'pro' as PlanId },
    { path: `/${currentLanguage}/performance`, label: 'Performance', icon: Gauge, minPlan: 'business' as PlanId },
    { path: `/${currentLanguage}/policies`, label: 'Policies', icon: Shield, minPlan: 'business' as PlanId },
    { path: `/${currentLanguage}/automation`, label: 'Automation', icon: Bot, minPlan: 'business' as PlanId },
    { path: `/${currentLanguage}/billing`, label: 'Billing', icon: CreditCard, minPlan: 'community' as PlanId },
    { path: `/${currentLanguage}/webhooks`, label: 'Webhooks', icon: Wrench, minPlan: 'starter' as PlanId },
    { path: `/${currentLanguage}/api-keys`, label: 'API Keys', icon: Key, minPlan: 'pro' as PlanId },
    { path: `/${currentLanguage}/intelligence-network`, label: 'Intelligence Network', icon: Users, minPlan: 'pro' as PlanId },  // ✅ TRM Beacon-Style
    { path: `/${currentLanguage}/wallet-scanner`, label: 'Wallet Scanner', icon: Key, minPlan: 'pro' as PlanId },  // ✅ Chainalysis Wallet Scan
    { path: `/${currentLanguage}/bitcoin-investigation`, label: 'Bitcoin Investigation', icon: Search, minPlan: 'plus' as PlanId },  // ✅ Deep Criminal Case Analysis
    { path: `/${currentLanguage}/universal-screening`, label: 'Universal Screening', icon: Search, minPlan: 'pro' as PlanId },  // ✅ TRM-Style Multi-Chain Screening
    { path: `/${currentLanguage}/ai-agent`, label: 'AI Agent', icon: Sparkles, minPlan: 'plus' as PlanId },
    
    // ADMIN-NAVIGATION (System-Management)
    { path: `/${currentLanguage}/analytics`, label: 'Analytics', icon: BarChart3, roles: ['admin'] as Array<string> },  // ✅ Nur Admin!
    { path: `/${currentLanguage}/web-analytics`, label: 'Web Analytics', icon: Globe, roles: ['admin'] as Array<string> },  // ✅ Nur Admin!
    { path: `/${currentLanguage}/admin/appsumo`, label: 'AppSumo Metrics', icon: Gift, roles: ['admin'] as Array<string> },  // ✅ AppSumo Dashboard!
    { path: `/${currentLanguage}/admin/appsumo/manager`, label: 'AppSumo Manager', icon: Settings, roles: ['admin'] as Array<string> },  // ✅ AppSumo Code Management!
    { path: `/${currentLanguage}/admin/institutional-verifications`, label: 'Institutional Verifications', icon: ShieldCheck, roles: ['admin', 'auditor'] as Array<string> },
    { path: `/${currentLanguage}/monitoring`, label: 'Monitoring', icon: Bell, roles: ['admin'] as Array<string> },
    { path: `/${currentLanguage}/monitoring/dashboard`, label: 'Monitoring Dashboard', icon: Activity, roles: ['admin'] as Array<string> },
    { path: `/${currentLanguage}/orgs`, label: 'Orgs', icon: Building2, roles: ['admin'] as Array<string> },
    { path: `/${currentLanguage}/admin`, label: 'Admin', icon: Settings, roles: ['admin'] as Array<string> },
  ] as Array<{ path: string; label: string; icon: any; roles?: string[]; minPlan?: PlanId }>, [currentLanguage])

  const visibleNavItems = navItems.filter((item) => {
    // Role-based filter
    if (item.roles && !item.roles.includes((user?.role as string) || 'guest')) {
      return false
    }
    // Plan-based filter (use canAccessRoute for comprehensive check)
    if (item.minPlan && !canAccessRoute(user, item.path)) {
      return false
    }
    return true
  })

  const labelMap = Object.fromEntries(navItems.map((n) => [n.path, n.label])) as Record<string, string>
  const buildBreadcrumbs = () => {
    const segments = location.pathname.split('/').filter(Boolean)
    const crumbs: Array<{ path: string; label: string }> = []
    let acc = ''
    if (segments.length === 0) return crumbs
    segments.forEach((seg) => {
      acc += `/${seg}`
      const known = labelMap[acc]
      const label = known || seg.replace(/[-_]/g, ' ').replace(/\b\w/g, (m) => m.toUpperCase())
      crumbs.push({ path: acc, label })
    })
    return crumbs
  }
  const breadcrumbs = buildBreadcrumbs()

  const onNavKeyDown = (e: React.KeyboardEvent<HTMLDivElement>) => {
    if (!navRef.current) return
    const focusable = Array.from(navRef.current.querySelectorAll<HTMLAnchorElement>('a[href]'))
    const currentIndex = focusable.indexOf(document.activeElement as HTMLAnchorElement)
    if (e.key === 'ArrowRight') {
      e.preventDefault()
      const next = focusable[(currentIndex + 1 + focusable.length) % focusable.length]
      next?.focus()
    } else if (e.key === 'ArrowLeft') {
      e.preventDefault()
      const prev = focusable[(currentIndex - 1 + focusable.length) % focusable.length]
      prev?.focus()
    }
  }

  const filteredItems = useMemo(() => (
    navItems.filter((n) => (n.label + ' ' + n.path).toLowerCase().includes(debouncedQuery.toLowerCase()))
  ), [navItems, debouncedQuery])

  // Prefetch route chunks on hover to improve perceived performance
  const prefetchRoute = (path: string) => {
    // Map a subset of common routes to their lazy chunks
    // These dynamic imports trigger Vite to prefetch the corresponding chunks
    try {
      const p = path.replace(/^\/[a-z]{2}(?:-[A-Z]{2})?/, '') || '/'
      switch (true) {
        case p === '/' || p === '/dashboard':
          import('@/pages/MainDashboard'); break
        case p.startsWith('/dashboard'):
          import('@/pages/DashboardHub'); break
        case /\/cases\/.+/.test(p):
          import('@/pages/CaseDetailPage'); break
        case p === '/cases' || p.startsWith('/cases'):
          import('@/pages/CasesPage'); break
        case p.startsWith('/dashboards'):
          import('@/pages/DashboardsOverviewPage'); break
        case p.startsWith('/trace/tools'):
          import('@/pages/Trace'); break
        case p.startsWith('/trace'):
          import('@/pages/TracePage'); break
        case p.startsWith('/analytics'):
          import('@/pages/GraphAnalyticsPage'); break
        case p.startsWith('/bridge-transfers'):
          import('@/pages/BridgeTransfersPage'); break
        case p.startsWith('/web-analytics'):
          import('@/pages/WebAnalyticsPage'); break
        case p.startsWith('/admin'):
          import('@/pages/AdminPage'); break
        case p.startsWith('/pricing'):
          import('@/pages/PricingPage'); break
        case p.startsWith('/billing'):
          import('@/pages/BillingPage'); break
        case p.startsWith('/investigator'):
          import('@/pages/InvestigatorGraphPage'); break
        case p.startsWith('/correlation'):
          import('@/pages/CorrelationAnalysisPage'); break
        case p.startsWith('/ai-agent'):
          import('@/pages/AIAgentPage'); break
        case p.startsWith('/intelligence-network'):
          import('@/pages/IntelligenceNetwork'); break
        case p.startsWith('/wallet-scanner'):
          import('@/pages/WalletScanner'); break
        case p.startsWith('/bitcoin-investigation'):
          import('@/pages/BitcoinInvestigation'); break
        case p.startsWith('/webhooks'):
          import('@/pages/WebhooksPage'); break
        case p.startsWith('/api-keys'):
          import('@/pages/APIKeysPage'); break
        case p.startsWith('/performance'):
          import('@/pages/PerformanceDashboard'); break
        case p.startsWith('/policies'):
          import('@/features/alerts/PolicyManager'); break
        case p.startsWith('/monitoring/dashboard'):
          import('@/pages/MonitoringDashboardPage'); break
        case p.startsWith('/monitoring'):
          import('@/pages/MonitoringAlertsPage'); break
        case p.startsWith('/news-cases'):
          import('@/pages/NewsCasesManager'); break
        case p.startsWith('/news/'):
          import('@/pages/NewsCasePublicPage'); break
        case p.startsWith('/universal-screening'):
          import('@/pages/UniversalScreening'); break
        case p.startsWith('/vasp-compliance'):
          import('@/pages/VASPCompliance'); break
        case p.startsWith('/security'):
          import('@/pages/SecurityComplianceDashboard'); break
        case p.startsWith('/coverage'):
          import('@/pages/ChainCoverage'); break
        case p.startsWith('/address'):
          import('@/pages/AddressAnalysisPage'); break
        case p.startsWith('/orgs'):
          import('@/pages/OrgsPage'); break
        default:
          break
      }
    } catch (_) { /* noop */ }
  }

  // Definiere welche Routen die Sidebar bekommen sollen (alle Dashboard/Admin Seiten)
  const showSidebar = useMemo(() => {
    const path = location.pathname
    // Extrahiere Sprach-Präfix (z.B. /de/dashboard -> /dashboard)
    const pathWithoutLang = path.replace(/^\/[a-z]{2}(-[A-Z]{2})?/, '') || '/'
    const sidebarRoutes = [
      '/dashboard', '/dashboard-main',
      '/forensics',
      '/cases',
      '/dashboards',
      '/bridge-transfers',
      '/trace', '/trace/tools',
      '/address',
      '/coverage',
      '/investigator',
      '/correlation',
      '/performance',
      '/analytics', '/web-analytics',
      '/patterns',
      '/automation',
      '/billing',
      '/webhooks',
      '/api-keys',
      '/orgs',
      '/policies',
      '/monitoring', '/monitoring/dashboard',
      '/intelligence-network',
      '/wallet-scanner',
      '/bitcoin-investigation',
      '/universal-screening',
      '/vasp-compliance',
      '/security',
      '/privacy-demixing',
      '/wallet',
      '/ai-agent',
      '/admin',
    ]
    return sidebarRoutes.some((route) => pathWithoutLang === route || pathWithoutLang.startsWith(route + '/'))
  }, [location.pathname])

  const addRecent = (item: { path: string; label: string }) => {
    setRecentPalette((prev) => {
      const next = [item, ...prev.filter((i) => i.path !== item.path)].slice(0, 5)
      try { localStorage.setItem('palette_recent', JSON.stringify(next)) } catch {}
      return next
    })
  }

  return (
    <div className="min-h-screen flex flex-col bg-background text-foreground" dir={isRTL ? 'rtl' : 'ltr'}>
      <div aria-live="polite" className="sr-only">{announcement}</div>
      <a href="#main-content" className="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 focus:z-[60] focus:bg-primary focus:text-primary-foreground px-3 py-2 rounded">{t('layout.skip_to_content', 'Zum Inhalt springen')}</a>
      {/* Header */}
      <header className={`bg-background/80 backdrop-blur border-b border-border sticky top-0 z-50 ${hasScrolled ? 'shadow-sm' : ''}`}>
        <div className="container mx-auto max-w-6xl px-4 sm:px-6">
          <div className="flex justify-between items-center h-14">
            <div className="flex items-center gap-3">
              {showSidebar && (
                <button
                  type="button"
                  onClick={() => setSidebarOpen((v) => !v)}
                  className="inline-flex lg:hidden items-center justify-center p-2 rounded-lg hover:bg-gray-50 dark:hover:bg-slate-800 focus-visible:ring-2 focus-visible:ring-primary/50"
                  aria-label={sidebarOpen ? 'Menü schließen' : 'Menü öffnen'}
                  aria-haspopup="dialog"
                  aria-expanded={sidebarOpen}
                >
                  <AnimatePresence initial={false} mode="wait">
                    {sidebarOpen ? (
                      <motion.span
                        key="icon-close"
                        initial={{ rotate: prefersReducedMotion ? 0 : -90, opacity: prefersReducedMotion ? 1 : 0 }}
                        animate={{ rotate: 0, opacity: 1 }}
                        exit={{ rotate: prefersReducedMotion ? 0 : 90, opacity: prefersReducedMotion ? 1 : 0 }}
                        transition={{ duration: prefersReducedMotion ? 0 : 0.18, ease: 'easeOut' }}
                      >
                        <X className="w-6 h-6" aria-hidden />
                      </motion.span>
                    ) : (
                      <motion.span
                        key="icon-menu"
                        initial={{ rotate: prefersReducedMotion ? 0 : -90, opacity: prefersReducedMotion ? 1 : 0 }}
                        animate={{ rotate: 0, opacity: 1 }}
                        exit={{ rotate: prefersReducedMotion ? 0 : 90, opacity: prefersReducedMotion ? 1 : 0 }}
                        transition={{ duration: prefersReducedMotion ? 0 : 0.18, ease: 'easeOut' }}
                      >
                        <Menu className="w-6 h-6" aria-hidden />
                      </motion.span>
                    )}
                  </AnimatePresence>
                </button>
              )}
              <Search className="w-8 h-8 text-primary-600" />
              <div className="leading-tight">
                <h1 className="text-xl font-bold">SIGMACODE</h1>
                <p className="text-xs text-muted-foreground mt-0.5">Blockchain Forensics</p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <CreditBadge />
              
              {/* Product Switcher - Zeigt AppSumo-Produkte */}
              {user && <ProductSwitcher />}
              
              <button
                type="button"
                className="hidden sm:inline-flex items-center gap-2 px-3 py-2 rounded-lg bg-white dark:bg-slate-800 hover:bg-gray-100 dark:hover:bg-slate-700 border border-gray-200 dark:border-slate-700 shadow-sm transition-all outline-none focus-visible:ring-2 focus-visible:ring-primary/50"
                onClick={() => { track('command_palette_open', { source: 'button' }); setPaletteOpen(true) }}
                aria-haspopup="dialog"
                aria-expanded={isPaletteOpen}
                ref={paletteButtonRef}
              >
                <Search className="w-5 h-5 text-gray-600 dark:text-gray-300" aria-hidden />
                <span className="text-sm font-medium text-gray-700 dark:text-gray-200">{t('common.search', 'Suchen')}</span>
                <kbd className="ml-1 hidden md:inline-flex select-none items-center gap-1 rounded border border-gray-300 dark:border-slate-600 bg-gray-50 dark:bg-slate-900 px-1.5 text-[10px] font-medium text-gray-500 dark:text-gray-400">⌘K</kbd>
              </button>
              
              {/* Theme Toggle - Links neben User-Menü */}
              <ThemeToggle />
              
              {/* User Menu Dropdown */}
              <div className="relative" ref={userMenuRef}>
                <button
                  ref={userMenuButtonRef}
                  type="button"
                  id={userMenuButtonId}
                  onClick={() => { setShowUserMenu(!showUserMenu); if (!showUserMenu) track('auth_dropdown_open', { source: 'dashboard_header', method: 'click' }) }}
                  className="flex items-center gap-2 px-3 py-2 rounded-lg bg-white dark:bg-slate-800 hover:bg-gray-100 dark:hover:bg-slate-700 border border-gray-200 dark:border-slate-700 shadow-sm transition-all outline-none focus-visible:ring-2 focus-visible:ring-primary/50"
                  aria-haspopup="true"
                  aria-expanded={showUserMenu}
                  aria-controls={showUserMenu ? userMenuId : undefined}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ' || e.key === 'ArrowDown') {
                      e.preventDefault()
                      if (!showUserMenu) { setShowUserMenu(true); track('auth_dropdown_open', { source: 'dashboard_header', method: 'keydown', key: e.key }) }
                    }
                  }}
                  onMouseEnter={() => {
                    if (hoverTimerUser.current) window.clearTimeout(hoverTimerUser.current)
                    hoverTimerUser.current = window.setTimeout(() => { setShowUserMenu(true); try { import('@/pages/RegisterPage'); import('@/pages/LoginPage') } catch {} }, 100)
                  }}
                  onMouseLeave={(e) => {
                    if (hoverTimerUser.current) window.clearTimeout(hoverTimerUser.current)
                    const to = e.relatedTarget as Node | null
                    if (to && userMenuRef.current && userMenuRef.current.contains(to)) return
                    hoverTimerUser.current = window.setTimeout(() => setShowUserMenu(false), 150)
                  }}
                >
                  {user ? (
                    <>
                      <User className="w-5 h-5 text-gray-600 dark:text-gray-300" />
                      <span className="hidden md:inline text-sm font-medium text-gray-700 dark:text-gray-200">{user.username}</span>
                      <ChevronDown className={`w-4 h-4 text-gray-500 dark:text-gray-400 transition-transform ${showUserMenu ? 'rotate-180' : ''}`} />
                    </>
                  ) : (
                    <>
                      <User className="w-5 h-5 text-gray-600 dark:text-gray-300" />
                      <span className="hidden md:inline text-sm font-medium text-gray-700 dark:text-gray-200">Account</span>
                      <ChevronDown className={`w-4 h-4 text-gray-500 dark:text-gray-400 transition-transform ${showUserMenu ? 'rotate-180' : ''}`} />
                    </>
                  )}
                </button>

                {/* Dropdown Menu */}
                <AnimatePresence>
                {showUserMenu && (
                  <motion.div
                    role="menu"
                    id={userMenuId}
                    aria-labelledby={userMenuButtonId}
                    initial={{ opacity: 0, y: -4, scale: 0.98 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, y: -4, scale: 0.98 }}
                    transition={{ duration: prefersReducedMotion ? 0 : 0.12, ease: 'easeOut' }}
                    className="absolute right-0 mt-2 w-56 rounded-lg bg-white dark:bg-slate-800 shadow-lg border border-gray-200 dark:border-slate-700 py-1 z-50"
                    onMouseEnter={() => { if (hoverTimerUser.current) window.clearTimeout(hoverTimerUser.current) }}
                    onMouseLeave={() => {
                      if (hoverTimerUser.current) window.clearTimeout(hoverTimerUser.current)
                      hoverTimerUser.current = window.setTimeout(() => setShowUserMenu(false), 150)
                    }}
                    onKeyDown={(e) => {
                      const items = Array.from((e.currentTarget as HTMLElement).querySelectorAll('[role="menuitem"]')) as HTMLElement[]
                      const currentIndex = items.findIndex((el) => el === document.activeElement)
                      if (e.key === 'ArrowDown') {
                        e.preventDefault(); items[(currentIndex + 1) % items.length]?.focus()
                      } else if (e.key === 'ArrowUp') {
                        e.preventDefault(); items[(currentIndex - 1 + items.length) % items.length]?.focus()
                      } else if (e.key === 'Home') {
                        e.preventDefault(); items[0]?.focus()
                      } else if (e.key === 'End') {
                        e.preventDefault(); items[items.length - 1]?.focus()
                      } else if (e.key === 'Tab') {
                        e.preventDefault(); if (items.length) { const dir = e.shiftKey ? -1 : 1; items[(currentIndex + dir + items.length) % items.length]?.focus() }
                      }
                    }}
                  >
                    {user ? (
                      <>
                        {/* Eingeloggt: User Info + Settings + Logout */}
                        <div className="px-4 py-3 border-b border-gray-200 dark:border-slate-700">
                          <p className="text-sm font-medium text-gray-900 dark:text-white">{user.username}</p>
                          <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{user.email}</p>
                        </div>
                        <Link
                          to={withLang('/settings')}
                          onClick={() => setShowUserMenu(false)}
                          className="flex items-center gap-3 px-4 py-2 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-slate-700 transition-colors focus:outline-none focus:ring-2 focus:ring-primary/40"
                          role="menuitem"
                          tabIndex={0}
                        >
                          <Settings className="w-4 h-4" />
                          Settings
                        </Link>
                        <button
                          ref={logoutBtnRef}
                          onClick={() => {
                            setShowUserMenu(false)
                            logout()
                            navigate(withLang('/'))
                          }}
                          className="w-full flex items-center gap-3 px-4 py-2 text-sm text-red-600 dark:text-red-400 hover:bg-gray-100 dark:hover:bg-slate-700 transition-colors focus:outline-none focus:ring-2 focus:ring-primary/40"
                          role="menuitem"
                          tabIndex={0}
                        >
                          <LogOut className="w-4 h-4" />
                          Logout
                        </button>
                      </>
                    ) : (
                      <>
                        {/* Nicht eingeloggt: Login + Register */}
                        <Link
                          to={withLang('/login')}
                          onClick={() => { setShowUserMenu(false); track('auth_click_login', { source: 'dashboard_header' }) }}
                          className="flex items-center gap-3 px-4 py-2 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-slate-700 transition-colors focus:outline-none focus:ring-2 focus:ring-primary/40"
                          role="menuitem"
                          tabIndex={0}
                          onMouseEnter={() => { try { import('@/pages/LoginPage') } catch {} }}
                        >
                          <User className="w-4 h-4" />
                          Login
                        </Link>
                        <Link
                          to={withLang('/register')}
                          onClick={() => { setShowUserMenu(false); track('auth_click_register', { source: 'dashboard_header' }) }}
                          className="flex items-center gap-3 px-4 py-2 text-sm text-primary-600 dark:text-primary-400 font-medium hover:bg-gray-100 dark:hover:bg-slate-700 transition-colors focus:outline-none focus:ring-2 focus:ring-primary/40"
                          role="menuitem"
                          tabIndex={0}
                          onMouseEnter={() => { try { import('@/pages/RegisterPage') } catch {} }}
                        >
                          <User className="w-4 h-4" />
                          Register
                        </Link>
                      </>
                    )}
                  </motion.div>
                )}
                </AnimatePresence>
              </div>
              {!showSidebar && (
                <nav
                  className="flex gap-1 overflow-x-auto whitespace-nowrap scrollbar-thin"
                  role="navigation"
                  aria-label={t('layout.main_navigation', 'Hauptnavigation')}
                  aria-orientation="horizontal"
                  ref={navRef}
                  onKeyDown={onNavKeyDown}
                >
                  {visibleNavItems.map((item) => {
                    const Icon = item.icon
                    return (
                      <Link
                        key={item.path}
                        to={item.path}
                        onClick={() => track('nav_click', { path: item.path, label: item.label })}
                        onMouseEnter={() => prefetchRouteDebounced(item.path)}
                        className={`
                          relative flex items-center gap-2 px-3 py-2 rounded-lg transition-all outline-none focus-visible:ring-2 focus-visible:ring-primary/50
                          ${
                            isActive(item.path)
                              ? 'bg-primary-600 text-white font-semibold shadow-sm dark:bg-primary-500 dark:text-white'
                              : 'text-gray-700 hover:bg-gray-100 hover:text-gray-900 dark:text-slate-300 dark:hover:bg-slate-700 dark:hover:text-white'
                          }
                        `}
                        aria-current={isActive(item.path) ? 'page' : undefined}
                        title={item.label}
                      >
                        <Icon className="w-5 h-5" aria-hidden />
                        <span className="hidden sm:inline">{t(`nav.${navKeyFromPath(item.path.replace(/^\/[a-z]{2}(?:-[A-Z]{2})?/, '') )}.label`, item.label)}</span>
                      </Link>
                    )
                  })}
                </nav>
              )}
            </div>
          </div>
        </div>
      </header>

      <div ref={liveRegionRef} className="sr-only" aria-live="polite" aria-atomic="true" />
      {showUserMenu && (
        <div
          className="fixed inset-0 bg-background/60 backdrop-blur-sm z-40"
          aria-hidden
          onClick={() => setShowUserMenu(false)}
        />
      )}
      
      {/* Main Content Area */}
      {showSidebar ? (
        <div className="flex-1">
          {/* Mobile Sidebar Overlay */}
          <AnimatePresence>
          {sidebarOpen && (
            <div
              className="fixed inset-0 z-40 lg:hidden"
              role="dialog"
              aria-modal="true"
              aria-labelledby="mobile-sidebar-title"
              tabIndex={-1}
              onKeyDown={(e) => { if (e.key === 'Escape') setSidebarOpen(false) }}
            >
              <motion.div
                className="fixed inset-0 bg-black/40"
                onClick={() => setSidebarOpen(false)}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: prefersReducedMotion ? 0 : 0.18, ease: 'easeOut' }}
              />
              <motion.aside
                data-tour="sidebar"
                className="fixed inset-y-0 left-0 z-50 w-64 overflow-y-auto bg-white/90 dark:bg-slate-900/90 backdrop-blur-md border-r border-gray-200 dark:border-slate-800 shadow-xl"
                initial={{ x: prefersReducedMotion ? 0 : -24, opacity: prefersReducedMotion ? 1 : 0, scale: prefersReducedMotion ? 1 : 0.995 }}
                animate={{ x: 0, opacity: 1, scale: 1 }}
                exit={{ x: prefersReducedMotion ? 0 : -24, opacity: prefersReducedMotion ? 1 : 0, scale: prefersReducedMotion ? 1 : 0.995 }}
                transition={{ duration: prefersReducedMotion ? 0 : 0.22, ease: [0.22, 1, 0.36, 1] }}
              >
                <div className="flex items-center justify-between px-4 py-4 border-b border-gray-200 dark:border-slate-800">
                  <div className="flex items-center gap-2">
                    <Search className="w-6 h-6 text-primary-600" aria-hidden />
                    <span id="mobile-sidebar-title" className="font-semibold text-sm">Navigation</span>
                  </div>
                  <button
                    onClick={() => setSidebarOpen(false)}
                    className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-slate-800"
                    aria-label="Schließen"
                  >
                    <X className="h-5 w-5" aria-hidden />
                  </button>
                </div>
                <motion.nav
                  className="px-3 py-4"
                  aria-label="Mobile Sidebar"
                  initial="closed"
                  animate="open"
                  exit="closed"
                  variants={{
                    open: { transition: { staggerChildren: prefersReducedMotion ? 0 : 0.035, delayChildren: prefersReducedMotion ? 0 : 0.05 } },
                    closed: { transition: { staggerChildren: prefersReducedMotion ? 0 : 0.02, staggerDirection: -1 } }
                  }}
                >
                  <div className="space-y-1">
                    {/* Hauptnavigation */}
                    <div className="mb-6">
                      <div className="px-3 mb-2 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Hauptbereich
                      </div>
                      {visibleNavItems.slice(0, 3).map((item) => {
                        const Icon = item.icon
                        return (
                          <motion.div
                            key={item.path}
                            initial={{ opacity: prefersReducedMotion ? 1 : 0, x: prefersReducedMotion ? 0 : -8 }}
                            animate={{ opacity: 1, x: 0 }}
                            exit={{ opacity: prefersReducedMotion ? 1 : 0, x: prefersReducedMotion ? 0 : -8 }}
                            transition={{ duration: prefersReducedMotion ? 0 : 0.18, ease: 'easeOut' }}
                          >
                          <Link
                            to={item.path}
                            onClick={() => { setSidebarOpen(false); track('nav_click', { path: item.path, label: item.label }) }}
                            className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40 ${isActive(item.path) ? 'bg-primary-600 text-white shadow-sm dark:bg-primary-500' : 'text-gray-700 hover:bg-gray-100 hover:text-gray-900 dark:text-slate-300 dark:hover:bg-slate-700 dark:hover:text-white'}`}
                            aria-current={isActive(item.path) ? 'page' : undefined}
                          >
                            <Icon className="h-5 w-5 flex-shrink-0" aria-hidden />
                            <span>{t(`nav.${navKeyFromPath(item.path.replace(/^\/[a-z]{2}(?:-[A-Z]{2})?/, '') )}.label`, item.label)}</span>
                          </Link>
                          </motion.div>
                        )
                      })}
                    </div>

                    {/* Analyse & Tools */}
                    <div className="mb-6">
                      <div className="px-3 mb-2 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Analyse & Tools
                      </div>
                      {visibleNavItems.slice(3, 10).map((item) => {
                        const Icon = item.icon
                        return (
                          <motion.div
                            key={item.path}
                            initial={{ opacity: prefersReducedMotion ? 1 : 0, x: prefersReducedMotion ? 0 : -8 }}
                            animate={{ opacity: 1, x: 0 }}
                            exit={{ opacity: prefersReducedMotion ? 1 : 0, x: prefersReducedMotion ? 0 : -8 }}
                            transition={{ duration: prefersReducedMotion ? 0 : 0.18, ease: 'easeOut' }}
                          >
                          <Link
                            to={item.path}
                            onClick={() => { setSidebarOpen(false); track('nav_click', { path: item.path, label: item.label }) }}
                            className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-all ${isActive(item.path) ? 'bg-primary-600 text-white shadow-sm dark:bg-primary-500' : 'text-gray-700 hover:bg-gray-100 hover:text-gray-900 dark:text-slate-300 dark:hover:bg-slate-700 dark:hover:text-white'}`}
                            aria-current={isActive(item.path) ? 'page' : undefined}
                          >
                            <Icon className="h-5 w-5 flex-shrink-0" aria-hidden />
                            <span>{t(`nav.${navKeyFromPath(item.path)}.label`, item.label)}</span>
                          </Link>
                          </motion.div>
                        )
                      })}
                    </div>

                    {/* System & Admin */}
                    <div>
                      <div className="px-3 mb-2 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        System & Admin
                      </div>
                      {visibleNavItems.slice(10).map((item) => {
                        const Icon = item.icon
                        return (
                          <motion.div
                            key={item.path}
                            initial={{ opacity: prefersReducedMotion ? 1 : 0, x: prefersReducedMotion ? 0 : -8 }}
                            animate={{ opacity: 1, x: 0 }}
                            exit={{ opacity: prefersReducedMotion ? 1 : 0, x: prefersReducedMotion ? 0 : -8 }}
                            transition={{ duration: prefersReducedMotion ? 0 : 0.18, ease: 'easeOut' }}
                          >
                          <Link
                            to={item.path}
                            onClick={() => { setSidebarOpen(false); track('nav_click', { path: item.path, label: item.label }) }}
                            className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-all ${isActive(item.path) ? 'bg-primary-600 text-white shadow-sm dark:bg-primary-500' : 'text-gray-700 hover:bg-gray-100 hover:text-gray-900 dark:text-slate-300 dark:hover:bg-slate-700 dark:hover:text-white'}`}
                            aria-current={isActive(item.path) ? 'page' : undefined}
                          >
                            <Icon className="h-5 w-5 flex-shrink-0" aria-hidden />
                            <span>{t(`nav.${navKeyFromPath(item.path)}.label`, item.label)}</span>
                          </Link>
                          </motion.div>
                        )
                      })}
                    </div>
                  </div>
                </motion.nav>
              </motion.aside>
            </div>
          )}
          </AnimatePresence>

          {/* Desktop Layout mit Sidebar */}
          <div className="flex h-full">
            {/* Desktop Sidebar */}
            <aside data-tour="sidebar" className="hidden lg:flex lg:flex-col lg:w-64 lg:fixed lg:inset-y-0 lg:top-14 lg:border-r lg:border-gray-200 dark:border-slate-800 lg:bg-white dark:bg-slate-900 lg:shadow-sm">
              <nav className="flex-1 px-3 py-4 overflow-y-auto" aria-label="Desktop Sidebar">
                <div className="space-y-1">
                  {/* Hauptnavigation */}
                  <div className="mb-6">
                    <div className="px-3 mb-2 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Hauptbereich
                    </div>
                    {visibleNavItems.slice(0, 3).map((item) => {
                      const Icon = item.icon
                      return (
                        <Link
                          key={item.path}
                          to={item.path}
                          onClick={() => track('nav_click', { path: item.path, label: item.label })}
                          className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all ${isActive(item.path) ? 'bg-primary-600 text-white shadow-sm' : 'text-gray-700 hover:bg-gray-100 dark:text-slate-300 dark:hover:bg-slate-800'}`}
                          aria-current={isActive(item.path) ? 'page' : undefined}
                          title={item.label}
                        >
                          <Icon className="h-5 w-5 flex-shrink-0" aria-hidden />
                          <span>{t(`nav.${navKeyFromPath(item.path)}.label`, item.label)}</span>
                        </Link>
                      )
                    })}
                  </div>

                  {/* Analyse & Tools */}
                  <div className="mb-6">
                    <div className="px-3 mb-2 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Analyse & Tools
                    </div>
                    {visibleNavItems.slice(3, 10).map((item) => {
                      const Icon = item.icon
                      return (
                        <Link
                          key={item.path}
                          to={item.path}
                          onClick={() => track('nav_click', { path: item.path, label: item.label })}
                          className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all ${isActive(item.path) ? 'bg-primary-600 text-white shadow-sm' : 'text-gray-700 hover:bg-gray-100 dark:text-slate-300 dark:hover:bg-slate-800'}`}
                          aria-current={isActive(item.path) ? 'page' : undefined}
                          title={item.label}
                        >
                          <Icon className="h-5 w-5 flex-shrink-0" aria-hidden />
                          <span>{t(`nav.${navKeyFromPath(item.path)}.label`, item.label)}</span>
                        </Link>
                      )
                    })}
                  </div>

                  {/* System & Admin */}
                  <div>
                    <div className="px-3 mb-2 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      System & Admin
                    </div>
                    {visibleNavItems.slice(10).map((item) => {
                      const Icon = item.icon
                      return (
                        <Link
                          key={item.path}
                          to={item.path}
                          onClick={() => track('nav_click', { path: item.path, label: item.label })}
                          className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all ${isActive(item.path) ? 'bg-primary-600 text-white shadow-sm' : 'text-gray-700 hover:bg-gray-100 dark:text-slate-300 dark:hover:bg-slate-800'}`}
                          aria-current={isActive(item.path) ? 'page' : undefined}
                          title={item.label}
                        >
                          <Icon className="h-5 w-5 flex-shrink-0" aria-hidden />
                          <span>{t(`nav.${navKeyFromPath(item.path)}.label`, item.label)}</span>
                        </Link>
                      )
                    })}
                  </div>
                </div>
              </nav>
            </aside>

            {/* Main Content mit Sidebar-Offset */}
            <main id="main-content" className="flex-1 lg:pl-64">
              <PageTransition variant="fade">
                {children}
              </PageTransition>
            </main>
          </div>
        </div>
      ) : (
        <main id="main-content" className="flex-1">
          <PageTransition variant="fade">
            {children}
          </PageTransition>
        </main>
      )}

      {/* Command Palette Overlay */}
      {isPaletteOpen && (
        <div className="fixed inset-0 z-[70]" role="dialog" aria-modal="true" aria-label="Command Palette">
          {/* Backdrop */}
          <div className="absolute inset-0 bg-black/40" onClick={togglePalette} />
          {/* Panel */}
          <div
            ref={paletteRef}
            className="relative mx-auto mt-24 w-full max-w-2xl rounded-xl border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-900 shadow-2xl overflow-hidden"
          >
            {/* Input */}
            <div className="flex items-center gap-2 px-4 py-3 border-b border-gray-200 dark:border-slate-800">
              <Search className="w-5 h-5 text-gray-500" aria-hidden />
              <input
                ref={paletteInputRef}
                value={paletteQuery}
                onChange={(e) => setPaletteQuery(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'ArrowDown') { e.preventDefault(); setPaletteIndex((i) => Math.min(i + 1, (filteredItems.length + Math.min(recentPalette.length, 5)) - 1)) }
                  else if (e.key === 'ArrowUp') { e.preventDefault(); setPaletteIndex((i) => Math.max(i - 1, 0)) }
                  else if (e.key === 'Enter') {
                    e.preventDefault()
                    const list: Array<{ path: string; label: string }> = paletteQuery.trim().length
                      ? filteredItems.map((n) => ({ path: n.path, label: n.label }))
                      : recentPalette.slice(0, 5)
                    const item = list[paletteIndex] || list[0]
                    if (item) navigateFromPalette(item, 'enter')
                  }
                }}
                placeholder={t('layout.quick_search_placeholder', 'Schnell suchen oder springen…')}
                className="flex-1 bg-transparent outline-none text-sm placeholder:text-gray-400 dark:placeholder:text-slate-500 py-1"
                aria-activedescendant={paletteIndex.toString()}
              />
              <button onClick={togglePalette} className="p-1.5 rounded-md hover:bg-gray-100 dark:hover:bg-slate-800" aria-label={t('common.close','Schließen')}>
                <X className="w-5 h-5" />
              </button>
            </div>
            {/* Results */}
            <div className="max-h-96 overflow-y-auto">
              {paletteQuery.trim().length ? (
                <ul role="listbox" aria-label="Suchergebnisse" className="py-1">
                  {filteredItems.map((n, idx) => (
                    <li key={n.path}>
                      <button
                        onMouseEnter={() => setPaletteIndex(idx)}
                        onClick={() => navigateFromPalette({ path: n.path, label: n.label }, 'click')}
                        className={`w-full flex items-center gap-3 px-4 py-2 text-sm text-left ${idx === paletteIndex ? 'bg-primary/10 text-primary' : 'hover:bg-muted'}`}
                        role="option"
                        aria-selected={idx === paletteIndex}
                      >
                        <span className="inline-flex items-center justify-center w-5 h-5">
                          {(() => { const Icon = (n as any).icon; return Icon ? <Icon className="w-4 h-4" /> : <span className="block w-2 h-2 rounded-full bg-current" /> })()}
                        </span>
                        <span className="font-medium">{n.label}</span>
                        <span className="ml-auto text-xs text-muted-foreground">{n.path}</span>
                      </button>
                    </li>
                  ))}
                  {filteredItems.length === 0 && (
                    <li className="px-4 py-6 text-sm text-muted-foreground">{t('common.no_results', 'Keine Treffer')}</li>
                  )}
                </ul>
              ) : (
                <div className="py-1">
                  <div className="px-4 py-1 text-xs uppercase tracking-wide text-muted-foreground">{t('common.recent', 'Zuletzt genutzt')}</div>
                  <ul role="listbox" aria-label="Zuletzt genutzt">
                    {recentPalette.slice(0, 5).map((it, idx) => (
                      <li key={it.path}>
                        <button
                          onMouseEnter={() => setPaletteIndex(idx)}
                          onClick={() => navigateFromPalette(it, 'recent')}
                          className={`w-full flex items-center gap-3 px-4 py-2 text-sm text-left ${idx === paletteIndex ? 'bg-primary/10 text-primary' : 'hover:bg-muted'}`}
                          role="option"
                          aria-selected={idx === paletteIndex}
                        >
                          <span className="inline-flex items-center justify-center w-5 h-5">
                            {(() => { const match = navItems.find(n => n.path === it.path); const Icon = (match as any)?.icon; return Icon ? <Icon className="w-4 h-4" /> : <span className="block w-2 h-2 rounded-full bg-current" /> })()}
                          </span>
                          <span className="font-medium">{it.label}</span>
                          <span className="ml-auto text-xs text-muted-foreground">{it.path}</span>
                        </button>
                      </li>
                    ))}
                    {recentPalette.length === 0 && (
                      <li className="px-4 py-6 text-sm text-muted-foreground">{t('layout.quick_search_hint', 'Tipp: Mit Cmd/Ctrl+K öffnen')}</li>
                    )}
                  </ul>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Footer */}
      <footer className="py-6 border-t border-gray-200 dark:border-slate-800 bg-muted/30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <p className="text-sm text-muted-foreground">
              © 2025 SIGMACODE Blockchain Forensics | Phase 0 (PoC) | Für Strafverfolgung, Compliance & Legal Teams · Mehr unter{' '}
              <a href="https://sigmacode.io" target="_blank" rel="noopener noreferrer" className="underline-offset-2 hover:underline">sigmacode.io</a>
            </p>
            <div className="mt-2">
              <button
                type="button"
                onClick={() => openCookieConsent(true)}
                className="text-xs underline underline-offset-2 hover:text-primary"
                aria-label="Cookie-Einstellungen"
              >
                Cookie-Einstellungen
              </button>
            </div>
          </div>
        </div>
      </footer>
      
      {/* Marketing ChatWidget - NUR auf Landingpages (/, /features, /pricing, etc.) */}
      {/* Im Dashboard-Bereich wird stattdessen das InlineChatPanel verwendet */}
      {!isDashboardArea && <ChatWidget />}
    </div>
  )
}

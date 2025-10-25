import React from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Shield, Github, Twitter, Linkedin, Mail, Menu, X, LayoutGrid, LogOut, Settings, FileText, LogIn, UserPlus } from 'lucide-react'
import { ThemeToggle } from '@/contexts/ThemeContext'
import { useI18n } from '@/contexts/I18nContext'
import { openCookieConsent } from '@/components/legal/CookieConsent'
import { useTranslation } from 'react-i18next'
import { useAuth } from '@/contexts/AuthContext'
import { track } from '@/lib/analytics'
import { authService } from '@/lib/auth'
import SeoI18n from '@/components/SeoI18n'
import { PageTransition } from '@/components/PageTransition'

interface PublicLayoutProps {
  children: React.ReactNode
}

export default function PublicLayout({ children }: PublicLayoutProps) {
  const { t, i18n } = useTranslation()
  const location = useLocation()
  const navigate = useNavigate()
  const { user, isAuthenticated, logout } = useAuth()
  const isActive = (path: string) => {
    // remove leading "/:lang" segment when comparing
    const current = location.pathname.replace(/^\/[a-zA-Z]{2}(?:-[A-Z]{2})?\b/, '') || '/'
    return current === path
  }
  const [mobileOpen, setMobileOpen] = React.useState(false)
  const [settingsOpen, setSettingsOpen] = React.useState(false)
  const [registerOpen, setRegisterOpen] = React.useState(false)
  const [groupsOpen, setGroupsOpen] = React.useState<{ [k: string]: boolean }>({ product: true, resources: true, company: true })
  const { currentLanguage, setLanguage, languages } = useI18n()
  const sortedLanguages = React.useMemo(() => {
    // Alle 42 Sprachen anzeigen (keine Allowlist mehr)
    return [...languages].sort((a, b) => {
      if (a.code === currentLanguage) return -1
      if (b.code === currentLanguage) return 1
      return a.nativeName.localeCompare(b.nativeName)
    })
  }, [languages, currentLanguage])

  const changeLanguage = async (lng: string) => {
    try {
      const prev = currentLanguage
      await setLanguage(lng)
      // zur gleichen Route mit neuem Sprachpräfix navigieren
      const pathname = location.pathname
      const suffix = pathname.replace(/^\/[a-zA-Z]{2}(?:-[A-Z]{2})?\b/, '') || '/'
      try { document.documentElement.setAttribute('lang', lng) } catch {}
      try { track('language_changed', { from: prev, to: lng, path: location.pathname }) } catch {}
      navigate(`/${lng}${suffix}${location.search}${location.hash}`)
    } catch {
      // noop
    }
  }
  // i18n state is provided by context; no local sync listener needed
  const [menuOpen, setMenuOpen] = React.useState(false)
  const menuRef = React.useRef<HTMLDivElement | null>(null)
  const settingsRef = React.useRef<HTMLDivElement | null>(null)
  const registerRef = React.useRef<HTMLDivElement | null>(null)
  const registerFirstItemRef = React.useRef<HTMLAnchorElement | null>(null)
  const settingsMenuId = 'settings-menu'
  const registerMenuId = 'auth-register-menu'
  const settingsButtonId = 'settings-button'
  const registerButtonId = 'register-button'
  const hoverTimerSettings = React.useRef<number | null>(null)
  const hoverTimerRegister = React.useRef<number | null>(null)
  const prefersReducedMotion = React.useMemo(() =>
    typeof window !== 'undefined' && window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches
  , [])
  const halo = React.useMemo(() => {
    const size = Math.random() > 0.5 ? 'h-9 w-9' : 'h-10 w-10'
    const dur = `${(2.2 + Math.random() * 1.2).toFixed(2)}s`
    const delay = `${(Math.random() * 1.4).toFixed(2)}s`
    const dur2 = `${(4.2 + Math.random() * 1.8).toFixed(2)}s`
    const delay2 = `${(Math.random() * 2.4).toFixed(2)}s`
    return { size, dur, delay, dur2, delay2 }
  }, [])

  // Cleanup hover timers on unmount
  React.useEffect(() => () => {
    if (hoverTimerSettings.current) window.clearTimeout(hoverTimerSettings.current)
    if (hoverTimerRegister.current) window.clearTimeout(hoverTimerRegister.current)
  }, [])

  // Focus first item when auth dropdown opens
  React.useEffect(() => {
    if (registerOpen) {
      const id = window.setTimeout(() => {
        registerFirstItemRef.current?.focus()
      }, 0)
      return () => window.clearTimeout(id)
    }
  }, [registerOpen])

  // Close menus on outside click / ESC
  React.useEffect(() => {
    function onDocClick(e: MouseEvent) {
      const target = e.target as Node
      if (menuRef.current && !menuRef.current.contains(target)) setMenuOpen(false)
      if (settingsRef.current && !settingsRef.current.contains(target)) setSettingsOpen(false)
      if (registerRef.current && !registerRef.current.contains(target)) setRegisterOpen(false)
    }
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape') { setMenuOpen(false); setSettingsOpen(false); setRegisterOpen(false) }
    }
    document.addEventListener('mousedown', onDocClick)
    document.addEventListener('keydown', onKey)
    return () => {
      document.removeEventListener('mousedown', onDocClick)
      document.removeEventListener('keydown', onKey)
    }
  }, [])

  // Lock background scroll when overlays/menus are open
  React.useEffect(() => {
    const root = document.documentElement
    const lock = settingsOpen || mobileOpen || registerOpen
    const prevOverflow = root.style.overflow
    if (lock) {
      root.style.overflow = 'hidden'
    }
    return () => {
      root.style.overflow = prevOverflow
    }
  }, [settingsOpen, mobileOpen, registerOpen])

  const initials = React.useMemo(() => {
    const name = (user?.username || user?.email || '').trim()
    if (!name) return 'U'
    const parts = name.replace(/[^a-zA-Z0-9 ]/g, '').split(' ').filter(Boolean)
    if (parts.length === 0) return name.slice(0, 2).toUpperCase()
    const i1 = parts[0][0] || ''
    const i2 = parts.length > 1 ? parts[1][0] : (parts[0][1] || '')
    return (i1 + i2).toUpperCase()
  }, [user])

  const handleLogout = async () => {
    setMenuOpen(false)
    await logout().catch(() => authService.clearAuth())
    navigate(`/${currentLanguage}/login`)
  }
  const haloFooter = React.useMemo(() => {
    const size = Math.random() > 0.5 ? 'h-7 w-7' : 'h-8 w-8'
    const dur = `${(2.6 + Math.random() * 1.4).toFixed(2)}s`
    const delay = `${(Math.random() * 1.8).toFixed(2)}s`
    const dur2 = `${(5.0 + Math.random() * 2.0).toFixed(2)}s`
    const delay2 = `${(Math.random() * 3.0).toFixed(2)}s`
    return { size, dur, delay, dur2, delay2 }
  }, [])

  // Warten, bis i18next initialisiert ist, um Missing-Namespace-Warnungen zu vermeiden
  if (!i18n?.isInitialized) {
    return <div className="min-h-screen bg-background text-foreground" />
  }

  return (
    <div className="min-h-screen bg-background text-foreground">
      <SeoI18n />
      {/* Navigation */}
      <nav className="fixed top-0 w-full bg-background/80 backdrop-blur-lg border-b border-gray-200 dark:border-slate-800 z-50">
        <div className="container mx-auto max-w-6xl px-4 sm:px-6 py-2.5 sm:py-3.5">
          <div className="flex items-center justify-between">
            <Link to={`/${currentLanguage}`} className="group flex items-center space-x-2">
              <span className="relative inline-flex h-8 w-8 items-center justify-center">
                <span
                  className={`pointer-events-none motion-safe:animate-ping absolute inline-flex rounded-full bg-primary/10 group-hover:bg-primary/15 ${halo.size}`}
                  style={{ animationDuration: halo.dur, animationDelay: halo.delay }}
                />
                <span
                  className="pointer-events-none motion-safe:animate-ping absolute inline-flex h-10 w-10 rounded-full bg-primary/5 group-hover:bg-primary/8"
                  style={{ animationDuration: halo.dur2, animationDelay: halo.delay2 }}
                />
                <Shield className="relative h-8 w-8 text-primary logo-shield" />
              </span>
              <div className="leading-tight">
                <div className="text-xl font-bold">SIGMACODE</div>
                <div className="text-xs text-muted-foreground mt-0.5">Blockchain Forensics</div>
              </div>
            </Link>
            
            <div className="flex items-center space-x-2 sm:space-x-3 md:space-x-4">
              <button
                type="button"
                className="inline-flex items-center justify-center rounded-md p-2 hover:bg-muted focus:outline-none focus-visible:ring-2 focus-visible:ring-primary/50"
                aria-label={mobileOpen ? t('navigation.close_menu', { defaultValue: 'Close navigation' }) : t('navigation.open_menu', { defaultValue: 'Open navigation' })}
                aria-expanded={mobileOpen}
                onClick={() => setMobileOpen((v) => !v)}
              >
                {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
              </button>
              {/* Einstellungen Dropdown (Sprache + Theme + Konto) - kontrolliert */}
              <div className="relative hidden md:block" ref={settingsRef}>
                <Button
                  id={settingsButtonId}
                  variant="outline"
                  size="icon"
                  className="inline-flex items-center border-gray-300 dark:border-slate-600 hover:bg-gray-100 dark:hover:bg-slate-700"
                  aria-haspopup="menu"
                  aria-expanded={settingsOpen}
                  aria-controls={settingsOpen ? settingsMenuId : undefined}
                  onClick={() => { setSettingsOpen((v) => !v); if (!settingsOpen) { setRegisterOpen(false); track('settings_dropdown_open', { source: 'public_header' }) } }}
                  onMouseEnter={() => {
                    if (hoverTimerSettings.current) window.clearTimeout(hoverTimerSettings.current)
                    hoverTimerSettings.current = window.setTimeout(() => { setSettingsOpen(true); setRegisterOpen(false) }, 100)
                  }}
                  onMouseLeave={(e) => {
                    if (hoverTimerSettings.current) window.clearTimeout(hoverTimerSettings.current)
                    const to = e.relatedTarget as EventTarget | null
                    // Only call contains() if relatedTarget is a real Node
                    if (to instanceof Node && settingsRef.current && settingsRef.current.contains(to)) return
                    hoverTimerSettings.current = window.setTimeout(() => setSettingsOpen(false), 150)
                  }}
                  aria-label={t('navigation.settings', { defaultValue: 'Settings' })}
                >
                  <Settings className="h-5 w-5" />
                </Button>
                <AnimatePresence>
                {settingsOpen && (
                  <motion.div
                    role="menu"
                    aria-label={t('navigation.settings')}
                    id={settingsMenuId}
                    aria-labelledby={settingsButtonId}
                    initial={{ opacity: 0, y: -4, scale: 0.98 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, y: -4, scale: 0.98 }}
                    transition={{ duration: prefersReducedMotion ? 0 : 0.12, ease: 'easeOut' }}
                    className="absolute right-0 mt-2 w-72 rounded-lg border border-border bg-background shadow-xl ring-1 ring-primary/10 py-2 z-50"
                    onMouseEnter={() => {
                      if (hoverTimerSettings.current) window.clearTimeout(hoverTimerSettings.current)
                    }}
                    onMouseLeave={() => {
                      if (hoverTimerSettings.current) window.clearTimeout(hoverTimerSettings.current)
                      hoverTimerSettings.current = window.setTimeout(() => setSettingsOpen(false), 150)
                    }}
                  >
                    <div className="px-3 pb-2 text-xs text-muted-foreground">{t('common.language')}</div>
                    <div className="px-3 pb-3 space-y-1 max-h-64 overflow-y-auto">
                      {sortedLanguages.map((l) => (
                        <button
                          key={l.code}
                          onClick={() => changeLanguage(l.code)}
                          role="menuitemradio"
                          aria-checked={currentLanguage === l.code}
                          aria-label={`${l.nativeName}`}
                          className={`w-full text-left px-3 py-2.5 rounded-lg border transition-all duration-200 flex items-center gap-3 ${
                            currentLanguage === l.code
                              ? 'border-primary bg-primary/5 text-primary shadow-sm'
                              : 'border-border text-foreground hover:border-primary/50 hover:bg-muted/50 hover:text-primary'
                          }`}
                        >
                          <span className="text-lg">{l.flag}</span>
                          <span className={`font-medium ${currentLanguage === l.code ? 'text-primary' : ''}`}>
                            {l.nativeName}
                          </span>
                          {currentLanguage === l.code && (
                            <svg className="ml-auto h-4 w-4 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                            </svg>
                          )}
                        </button>
                      ))}
                    </div>
                    <div className="my-2 h-px bg-border/60" />
                    <div className="px-3 pb-2 text-xs text-muted-foreground">{t('common.theme')}</div>
                    <div className="px-3 pb-2">
                      <ThemeToggle />
                    </div>
                    <div className="my-2 h-px bg-border/60" />
                    <div className="px-3 pb-2 text-xs text-muted-foreground">{t('cookie.title_short', { defaultValue: 'Cookies' })}</div>
                    <div className="px-3 pb-2">
                      <button
                        type="button"
                        onClick={() => { setSettingsOpen(false); openCookieConsent(true) }}
                        className="w-full text-left px-3 py-2 text-sm rounded-md hover:bg-muted"
                        role="menuitem"
                        aria-label={t('cookie.manage', { defaultValue: 'Cookie-Einstellungen' })}
                      >
                        {t('cookie.manage', { defaultValue: 'Cookie-Einstellungen' })}
                      </button>
                    </div>
                    <div className="my-2 h-px bg-border/60" />
                    <div className="px-3 pb-2 text-xs text-muted-foreground">{t('common.documents', 'Dokumente')}</div>
                    <div className="px-3 pb-2">
                      <Link
                        to={`/${currentLanguage}/businessplan`}
                        onClick={() => setSettingsOpen(false)}
                        className="flex items-center gap-2 w-full text-left px-3 py-2 text-sm rounded-md hover:bg-muted transition-colors"
                        role="menuitem"
                      >
                        <FileText className="h-4 w-4 text-primary" />
                        <span>{t('navigation.businessplan', 'Businessplan & Förderung')}</span>
                      </Link>
                    </div>
                    <div className="my-2 h-px bg-border/60" />
                    {isAuthenticated && (
                      <div className="px-1 py-1">
                        <div className="px-3 pb-2 text-xs text-muted-foreground mb-2">{t('common.account')}</div>
                        <Link to={`/${currentLanguage}/dashboard`} className="flex items-center gap-2 px-3 py-2 text-sm hover:bg-muted" role="menuitem">
                          <LayoutGrid className="h-4 w-4" />
                          {t('navigation.dashboard')}
                        </Link>
                        <button onClick={handleLogout} className="flex w-full items-center gap-2 px-3 py-2 text-left text-sm hover:bg-muted" role="menuitem">
                          <LogOut className="h-4 w-4" />
                          {t('navigation.logout')}
                        </button>
                      </div>
                    )}
                    
                  </motion.div>
                )}
                </AnimatePresence>
              </div>
              {/* Desktop Auth Dropdown (Register primary + Login) */}
              {!isAuthenticated && (
                <div className="relative hidden md:block" ref={registerRef}>
                  <Button
                    id={registerButtonId}
                    size="sm"
                    className="px-3 sm:px-4 font-semibold shadow-md hover:shadow-lg inline-flex items-center"
                    aria-haspopup="true"
                    aria-expanded={registerOpen}
                    aria-label={t('auth.register.submit')}
                    aria-controls={registerOpen ? registerMenuId : undefined}
                    onClick={() => { setRegisterOpen((v) => !v); if (!registerOpen) { setSettingsOpen(false); track('auth_dropdown_open', { source: 'public_header' }) } }}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' || e.key === ' ' || e.key === 'ArrowDown') {
                        e.preventDefault()
                        if (!registerOpen) {
                          setRegisterOpen(true)
                          setSettingsOpen(false)
                          track('auth_dropdown_open', { source: 'public_header', key: e.key })
                        }
                        // focus handled by effect
                      }
                    }}
                    onMouseEnter={() => {
                      if (hoverTimerRegister.current) window.clearTimeout(hoverTimerRegister.current)
                      hoverTimerRegister.current = window.setTimeout(() => { setRegisterOpen(true); setSettingsOpen(false); try { import('@/pages/RegisterPage'); import('@/pages/LoginPage') } catch {} }, 100)
                    }}
                    onMouseLeave={(e) => {
                      if (hoverTimerRegister.current) window.clearTimeout(hoverTimerRegister.current)
                      const to = e.relatedTarget as EventTarget | null
                      if (to && to instanceof Node && registerRef.current && registerRef.current.contains(to)) return
                      hoverTimerRegister.current = window.setTimeout(() => setRegisterOpen(false), 150)
                    }}
                  >
                    {t('auth.register.submit')}
                    <span className="hidden lg:inline-block ml-2 text-[10px] leading-4 px-1.5 py-0.5 rounded bg-primary/10 text-primary font-semibold">
                      {t('common.start_free', 'Kostenlos starten')}
                    </span>
                    <svg className={`ml-1 h-4 w-4 transition-transform ${registerOpen ? 'rotate-180' : ''}`} viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path fillRule="evenodd" d="M5.23 7.21a.75.75 0 011.06.02L10 11.085l3.71-3.855a.75.75 0 111.08 1.04l-4.24 4.4a.75.75 0 01-1.08 0l-4.24-4.4a.75.75 0 01.02-1.06z" clipRule="evenodd"/></svg>
                  </Button>
                  <AnimatePresence>
                  {registerOpen && (
                    <motion.div
                      role="menu"
                      aria-label={t('auth.register.submit')}
                      id={registerMenuId}
                      aria-labelledby={registerButtonId}
                      initial={{ opacity: 0, y: -4, scale: 0.98 }}
                      animate={{ opacity: 1, y: 0, scale: 1 }}
                      exit={{ opacity: 0, y: -4, scale: 0.98 }}
                      transition={{ duration: prefersReducedMotion ? 0 : 0.12, ease: 'easeOut' }}
                      className="absolute right-0 mt-2 w-60 rounded-lg border border-border bg-background shadow-xl ring-1 ring-primary/10 py-2 z-50"
                      onKeyDown={(e) => {
                        const items = Array.from((e.currentTarget as HTMLElement).querySelectorAll('[role=\"menuitem\"]')) as HTMLElement[]
                        const currentIndex = items.findIndex((el) => el === document.activeElement)
                        if (e.key === 'ArrowDown') {
                          e.preventDefault()
                          const next = items[(currentIndex + 1) % items.length]
                          next?.focus()
                        } else if (e.key === 'ArrowUp') {
                          e.preventDefault()
                          const prev = items[(currentIndex - 1 + items.length) % items.length]
                          prev?.focus()
                        } else if (e.key === 'Home') {
                          e.preventDefault(); items[0]?.focus()
                        } else if (e.key === 'End') {
                          e.preventDefault(); items[items.length - 1]?.focus()
                        } else if (e.key === 'Tab') {
                          e.preventDefault()
                          if (items.length === 0) return
                          const dir = e.shiftKey ? -1 : 1
                          const nextIndex = (currentIndex + dir + items.length) % items.length
                          items[nextIndex]?.focus()
                        }
                      }}
                      onMouseEnter={() => {
                        if (hoverTimerRegister.current) window.clearTimeout(hoverTimerRegister.current)
                      }}
                      onMouseLeave={() => {
                        if (hoverTimerRegister.current) window.clearTimeout(hoverTimerRegister.current)
                        hoverTimerRegister.current = window.setTimeout(() => setRegisterOpen(false), 150)
                      }}
                    >
                      <div className="px-1 py-1">
                        <Link
                          to={`/${currentLanguage}/register`}
                          onClick={() => { setRegisterOpen(false); track('auth_click_register', { source: 'public_header' }) }}
                          className="flex items-center gap-2 px-3 py-2 text-sm rounded-md hover:bg-muted font-semibold focus:outline-none focus:ring-2 focus:ring-primary/40"
                          role="menuitem"
                          tabIndex={0}
                          ref={registerFirstItemRef}
                          onMouseEnter={() => { try { import('@/pages/RegisterPage') } catch {} }}
                        >
                          <UserPlus className="h-4 w-4 text-primary" />
                          {t('auth.register.submit')}
                        </Link>
                        <Link
                          to={`/${currentLanguage}/login`}
                          onClick={() => { setRegisterOpen(false); track('auth_click_login', { source: 'public_header' }) }}
                          className="flex items-center gap-2 px-3 py-2 text-sm rounded-md hover:bg-muted focus:outline-none focus:ring-2 focus:ring-primary/40"
                          role="menuitem"
                          tabIndex={0}
                          onMouseEnter={() => { try { import('@/pages/LoginPage') } catch {} }}
                        >
                          <LogIn className="h-4 w-4" />
                          {t('auth.login.submit')}
                        </Link>
                      </div>
                    </motion.div>
                  )}
                  </AnimatePresence>
                </div>
              )}
              {/* Fallback Buttons on small screens */}
              <div className="md:hidden flex items-center gap-1">
                <Link to={`/${currentLanguage}/login`}>
                  <Button variant="outline" size="sm" className="px-3 font-medium border-gray-300 dark:border-slate-600">{t('auth.login.submit')}</Button>
                </Link>
                <Link to={`/${currentLanguage}/register`}>
                  <Button size="sm" className="px-3 font-semibold shadow-md">{t('auth.register.submit')}</Button>
                </Link>
              </div>
            </div>
          </div>
        </div>
      </nav>
      {/* Backdrops */}
      {settingsOpen && (
        <div
          className="fixed inset-0 bg-background/60 backdrop-blur-sm z-40"
          aria-hidden
          onClick={() => setSettingsOpen(false)}
        />
      )}
      {registerOpen && (
        <div
          className="fixed inset-0 bg-background/60 backdrop-blur-sm z-40"
          aria-hidden
          onClick={() => setRegisterOpen(false)}
        />
      )}
      {mobileOpen && (
        <div
          className={`fixed inset-0 bg-background/60 backdrop-blur-sm z-30 transition-opacity ${mobileOpen ? 'opacity-100' : 'opacity-0'}`}
          aria-hidden
          onClick={() => setMobileOpen(false)}
        />
      )}
      {/* Mobile nav panel */}
      <div
        className={`fixed top-[56px] sm:top-[64px] left-0 right-0 z-40 transition-transform duration-200 ${mobileOpen ? 'translate-y-0' : '-translate-y-2 pointer-events-none'} `}
        aria-hidden={!mobileOpen}
      >
        <div className={`mx-4 rounded-lg border border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/70 shadow-lg overflow-hidden ${mobileOpen ? 'opacity-100' : 'opacity-0'}`}>
          <nav className="flex flex-col py-2" onClick={() => setMobileOpen(false)}>
            <div className="px-2">
              <button
                type="button"
                aria-expanded={groupsOpen.product}
                aria-controls="group-product"
                className="w-full flex items-center justify-between px-2 py-2 rounded-md hover:bg-muted"
                onClick={(e) => { e.stopPropagation(); setGroupsOpen((p) => ({ ...p, product: !p.product })) }}
              >
                <span className="text-[11px] uppercase tracking-wide text-muted-foreground">{t('navigation.group_product', { defaultValue: 'Product' })}</span>
                <svg className={`h-4 w-4 transition-transform ${groupsOpen.product ? 'rotate-180' : ''}`} viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path fillRule="evenodd" d="M5.23 7.21a.75.75 0 011.06.02L10 11.085l3.71-3.855a.75.75 0 111.08 1.04l-4.24 4.4a.75.75 0 01-1.08 0l-4.24-4.4a.75.75 0 01.02-1.06z" clipRule="evenodd"/></svg>
              </button>
              <div id="group-product" className={`${groupsOpen.product ? 'block' : 'hidden'}`}>
                <Link to={`/${currentLanguage}`} className={`block px-4 py-3 text-sm ${isActive('/') ? 'text-primary font-medium' : 'text-foreground hover:text-primary'} transition`}>{t('navigation.home', { defaultValue: 'Home' })}</Link>
                <Link to={`/${currentLanguage}/features`} className={`block px-4 py-3 text-sm ${isActive('/features') ? 'text-primary font-medium' : 'text-foreground hover:text-primary'} transition`}>{t('navigation.features', { defaultValue: 'Features' })}</Link>
                <Link to={`/${currentLanguage}/use-cases`} className={`block px-4 py-3 text-sm ${isActive('/use-cases') || location.pathname.includes('/use-cases/') ? 'text-primary font-medium' : 'text-foreground hover:text-primary'} transition`}>{t('navigation.use_cases', { defaultValue: 'Use Cases' })}</Link>
                <Link to={`/${currentLanguage}/pricing`} className={`block px-4 py-3 text-sm ${isActive('/pricing') ? 'text-primary font-medium' : 'text-foreground hover:text-primary'} transition`}>{t('navigation.pricing', { defaultValue: 'Pricing' })}</Link>
              </div>
            </div>

            <div className="px-2 mt-2 border-t border-border/60 pt-2">
              <button
                type="button"
                aria-expanded={groupsOpen.company}
                aria-controls="group-company"
                className="w-full flex items-center justify-between px-2 py-2 rounded-md hover:bg-muted"
                onClick={(e) => { e.stopPropagation(); setGroupsOpen((p) => ({ ...p, company: !p.company })) }}
              >
                <span className="text-[11px] uppercase tracking-wide text-muted-foreground">{t('navigation.group_company', { defaultValue: 'Company' })}</span>
                <svg className={`h-4 w-4 transition-transform ${groupsOpen.company ? 'rotate-180' : ''}`} viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path fillRule="evenodd" d="M5.23 7.21a.75.75 0 011.06.02L10 11.085l3.71-3.855a.75.75 0 111.08 1.04l-4.24 4.4a.75.75 0 01-1.08 0l-4.24-4.4a.75.75 0 01.02-1.06z" clipRule="evenodd"/></svg>
              </button>
              <div id="group-company" className={`${groupsOpen.company ? 'block' : 'hidden'}`}>
                <Link to={`/${currentLanguage}/about`} className={`block px-4 py-3 text-sm ${isActive('/about') ? 'text-primary font-medium' : 'text-foreground hover:text-primary'} transition`}>{t('navigation.about', { defaultValue: 'About' })}</Link>
                <Link to={`/${currentLanguage}/businessplan`} className="block px-4 py-3 text-sm text-foreground hover:text-primary transition">
                  {t('navigation.businessplan', { defaultValue: 'Businessplan & Funding' })}
                </Link>
              </div>
            </div>

            <div className="px-2 mt-2 border-t border-border/60 pt-2">
              <button
                type="button"
                aria-expanded={groupsOpen.resources}
                aria-controls="group-resources"
                className="w-full flex items-center justify-between px-2 py-2 rounded-md hover:bg-muted"
                onClick={(e) => { e.stopPropagation(); setGroupsOpen((p) => ({ ...p, resources: !p.resources })) }}
              >
                <span className="text-[11px] uppercase tracking-wide text-muted-foreground">{t('navigation.group_preferences', { defaultValue: 'Preferences' })}</span>
                <svg className={`h-4 w-4 transition-transform ${groupsOpen.resources ? 'rotate-180' : ''}`} viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path fillRule="evenodd" d="M5.23 7.21a.75.75 0 011.06.02L10 11.085l3.71-3.855a.75.75 0 111.08 1.04l-4.24 4.4a.75.75 0 01-1.08 0l-4.24-4.4a.75.75 0 01.02-1.06z" clipRule="evenodd"/></svg>
              </button>
              <div id="group-resources" className={`${groupsOpen.resources ? 'block' : 'hidden'}`}>
                <div className="px-4 py-2">
                  <div className="text-xs text-muted-foreground mb-2">{t('common.language', { defaultValue: 'Language' })}</div>
                  <div className="space-y-1 max-h-64 overflow-y-auto">
                    {sortedLanguages.map((l) => (
                      <button
                        key={l.code}
                        onClick={(e) => { e.stopPropagation(); changeLanguage(l.code) }}
                        role="menuitemradio"
                        aria-checked={currentLanguage === l.code}
                        aria-label={`${l.nativeName}`}
                        className={`w-full text-left px-3 py-2.5 rounded-lg border transition-all duration-200 flex items-center gap-3 ${
                          currentLanguage === l.code
                            ? 'border-primary bg-primary/5 text-primary shadow-sm'
                            : 'border-border text-foreground hover:border-primary/50 hover:bg-muted/50 hover:text-primary'
                        }`}
                      >
                        <span className="text-lg">{l.flag}</span>
                        <span className={`font-medium ${currentLanguage === l.code ? 'text-primary' : ''}`}>
                          {l.nativeName}
                        </span>
                        {currentLanguage === l.code && (
                          <svg className="ml-auto h-4 w-4 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                          </svg>
                        )}
                      </button>
                    ))}
                  </div>
                </div>
                <div className="px-4 py-2">
                  <div className="text-xs text-muted-foreground mb-1">{t('common.theme', { defaultValue: 'Theme' })}</div>
                  <ThemeToggle />
                </div>
                <div className="px-4 py-2">
                  <div className="text-xs text-muted-foreground mb-1">{t('cookie.title_short', { defaultValue: 'Cookies' })}</div>
                  <button
                    type="button"
                    onClick={() => { setMobileOpen(false); openCookieConsent(true) }}
                    className="w-full text-left px-3 py-2 text-sm rounded-md border border-border hover:border-primary/50 hover:bg-muted/50"
                    aria-label={t('cookie.manage', { defaultValue: 'Cookie-Einstellungen' })}
                  >
                    {t('cookie.manage', { defaultValue: 'Cookie-Einstellungen' })}
                  </button>
                </div>
              </div>
            </div>

            <div className="px-4 pt-2 pb-3 grid grid-cols-2 gap-2">
              <Link to={`/${currentLanguage}/login`} className="col-span-1" onClick={() => { setMobileOpen(false); track('auth_click_login', { source: 'public_mobile' }) }}>
                <Button variant="outline" size="sm" className="w-full" aria-label={t('auth.login.submit')}>{t('auth.login.submit')}</Button>
              </Link>
              <Link to={`/${currentLanguage}/register`} className="col-span-1" onClick={() => { setMobileOpen(false); track('auth_click_register', { source: 'public_mobile' }) }}>
                <Button size="sm" className="w-full" aria-label={t('auth.register.submit')}>{t('auth.register.submit')}</Button>
              </Link>
            </div>
          </nav>
        </div>
      </div>

      {/* Content */}
      <main className="pt-16 sm:pt-20">
        <PageTransition variant="fade">
          {children}
        </PageTransition>
      </main>

      {/* Footer */}
      <footer className="px-4 sm:px-6 pt-10 sm:pt-12 pb-6 sm:pb-8 border-t border-transparent bg-muted/30 relative">
        {/* subtle gradient divider */}
        <div className="pointer-events-none absolute inset-x-0 -top-px h-px bg-gradient-to-r from-transparent via-primary/50 to-transparent" />
        <div className="container mx-auto max-w-6xl">
          <div className="grid md:grid-cols-4 gap-6 sm:gap-8 mb-8 sm:mb-10">
            <div>
              <div className="group flex items-center space-x-2 mb-4">
                <span className="relative inline-flex h-6 w-6 items-center justify-center">
                  <span
                    className={`pointer-events-none motion-safe:animate-ping absolute inline-flex rounded-full bg-primary/10 group-hover:bg-primary/15 ${haloFooter.size}`}
                    style={{ animationDuration: haloFooter.dur, animationDelay: haloFooter.delay }}
                  />
                  <span
                    className="pointer-events-none motion-safe:animate-ping absolute inline-flex h-9 w-9 rounded-full bg-primary/5 group-hover:bg-primary/8"
                    style={{ animationDuration: haloFooter.dur2, animationDelay: haloFooter.delay2 }}
                  />
                  <Shield className="relative h-6 w-6 text-primary logo-shield" />
                </span>
                <div className="flex flex-col items-start leading-none">
                  <span className="font-extrabold text-foreground tracking-tight">SIGMACODE.io</span>
                  <span className="text-xs text-muted-foreground tracking-wide mt-1">Blockchain Forensics</span>
                </div>
              </div>
              <p className="text-sm text-muted-foreground mb-4">
                {t('footer.tagline')}
              </p>
              <div className="flex items-center gap-2.5 sm:gap-3">
                <a aria-label="Twitter" href="https://twitter.com/sigmacode_io" target="_blank" rel="noopener noreferrer" className="inline-flex h-9 w-9 items-center justify-center rounded-full border border-border bg-background hover:bg-background/70 hover:border-primary/40 transition-colors">
                  <Twitter className="h-4 w-4" />
                </a>
                <a aria-label="LinkedIn" href="https://www.linkedin.com/company/sigmacode" target="_blank" rel="noopener noreferrer" className="inline-flex h-9 w-9 items-center justify-center rounded-full border border-border bg-background hover:bg-background/70 hover:border-primary/40 transition-colors">
                  <Linkedin className="h-4 w-4" />
                </a>
                <a aria-label="GitHub" href="https://github.com/sigmacode-io" target="_blank" rel="noopener noreferrer" className="inline-flex h-9 w-9 items-center justify-center rounded-full border border-border bg-background hover:bg-background/70 hover:border-primary/40 transition-colors">
                  <Github className="h-4 w-4" />
                </a>
                <a aria-label="Kontakt" href="mailto:contact@sigmacode.io" className="inline-flex h-9 w-9 items-center justify-center rounded-full border border-border bg-background hover:bg-background/70 hover:border-primary/40 transition-colors">
                  <Mail className="h-4 w-4" />
                </a>
              </div>
            </div>
            <div>
              <h4 className="font-semibold mb-4">{t('footer.product')}</h4>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li><Link to={`/${currentLanguage}/features`} className="hover:text-primary">{t('navigation.features')}</Link></li>
                <li><Link to={`/${currentLanguage}/chatbot`} className="hover:text-primary">Chatbot</Link></li>
                <li><Link to={`/${currentLanguage}/pricing`} className="hover:text-primary">{t('navigation.pricing')}</Link></li>
                <li><Link to={`/${currentLanguage}/dashboard`} className="hover:text-primary">{t('navigation.dashboard')}</Link></li>
                <li><Link to={`/${currentLanguage}/register`} className="hover:text-primary">{t('footer.request_demo')}</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-4">{t('footer.company')}</h4>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li><Link to={`/${currentLanguage}/about`} className="hover:text-primary">{t('navigation.about')}</Link></li>
                <li><a href="#" className="hover:text-primary">{t('footer.careers')}</a></li>
                <li><a href="#" className="hover:text-primary">{t('footer.contact')}</a></li>
                <li><Link to={`/${currentLanguage}/blog`} className="hover:text-primary">{t('footer.blog')}</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-4">{t('footer.legal')}</h4>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li><Link to={`/${currentLanguage}/legal/privacy`} className="hover:text-primary">{t('footer.privacy')}</Link></li>
                <li><Link to={`/${currentLanguage}/legal/terms`} className="hover:text-primary">{t('footer.terms')}</Link></li>
                <li><Link to={`/${currentLanguage}/legal/impressum`} className="hover:text-primary">{t('footer.imprint')}</Link></li>
                <li><a href="#" className="hover:text-primary">{t('footer.security')}</a></li>
              </ul>
            </div>
          </div>
          <div className="pt-5 sm:pt-6 mt-1 sm:mt-2 border-t border-border/60">
            <div className="flex flex-col md:flex-row items-center justify-between gap-3 sm:gap-4 text-xs sm:text-sm text-muted-foreground">
              <p>© {new Date().getFullYear()} SIGMACODE.io · Blockchain Forensics. {t('footer.rights_reserved')}</p>
              <div className="flex items-center gap-3 sm:gap-4">
                <Link to={`/${currentLanguage}/legal/privacy`} className="hover:text-primary">{t('footer.privacy')}</Link>
                <Link to={`/${currentLanguage}/legal/impressum`} className="hover:text-primary">{t('footer.imprint')}</Link>
                <a href="#" className="hover:text-primary">{t('footer.security')}</a>
                <button
                  type="button"
                  onClick={() => openCookieConsent(true)}
                  className="underline underline-offset-2 hover:text-primary"
                  aria-label={t('cookie.manage', { defaultValue: 'Cookie-Einstellungen' })}
                >
                  {t('cookie.manage', { defaultValue: 'Cookie-Einstellungen' })}
                </button>
              </div>
            </div>
          </div>
        </div>
      </footer>
      {/* Cookie Consent wird global in App.tsx gerendert */}
    </div>
  )
}

import type { ConsentState } from '@/components/legal/CookieConsent'
import { getConsent, onConsentChange } from '@/lib/consent'

interface DeviceFingerprint {
  canvas: string
  webgl: string
  audio: string
  fonts: string[]
  plugins: string[]
  screen: {
    width: number
    height: number
    colorDepth: number
    pixelRatio: number
  }
  timezone: string
  language: string
  platform: string
  hardwareConcurrency: number
  deviceMemory?: number
  maxTouchPoints: number
}

interface UserBehavior {
  mouseMovements: Array<{ x: number; y: number; timestamp: number }>
  clicks: Array<{ x: number; y: number; element: string; timestamp: number }>
  scrollDepth: number
  timeOnPage: number
  interactions: Array<{ type: string; target: string; timestamp: number }>
}

interface PerformanceMetrics {
  pageLoad: number
  domReady: number
  firstPaint: number
  firstContentfulPaint: number
  largestContentfulPaint: number
  timeToInteractive: number
  apiLatencies: Record<string, number[]>
  resourceTimings: Array<{ name: string; duration: number; size: number }>
}

interface NetworkInfo {
  effectiveType: string
  downlink: number
  rtt: number
  saveData: boolean
}

type CleanupFn = () => void

const STORAGE_KEY = 'ultimate_analytics_session_v2'
const MAX_MOUSE_MOVEMENTS = 150
const MAX_CLICKS = 200
const MAX_INTERACTIONS = 250
const MAX_ERRORS = 50
const MAX_RESOURCE_TIMINGS = 120
const MAX_LATENCY_SAMPLES = 25
const SAMPLE_INTERVAL_MS = 120
const DEFAULT_FLUSH_INTERVAL_MS = 30_000
const MIN_FLUSH_INTERVAL_MS = 5_000

const isBrowser = typeof window !== 'undefined'

const hasDoNotTrackEnabled = (): boolean => {
  if (!isBrowser) return false
  const dnt = navigator.doNotTrack || (window as any).doNotTrack || (navigator as any).msDoNotTrack
  return dnt === '1' || dnt === 'yes'
}

class UltimateAnalyticsTracker {
  private initialized = false
  private active = false
  private analyticsAllowed = false
  private currentConsent: ConsentState | null = null
  private sessionId: string | null = null
  private userId?: string
  private fingerprint?: DeviceFingerprint
  private behavior: UserBehavior = this.createEmptyBehavior()
  private performance: PerformanceMetrics = this.createEmptyPerformance()
  private errors: Array<{ message: string; stack?: string; timestamp: number }> = []
  private cleanupFns: CleanupFn[] = []
  private flushIntervalId: number | null = null
  private timeIntervalId: number | null = null
  private lcpObserver?: PerformanceObserver
  private consentUnsubscribe?: () => void
  private lastMouseSample = 0
  private lastFlush = 0
  private startTimestamp = 0
  private readonly endpoint: string

  private handleMouseMove = (event: MouseEvent) => {
    if (!this.active) return
    const now = typeof performance !== 'undefined' ? performance.now() : Date.now()
    if (now - this.lastMouseSample < SAMPLE_INTERVAL_MS) return
    this.lastMouseSample = now
    this.behavior.mouseMovements.push({ x: event.clientX, y: event.clientY, timestamp: Date.now() })
    if (this.behavior.mouseMovements.length > MAX_MOUSE_MOVEMENTS) {
      this.behavior.mouseMovements.splice(0, this.behavior.mouseMovements.length - MAX_MOUSE_MOVEMENTS)
    }
  }

  private handleClick = (event: MouseEvent) => {
    if (!this.active) return
    const target = event.target as HTMLElement | null
    this.behavior.clicks.push({
      x: event.clientX,
      y: event.clientY,
      element: target ? this.getElementSelector(target) : 'unknown',
      timestamp: Date.now()
    })
    if (this.behavior.clicks.length > MAX_CLICKS) {
      this.behavior.clicks.splice(0, this.behavior.clicks.length - MAX_CLICKS)
    }
  }

  private handleScroll = () => {
    if (!this.active) return
    const total = document.documentElement.scrollHeight - window.innerHeight
    if (total <= 0) return
    const depth = Math.round((window.scrollY / total) * 100)
    if (depth > this.behavior.scrollDepth) {
      this.behavior.scrollDepth = depth
    }
  }

  private handleError = (event: ErrorEvent) => {
    if (!this.active) return
    this.errors.push({
      message: event.message,
      stack: event.error?.stack,
      timestamp: Date.now()
    })
    if (this.errors.length > MAX_ERRORS) {
      this.errors.splice(0, this.errors.length - MAX_ERRORS)
    }
  }

  private handleUnhandledRejection = (event: PromiseRejectionEvent) => {
    if (!this.active) return
    this.errors.push({
      message: `Unhandled Promise Rejection: ${String(event.reason)}`,
      timestamp: Date.now()
    })
    if (this.errors.length > MAX_ERRORS) {
      this.errors.splice(0, this.errors.length - MAX_ERRORS)
    }
  }

  private handleBeforeUnload = () => {
    if (!this.active) return
    void this.flush(true)
  }

  constructor() {
    const baseUrl = (import.meta.env.VITE_API_URL as string | undefined) || ''
    const normalized = baseUrl ? baseUrl.replace(/\/$/, '') : ''
    this.endpoint = normalized ? `${normalized}/api/v1/analytics/track` : '/api/v1/analytics/track'
  }

  public initialize() {
    if (!isBrowser || this.initialized) return
    this.initialized = true
    this.applyConsent(getConsent())
    this.consentUnsubscribe = onConsentChange((consent) => {
      this.applyConsent(consent)
    })
  }

  public shutdown() {
    if (!this.initialized) return
    this.consentUnsubscribe?.()
    this.consentUnsubscribe = undefined
    this.deactivate()
    this.initialized = false
    this.analyticsAllowed = false
    this.currentConsent = null
  }

  public setUserId(userId: string) {
    this.ensureInitialized()
    this.ensureActive()
    this.userId = userId
  }

  public trackEvent(eventName: string, properties: Record<string, any> = {}) {
    this.ensureInitialized()
    this.ensureActive()
    if (!this.active) return
    this.behavior.interactions.push({
      type: eventName,
      target: JSON.stringify(properties ?? {}),
      timestamp: Date.now()
    })
    if (this.behavior.interactions.length > MAX_INTERACTIONS) {
      this.behavior.interactions.splice(0, this.behavior.interactions.length - MAX_INTERACTIONS)
    }
  }

  public trackAPICall(endpoint: string, duration: number) {
    this.ensureInitialized()
    this.ensureActive()
    if (!this.active) return
    if (!this.performance.apiLatencies[endpoint]) {
      this.performance.apiLatencies[endpoint] = []
    }
    this.performance.apiLatencies[endpoint].push(duration)
    if (this.performance.apiLatencies[endpoint].length > MAX_LATENCY_SAMPLES) {
      this.performance.apiLatencies[endpoint].splice(0, this.performance.apiLatencies[endpoint].length - MAX_LATENCY_SAMPLES)
    }
  }

  private ensureInitialized() {
    if (!this.initialized) {
      this.initialize()
    }
  }

  private ensureActive() {
    if (!this.analyticsAllowed || this.active) return
    this.activate()
  }

  private applyConsent(consent: ConsentState | null) {
    this.currentConsent = consent
    const allowed = !!consent?.analytics && !hasDoNotTrackEnabled()
    if (allowed === this.analyticsAllowed && this.active === allowed) return
    this.analyticsAllowed = allowed
    if (allowed) {
      this.activate()
    } else {
      this.deactivate()
      this.clearSession()
    }
  }

  private activate() {
    if (!isBrowser || this.active || !this.analyticsAllowed) return
    this.active = true
    if (!this.sessionId) {
      this.sessionId = this.generateSessionId()
    }
    this.startTimestamp = Date.now()
    this.behavior.timeOnPage = 0
    this.lastMouseSample = 0
    this.behavior.mouseMovements = []
    this.behavior.clicks = []
    this.behavior.interactions = []
    this.behavior.scrollDepth = 0
    this.errors = []
    this.performance = this.createEmptyPerformance()
    void this.captureFingerprint()
    this.registerEventListeners()
    this.capturePerformanceMetrics()
    this.scheduleTimers()
  }

  private deactivate() {
    if (!this.active) return
    this.active = false
    this.cleanupFns.forEach((fn) => fn())
    this.cleanupFns = []
    if (this.flushIntervalId !== null) {
      clearInterval(this.flushIntervalId)
      this.flushIntervalId = null
    }
    if (this.timeIntervalId !== null) {
      clearInterval(this.timeIntervalId)
      this.timeIntervalId = null
    }
    this.lcpObserver?.disconnect()
    this.lcpObserver = undefined
    this.behavior = this.createEmptyBehavior()
    this.performance = this.createEmptyPerformance()
    this.errors = []
    this.lastFlush = 0
  }

  private scheduleTimers() {
    if (!isBrowser) return
    if (this.flushIntervalId !== null) {
      clearInterval(this.flushIntervalId)
    }
    this.flushIntervalId = window.setInterval(() => {
      void this.flush()
    }, DEFAULT_FLUSH_INTERVAL_MS)

    if (this.timeIntervalId !== null) {
      clearInterval(this.timeIntervalId)
    }
    this.timeIntervalId = window.setInterval(() => {
      if (!this.active) return
      this.behavior.timeOnPage = Math.max(0, Math.round((Date.now() - this.startTimestamp) / 1000))
    }, 1_000)
  }

  private registerEventListeners() {
    const addDocumentListener = <K extends keyof DocumentEventMap>(
      type: K,
      handler: (event: DocumentEventMap[K]) => void,
      options?: boolean | AddEventListenerOptions
    ) => {
      const wrapped = handler as unknown as EventListener
      document.addEventListener(type, wrapped, options)
      this.cleanupFns.push(() => document.removeEventListener(type, wrapped, options))
    }

    const addWindowListener = <K extends keyof WindowEventMap>(
      type: K,
      handler: (event: WindowEventMap[K]) => void,
      options?: boolean | AddEventListenerOptions
    ) => {
      const wrapped = handler as unknown as EventListener
      window.addEventListener(type, wrapped, options)
      this.cleanupFns.push(() => window.removeEventListener(type, wrapped, options))
    }

    addDocumentListener('mousemove', this.handleMouseMove, { passive: true })
    addDocumentListener('click', this.handleClick, { passive: true })
    addDocumentListener('scroll', this.handleScroll, { passive: true })
    addWindowListener('error', this.handleError)
    addWindowListener('unhandledrejection', this.handleUnhandledRejection)
    addWindowListener('beforeunload', () => this.handleBeforeUnload())
  }

  private async captureFingerprint() {
    if (!this.active || this.fingerprint) return
    try {
      this.fingerprint = await this.generateFingerprint()
    } catch (error) {
      if (import.meta.env.DEV) {
        console.warn('Fingerprint generation failed', error)
      }
    }
  }

  private capturePerformanceMetrics() {
    if (!isBrowser || typeof performance === 'undefined') return
    const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming | undefined
    if (navigation) {
      this.performance.pageLoad = navigation.loadEventEnd - navigation.fetchStart
      this.performance.domReady = navigation.domContentLoadedEventEnd - navigation.fetchStart
      this.performance.timeToInteractive = navigation.domInteractive - navigation.fetchStart
    }
    const paintEntries = performance.getEntriesByType('paint')
    for (const entry of paintEntries) {
      if (entry.name === 'first-paint') {
        this.performance.firstPaint = entry.startTime
      }
      if (entry.name === 'first-contentful-paint') {
        this.performance.firstContentfulPaint = entry.startTime
      }
    }
    try {
      this.lcpObserver?.disconnect()
      this.lcpObserver = new PerformanceObserver((list) => {
        const entries = list.getEntries()
        if (!entries.length) return
        const last = entries[entries.length - 1]
        if (typeof last.startTime === 'number') {
          this.performance.largestContentfulPaint = last.startTime
        }
      })
      this.lcpObserver.observe({ entryTypes: ['largest-contentful-paint'] })
    } catch {}

    const resources = performance.getEntriesByType('resource') as PerformanceResourceTiming[]
    if (resources?.length) {
      const slice = resources.slice(-MAX_RESOURCE_TIMINGS)
      this.performance.resourceTimings = slice.map((r) => ({
        name: r.name,
        duration: r.duration,
        size: r.transferSize || 0
      }))
    }
  }

  private async flush(force = false) {
    if (!isBrowser || !this.active || !this.sessionId) return
    const now = Date.now()
    if (!force && now - this.lastFlush < MIN_FLUSH_INTERVAL_MS) return
    this.lastFlush = now

    const payload = {
      session_id: this.sessionId,
      user_id: this.userId,
      fingerprint: this.fingerprint ?? null,
      behavior: this.behavior,
      performance: this.performance,
      network: this.getNetworkInfo(),
      errors: this.errors,
      timestamp: new Date().toISOString(),
      page: {
        url: window.location.href,
        title: document.title,
        referrer: document.referrer || null
      },
      consent_version: this.currentConsent?.version ?? null,
      events_count: this.behavior.interactions.length
    }

    try {
      if (navigator.sendBeacon) {
        const blob = new Blob([JSON.stringify(payload)], { type: 'application/json' })
        navigator.sendBeacon(this.endpoint, blob)
      } else {
        await fetch(this.endpoint, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
          keepalive: true
        })
      }
      this.errors = []
    } catch (error) {
      if (import.meta.env.DEV) {
        console.warn('Ultimate analytics flush failed', error)
      }
    }
  }

  private createEmptyBehavior(): UserBehavior {
    return {
      mouseMovements: [],
      clicks: [],
      scrollDepth: 0,
      timeOnPage: 0,
      interactions: []
    }
  }

  private createEmptyPerformance(): PerformanceMetrics {
    return {
      pageLoad: 0,
      domReady: 0,
      firstPaint: 0,
      firstContentfulPaint: 0,
      largestContentfulPaint: 0,
      timeToInteractive: 0,
      apiLatencies: {},
      resourceTimings: []
    }
  }

  private getNetworkInfo(): NetworkInfo | null {
    const connection = (navigator as any).connection || (navigator as any).mozConnection || (navigator as any).webkitConnection
    if (!connection) return null
    return {
      effectiveType: connection.effectiveType || 'unknown',
      downlink: Number(connection.downlink) || 0,
      rtt: Number(connection.rtt) || 0,
      saveData: Boolean(connection.saveData)
    }
  }

  private async generateFingerprint(): Promise<DeviceFingerprint> {
    return {
      canvas: this.getCanvasFingerprint(),
      webgl: this.getWebGLFingerprint(),
      audio: await this.getAudioFingerprint(),
      fonts: this.getInstalledFonts(),
      plugins: this.getPlugins(),
      screen: {
        width: window.screen.width,
        height: window.screen.height,
        colorDepth: window.screen.colorDepth,
        pixelRatio: window.devicePixelRatio
      },
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
      language: navigator.language,
      platform: navigator.platform,
      hardwareConcurrency: navigator.hardwareConcurrency,
      deviceMemory: (navigator as any).deviceMemory,
      maxTouchPoints: navigator.maxTouchPoints
    }
  }

  private getCanvasFingerprint(): string {
    const canvas = document.createElement('canvas')
    const ctx = canvas.getContext('2d')
    if (!ctx) return ''
    canvas.width = 200
    canvas.height = 50
    ctx.textBaseline = 'top'
    ctx.font = '14px Arial'
    ctx.fillStyle = '#f60'
    ctx.fillRect(125, 1, 62, 20)
    ctx.fillStyle = '#069'
    ctx.fillText('Ultimate Analytics', 2, 15)
    return canvas.toDataURL()
  }

  private getWebGLFingerprint(): string {
    const canvas = document.createElement('canvas')
    const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl')
    if (!gl) return ''
    const debugInfo = (gl as any).getExtension('WEBGL_debug_renderer_info')
    if (!debugInfo) return ''
    return (gl as any).getParameter(debugInfo.UNMASKED_RENDERER_WEBGL) || ''
  }

  private async getAudioFingerprint(): Promise<string> {
    try {
      const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext
      if (!AudioContextClass) return ''
      const audioContext = new AudioContextClass()
      const oscillator = audioContext.createOscillator()
      const analyser = audioContext.createAnalyser()
      const gainNode = audioContext.createGain()
      gainNode.gain.value = 0
      oscillator.connect(analyser)
      analyser.connect(gainNode)
      gainNode.connect(audioContext.destination)
      oscillator.start(0)
      const frequencyData = new Uint8Array(analyser.frequencyBinCount)
      analyser.getByteFrequencyData(frequencyData)
      oscillator.stop()
      audioContext.close().catch(() => {})
      return Array.from(frequencyData.slice(0, 32)).join(',')
    } catch {
      return ''
    }
  }

  private getInstalledFonts(): string[] {
    const baseFonts = ['monospace', 'sans-serif', 'serif']
    const testFonts = [
      'Arial', 'Verdana', 'Courier New', 'Georgia', 'Times New Roman',
      'Comic Sans MS', 'Impact', 'Trebuchet MS', 'Palatino', 'Garamond',
      'Bookman', 'Avant Garde', 'Helvetica', 'Calibri', 'Cambria'
    ]
    const canvas = document.createElement('canvas')
    const ctx = canvas.getContext('2d')
    if (!ctx) return []
    const detected: string[] = []
    for (const font of testFonts) {
      let detectedFont = false
      for (const base of baseFonts) {
        ctx.font = `12px ${base}`
        const baseWidth = ctx.measureText('mmmmmmmmmmlli').width
        ctx.font = `12px ${font}, ${base}`
        const testWidth = ctx.measureText('mmmmmmmmmmlli').width
        if (baseWidth !== testWidth) {
          detectedFont = true
          break
        }
      }
      if (detectedFont) detected.push(font)
    }
    return detected
  }

  private getPlugins(): string[] {
    try {
      return Array.from(navigator.plugins || []).map((plugin) => plugin.name)
    } catch {
      return []
    }
  }

  private getElementSelector(element: HTMLElement): string {
    if (element.id) return `#${element.id}`
    if (typeof element.className === 'string' && element.className.length > 0) {
      return `.${element.className.split(' ')[0]}`
    }
    return element.tagName.toLowerCase()
  }

  private generateSessionId(): string {
    if (!isBrowser) {
      return `sess_${Date.now()}_${Math.random().toString(36).slice(2, 10)}`
    }
    const existing = window.localStorage.getItem(STORAGE_KEY)
    if (existing) return existing
    const uuid = typeof crypto !== 'undefined' && crypto.randomUUID ? crypto.randomUUID() : `sess_${Date.now()}_${Math.random().toString(36).slice(2, 10)}`
    window.localStorage.setItem(STORAGE_KEY, uuid)
    return uuid
  }

  private clearSession() {
    if (!isBrowser) return
    window.localStorage.removeItem(STORAGE_KEY)
    this.sessionId = null
  }
}

export const analyticsTracker = new UltimateAnalyticsTracker()

// Analytics helper with lazy provider loading (Plausible or GA4)
// Respects DNT and cookie consent stored in localStorage['cookie_consent']

import { getConsent } from '@/lib/consent'
import i18n from '@/i18n/config-optimized'

// Optional first-party fallback endpoint (keeps legacy support)
const API_URL = import.meta.env.VITE_API_URL || "";

// Provider envs
const PLAUSIBLE_DOMAIN = import.meta.env.VITE_PLAUSIBLE_DOMAIN as string | undefined;
const PLAUSIBLE_SCRIPT_URL = (import.meta.env.VITE_PLAUSIBLE_SCRIPT_URL as string | undefined) || 'https://plausible.io/js/plausible.js';
const GA4_ID = import.meta.env.VITE_GA4_ID as string | undefined;

let providerLoaded = false;
let provider: 'plausible' | 'ga4' | 'none' = 'none';
let currentUserId: string | undefined;

// Resolve UI language robustly (URL -> html[lang] -> i18n -> localStorage -> navigator)
function resolveLanguage(): string {
  try {
    // 1) URL first segment: /xx or /xx-XX
    const m = location.pathname.match(/^\/([a-z]{2}(?:-[A-Z]{2})?)(?:\/|$)/);
    if (m && m[1]) return m[1];
  } catch {}
  try {
    // 2) html lang attribute
    const htmlLang = document.documentElement.getAttribute('lang');
    if (htmlLang) return htmlLang;
  } catch {}
  try {
    // 3) i18n current language
    if (i18n && typeof i18n.language === 'string' && i18n.language) return i18n.language;
  } catch {}
  try {
    // 4) persisted user_language
    const saved = localStorage.getItem('user_language');
    if (saved) return saved;
  } catch {}
  try {
    // 5) browser locale
    if (navigator.language) return navigator.language;
  } catch {}
  return 'en';
}

function hasConsent(): boolean {
  if (typeof navigator !== 'undefined' && (navigator as any).doNotTrack === "1") return false;
  try {
    const c = getConsent();
    return !!c && c.version === 1 && c.analytics === true;
  } catch {
    return false;
  }
}

// Initialize provider immediately if consent exists and keep in sync on consent changes
export function initAnalyticsConsentBridge() {
  if (typeof window === 'undefined') return;
  try {
    const onChanged = () => {
      // reset local state; scripts remain loaded, but providerLoaded controls lazy init
      providerLoaded = false;
      if (hasConsent()) {
        void loadProvider();
      }
      // If consent revoked, we do not attempt to unload third-party scripts here.
    };

    // initial load if consent already granted
    if (hasConsent()) {
      void loadProvider();
    }

    // listen for consent changes (our canonical event)
    window.addEventListener('cookie-consent:changed', onChanged as EventListener);
    // listen for potential underscore variant (backward compatibility)
    window.addEventListener('cookie_consent_changed' as any, onChanged as any);
    // listen for cross-tab storage updates
    window.addEventListener('storage', (e: StorageEvent) => {
      if (e.key === 'cookie_consent') onChanged();
    });
  } catch {
    // noop
  }
}

function decideProvider(): 'plausible' | 'ga4' | 'none' {
  if (PLAUSIBLE_DOMAIN) return 'plausible';
  if (GA4_ID) return 'ga4';
  return 'none';
}

function ensureScriptOnce(src: string, attrs: Record<string, string> = {}): Promise<void> {
  return new Promise((resolve, reject) => {
    if (document.querySelector(`script[src="${src}"]`)) return resolve();
    const s = document.createElement('script');
    s.async = true;
    s.src = src;
    Object.entries(attrs).forEach(([k, v]) => s.setAttribute(k, v));
    s.onload = () => resolve();
    s.onerror = () => reject(new Error(`Failed to load script ${src}`));
    document.head.appendChild(s);
  });
}

async function loadProvider(): Promise<void> {
  if (providerLoaded) return;
  provider = decideProvider();
  switch (provider) {
    case 'plausible': {
      await ensureScriptOnce(PLAUSIBLE_SCRIPT_URL!, { 'data-domain': PLAUSIBLE_DOMAIN!, 'defer': '' });
      providerLoaded = true;
      break;
    }
    case 'ga4': {
      const id = GA4_ID!;
      await ensureScriptOnce(`https://www.googletagmanager.com/gtag/js?id=${encodeURIComponent(id)}`);
      (window as any).dataLayer = (window as any).dataLayer || [];
      (window as any).gtag = function (...args: any[]) { (window as any).dataLayer.push(args); };
      (window as any).gtag('js', new Date());
      (window as any).gtag('config', id, { anonymize_ip: true });
      providerLoaded = true;
      break;
    }
    default: {
      providerLoaded = true; // no provider -> no-op
    }
  }
}

function basePayload() {
  return {
    ts: Date.now() / 1000,
    path: location.pathname + location.search,
    referrer: document.referrer || undefined,
    session_id: getSessionId(),
    language: resolveLanguage(),
  };
}

function getSessionId(): string {
  const key = "sid";
  try {
    let sid = localStorage.getItem(key);
    if (!sid) {
      const generated = (crypto as any).randomUUID
        ? (crypto as any).randomUUID()
        : `${Date.now()}-${Math.random().toString(36).slice(2)}`;
      sid = generated;
      try { localStorage.setItem(key, generated); } catch {}
    }
    return sid || "";
  } catch {
    return "";
  }
}

export function identify(userId?: string) {
  if (!hasConsent()) return;
  currentUserId = userId || currentUserId;
  try {
    if (!providerLoaded) return;
    if (provider === 'ga4' && typeof (window as any).gtag === 'function' && GA4_ID && currentUserId) {
      (window as any).gtag('config', GA4_ID, { user_id: currentUserId });
    }
  } catch {}
}

export async function track(event: string, properties: Record<string, any> = {}, userId?: string) {
  if (!hasConsent()) return;
  try {
    await loadProvider();
  } catch {
    // ignore script load errors
  }

  try {
    // resolve org id from localStorage (best-effort)
    const orgId = (() => { try { return localStorage.getItem('org_id') || undefined } catch { return undefined } })();
    const effectiveUserId = userId || currentUserId;
    const lang = resolveLanguage();
    const props = { language: lang, ...properties, user_id: effectiveUserId, org_id: orgId };

    if (provider === 'plausible' && typeof (window as any).plausible === 'function') {
      (window as any).plausible(event, { props });
      return;
    }
    if (provider === 'ga4' && typeof (window as any).gtag === 'function') {
      (window as any).gtag('event', event, props);
      return;
    }
    // Fallback: optional first-party endpoint if configured
    if (API_URL) {
      await fetch(`${API_URL}/api/v1/analytics/events`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "Accept-Language": lang },
        body: JSON.stringify({ event, ...basePayload(), properties: props, user_id: effectiveUserId, org_id: orgId }),
        keepalive: true,
      });
    }
  } catch {
    // ignore
  }
}

export function pageview(userId?: string) {
  track("page_view", {}, userId);
}

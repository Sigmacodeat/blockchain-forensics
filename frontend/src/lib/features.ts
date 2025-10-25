/**
 * Feature Gates & Plan Authorization System
 * 
 * Zentrale Verwaltung von Plan-basierten Berechtigungen
 */

import type { User } from './auth'

export type PlanId = 'community' | 'starter' | 'pro' | 'business' | 'plus' | 'enterprise'

/**
 * Plan-Hierarchie (aufsteigend)
 */
const PLAN_HIERARCHY: PlanId[] = ['community', 'starter', 'pro', 'business', 'plus', 'enterprise']

/**
 * Feature-Definitionen: Welcher Plan benötigt welches Feature
 * 
 * KUNDE-FEATURES = Forensik-Tools (Hauptprodukt)
 * ADMIN-FEATURES = System-Management (nur Admins)
 */
export const FEATURE_GATES: Record<string, PlanId> = {
  // ========================================
  // KUNDEN-FEATURES (Forensik)
  // ========================================
  
  // Community (Kostenlos) - Basic Forensik
  'dashboard.basic': 'community',
  'cases.view': 'community',
  'tracing.basic': 'community',          // ✅ Bitcoin-Adressen tracen möglich!
  'alerts.view': 'community',
  'bridge_transfers.view': 'community',
  
  // Starter - Erweiterte Forensik
  'tracing.enhanced': 'starter',         // ✅ Mehr Traces, mehr Tiefe
  'labels.enrichment': 'starter',        // Labels für Adressen
  'webhooks.limited': 'starter',
  'reports.pdf': 'starter',
  'cases.create': 'starter',
  
  // Pro - Professional Forensik
  'investigator.access': 'pro',          // ✅ Graph Explorer
  'correlation.basic': 'pro',            // ✅ Pattern-Erkennung
  'case_management.full': 'pro',
  'graph_views.access': 'pro',
  'playbooks.editable': 'pro',
  'tracing.unlimited': 'pro',
  'analytics.trends': 'pro',             // ✅ Eigene Trend-Charts (org_id gefiltert)
  
  // Business - Enterprise Forensik
  'risk_policies.manage': 'business',
  'roles_permissions.manage': 'business',
  'sso.basic': 'business',
  'scheduled_reports': 'business',
  'compliance.reports': 'business',
  
  // Plus - Financial Institution Features
  'ai_agents.unlimited': 'plus',         // ✅ AI-Assistent
  'correlation.advanced': 'plus',
  'investigator.full': 'plus',
  'travel_rule.support': 'plus',
  'sanctions.all_lists': 'plus',
  'sso.saml': 'plus',
  'siem_exports.full': 'plus',
  'graph_exports.unlimited': 'plus',
  'audit_logs.advanced': 'plus',
  
  // Enterprise - Custom Solutions
  'chain_of_custody.full': 'enterprise',
  'eidas.signatures': 'enterprise',
  'data_residency.custom': 'enterprise',
  'vpc.onprem': 'enterprise',
  'private_indexers': 'enterprise',
  'integrations.grc_siem': 'enterprise',
  'white_label': 'enterprise',           // ✅ White-Label
  'support.dedicated': 'enterprise',
  'custom_policies': 'enterprise',
}

/**
 * Route-Zugriffskontrolle
 * 
 * KUNDE-ROUTEN = Forensik-Tools
 * ADMIN-ROUTEN = System-Management
 */
export const ROUTE_GATES: Record<string, { minPlan?: PlanId; roles?: string[] }> = {
  // ========================================
  // PUBLIC ROUTES
  // ========================================
  '/': {},
  '/features': {},
  '/pricing': {},
  '/about': {},
  '/contact': {},
  
  // ========================================
  // KUNDEN-ROUTEN (Forensik)
  // ========================================
  
  // Community+ (Basic Forensik)
  '/dashboard': { minPlan: 'community' },
  '/forensics': { minPlan: 'community' },
  '/cases': { minPlan: 'community' },
  '/trace': { minPlan: 'community' },              // ✅ Tracing ab Community!
  '/bridge-transfers': { minPlan: 'community' },
  '/billing': { minPlan: 'community' },
  
  // Starter+
  '/trace/tools': { minPlan: 'starter' },
  
  // Pro+ (Professional Forensik)
  '/investigator': { minPlan: 'pro' },             // Graph Explorer
  '/correlation': { minPlan: 'pro' },              // Pattern-Erkennung
  '/patterns': { minPlan: 'pro' },                 // Pattern-Detection (Peel Chain, Rapid Movement)
  '/privacy-demixing': { minPlan: 'pro' },          // Tornado Cash Demixing
  '/dashboards': { minPlan: 'pro' },               // Eigene Analytics/Charts
  '/analytics': { minPlan: 'pro' },                // Eigene Analytics (Fallback)
  '/api-keys': { minPlan: 'pro' },                 // Developer API Keys
  
  // Business+
  '/policies': { minPlan: 'business' },
  '/performance': { minPlan: 'business' },         // Eigene Performance-Metriken
  '/automation': { minPlan: 'business' },          // Automation Rules & Simulation
  '/webhooks': { minPlan: 'starter' },             // Webhooks ab Starter
  
  // Plus+
  '/ai-agent': { minPlan: 'plus' },                // AI-Assistent
  
  // ========================================
  // ADMIN-ROUTEN (System-Management)
  // ========================================
  '/admin': { roles: ['admin'] },
  '/admin/analytics': { roles: ['admin'] },        // ✅ Web-Analytics (Homepage-Traffic)
  '/admin/saas-metrics': { roles: ['admin'] },     // ✅ SaaS-Metriken (MRR, Churn)
  '/admin/users': { roles: ['admin'] },
  '/orgs': { roles: ['admin'] },
  '/monitoring': { roles: ['admin'] },
  '/web-analytics': { roles: ['admin'] },          // ✅ Legacy-Route
  '/monitoring/dashboard': { roles: ['admin'] },
}

/**
 * Prüft, ob ein User einen bestimmten Plan hat (oder höher)
 */
export function hasPlan(user: User | null, requiredPlan: PlanId): boolean {
  if (!user) return false
  // Fallback: Wenn kein Plan gesetzt ist, behandle Nutzer als 'community'
  const effectivePlan: PlanId = (user.plan as PlanId) || 'community'
  
  const userPlanIndex = PLAN_HIERARCHY.indexOf(effectivePlan)
  const requiredPlanIndex = PLAN_HIERARCHY.indexOf(requiredPlan)
  
  return userPlanIndex >= requiredPlanIndex
}

/**
 * Prüft, ob ein User ein bestimmtes Feature nutzen darf
 */
export function hasFeature(user: User | null, featureName: string): boolean {
  if (!user) return false
  
  // Admin hat Zugriff auf alles
  if (user.role === 'admin') return true
  
  // Prüfe explizite Features aus user.features[]
  if (user.features && user.features.includes(featureName)) {
    return true
  }
  
  // Prüfe Plan-basierte Features
  const requiredPlan = FEATURE_GATES[featureName]
  if (!requiredPlan) return false
  
  return hasPlan(user, requiredPlan)
}

/**
 * Prüft, ob ein User Zugriff auf eine Route hat
 */
export function canAccessRoute(user: User | null, route: string): boolean {
  // Admin hat Zugriff auf alles
  if (user?.role === 'admin') return true
  
  // Entferne Sprach-Prefix (z.B. /de/dashboard → /dashboard)
  const cleanRoute = route.replace(/^\/(de|en|fr|es|it|pt|nl|pl|ru|ja|zh|ar|he|tr|cs|sk|da|sv|no|fi|is|ga|be|sq|rm|lv|mt|nn)[\/]?/, '/')
  
  // Finde passende Gate-Definition
  const gate = ROUTE_GATES[cleanRoute] || {}
  
  // Keine Gates = öffentlich
  if (!gate.minPlan && !gate.roles) return true
  
  // Prüfe Rollen
  if (gate.roles && user) {
    if (gate.roles.includes(user.role)) return true
  }
  
  // Prüfe Plan
  if (gate.minPlan) {
    return hasPlan(user, gate.minPlan)
  }
  
  return false
}

/**
 * Gibt den Plan-Namen in lesbarer Form zurück
 */
export function getPlanDisplayName(planId: PlanId): string {
  const names: Record<PlanId, string> = {
    community: 'Community',
    starter: 'Starter',
    pro: 'Pro',
    business: 'Business',
    plus: 'Plus',
    enterprise: 'Enterprise',
  }
  return names[planId] || planId
}

/**
 * Badge-Variant für Plan-Display
 */
export function getPlanBadgeVariant(planId: PlanId): 'default' | 'secondary' | 'destructive' | 'outline' {
  if (planId === 'enterprise' || planId === 'plus') return 'default'
  if (planId === 'business' || planId === 'pro') return 'secondary'
  return 'outline'
}

/**
 * Upgrade-Message für gesperrte Features
 */
export function getUpgradeMessage(featureName: string): string {
  const requiredPlan = FEATURE_GATES[featureName]
  if (!requiredPlan) return 'Upgrade erforderlich'
  
  const planName = getPlanDisplayName(requiredPlan)
  return `Upgrade zu ${planName} erforderlich`
}

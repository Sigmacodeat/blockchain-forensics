import { test, expect } from '@playwright/test'

// Stabiler Dashboard Smoke Test ohne echtes Backend via Route-Mocking

test.describe('Dashboard Smoke (Mocked API)', () => {
  test.beforeEach(async ({ page, baseURL }) => {
    // 1) Auth in LocalStorage setzen, damit AuthContext user lädt
    await page.addInitScript(() => {
      const user = {
        id: 'e2e-pro-1',
        email: 'pro@example.com',
        username: 'pro-user',
        role: 'analyst',
        plan: 'pro',
        created_at: new Date().toISOString(),
        is_active: true,
      }
      localStorage.setItem('access_token',
        // dummy jwt with far future exp: header.payload.signature, payload has exp ~ year 2099
        'eyJhbGciOiJIUzI1NiJ9.eyJleHAiOjQwMDAwMDAwMDB9.signature'
      )
      localStorage.setItem('refresh_token', 'dummy-refresh-token')
      localStorage.setItem('user', JSON.stringify(user))
    })

    // 2) Routen mocken, die vom Dashboard aufgerufen werden
    await page.route('**/api/v1/auth/me', async (route) => {
      const body = {
        id: 'e2e-pro-1',
        email: 'pro@example.com',
        username: 'pro-user',
        role: 'analyst',
        plan: 'pro',
        created_at: new Date().toISOString(),
        is_active: true,
      }
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(body) })
    })

    await page.route('**/api/v1/system/health', async (route) => {
      const body = {
        status: 'healthy',
        uptime: 123456,
        version: '1.0.0',
        database: { connected: true, response_time: 12 },
        services: { alert_engine: true, graph_db: true, ml_service: true },
      }
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(body) })
    })

    await page.route('**/api/v1/alerts/ops**', async (route) => {
      const body = {
        alert_aging: { '24h': 3, '3d': 5, '7d': 2, '>7d': 1 },
        backlog_open_alerts: 4,
        backlog_open_cases: 2,
        analyst_throughput: 7,
      }
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(body) })
    })

    await page.route('**/api/v1/alerts/kpis**', async (route) => {
      const body = { fpr: 0.12, mttr: 18, sla_breach_rate: 0.05, sanctions_hits: 2 }
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(body) })
    })

    await page.route('**/api/v1/alerts/rules/effectiveness**', async (route) => {
      const body = [
        { rule: 'High Risk Inflow', total_alerts: 10, labeled: 9, false_positives: 2, fp_rate: 0.2 },
        { rule: 'Mixer Outflow', total_alerts: 5, labeled: 5, false_positives: 0, fp_rate: 0.0 },
      ]
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(body) })
    })

    await page.route('**/api/v1/audit/stats', async (route) => {
      const body = { total_logs: 100, failed_actions: 1, success_rate: 0.99, actions_by_type: { login: 10 }, last_24h_count: 5 }
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(body) })
    })

    await page.route('**/api/v1/alerts/summary', async (route) => {
      const body = {
        total_alerts: 12,
        suppression_rate: 0.5,
        by_severity: { low: 3, medium: 5, high: 3, critical: 1 },
        by_type: {},
        recent_alerts: [ { title: 'Suspicious inflow', severity: 'high' } ],
      }
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(body) })
    })

    await page.route('**/api/v1/cases/stats', async (route) => {
      const body = {
        total_cases: 7,
        by_status: { open: 3, investigating: 2, closed: 2 },
        by_priority: { high: 2, medium: 3, low: 2 },
        recent_cases: [],
      }
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(body) })
    })

    await page.route('**/api/v1/graph-analytics/stats/network', async (route) => {
      const body = { total_nodes: 1000, total_edges: 1200, network_density: 0.12, communities_detected: 5, high_risk_clusters: 2 }
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(body) })
    })

    await page.route('**/api/v1/ml/models', async (route) => {
      const body = [ { name: 'gnn', status: 'active' }, { name: 'demix', status: 'on_disk' } ]
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(body) })
    })

    // 3) Dashboard öffnen: MainDashboard liegt unter /:lang/dashboard-main
    await page.goto(`${baseURL}/en/dashboard-main`)
  })

  test('renders core dashboard sections', async ({ page }) => {
    // Warte bis erste API-Responses verarbeitet sind
    await page.waitForTimeout(200)

    // KPI-Bereich sichtbar (data-tour)
    await expect(page.locator('[data-tour="metrics"]')).toBeVisible()

    // Systemstatus-Region vorhanden (via id und role region)
    await expect(page.locator('#main-content[role="region"]')).toBeVisible()

    // Alerts-Überschrift oder Abschnitt vorhanden (fallback auf Icon-Section)
    await expect(page.locator('section, div').filter({ hasText: /alert/i }).first()).toBeVisible()

    // Cases-Übersicht vorhanden (fallback auf Icon-Section)
    await expect(page.locator('section, div').filter({ hasText: /case/i }).first()).toBeVisible()
  })
})

import { test, expect } from '@playwright/test'

// Sample result matching backend schema
const sampleResult = {
  success: true,
  data: {
    address: '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb',
    screened_chains: ['ethereum', 'polygon'],
    total_chains_checked: 2,
    aggregate_risk_score: 0.42,
    aggregate_risk_level: 'medium',
    highest_risk_chain: 'ethereum',
    is_sanctioned_any_chain: false,
    cross_chain_activity: true,
    chain_results: {
      ethereum: {
        chain_id: 'ethereum',
        address: '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb',
        risk_score: 0.6,
        risk_level: 'medium',
        is_sanctioned: false,
        labels: ['exchange', 'defi:uniswap'],
        attribution_evidence: [
          {
            source: 'exchange_label',
            confidence: 0.85,
            label: 'Known CEX',
            evidence_type: 'known_entity',
            timestamp: new Date().toISOString(),
            metadata: { source: 'label_database' },
            verification_method: 'label_repository',
          },
        ],
        exposure_summary: {
          direct_exposure: { mixer: 0.1 },
          indirect_exposure: { scam: 0.2 },
          total_exposure_score: 0.3,
        },
        transaction_count: 12,
        first_seen: null,
        last_activity: null,
        total_value_usd: 1234.56,
        counterparties: 7,
      },
      polygon: {
        chain_id: 'polygon',
        address: '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb',
        risk_score: 0.24,
        risk_level: 'low',
        is_sanctioned: false,
        labels: ['defi:aave'],
        attribution_evidence: [],
        exposure_summary: {
          direct_exposure: {},
          indirect_exposure: {},
          total_exposure_score: 0,
        },
        transaction_count: 3,
        first_seen: null,
        last_activity: null,
        total_value_usd: 210.11,
        counterparties: 2,
      },
    },
    screening_timestamp: new Date().toISOString(),
    processing_time_ms: 250.0,
    summary: {
      total_transactions: 15,
      total_value_usd: 1444.67,
      unique_counterparties: 9,
      all_labels: ['exchange', 'defi:uniswap', 'defi:aave'],
    },
  },
}

// Helper to stub API
async function stubUniversalScreening(routeBase: string, page: any) {
  await page.route(`${routeBase}/api/v1/universal-screening/screen`, async (route: any) => {
    const req = route.request()
    if (req.method() === 'POST') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(sampleResult),
      })
      return
    }
    await route.fallback()
  })
}

// E2E tests
// Assumes dev server at http://localhost:3000
const FRONTEND = process.env.FRONTEND_URL || 'http://localhost:3000'
const API = process.env.VITE_API_BASE_URL || 'http://localhost:8000'

test.describe('Universal Screening', () => {
  test('renders page and screens address (stubbed)', async ({ page }) => {
    await stubUniversalScreening(API, page)

    await page.goto(`${FRONTEND}/en/universal-screening`)

    const input = page.getByPlaceholder('0x... or bc1... or any wallet address')
    await expect(input).toBeVisible()

    await input.fill('0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb')
    await page.getByRole('button', { name: /Screen/i }).click()

    // Summary cards visible
    await expect(page.getByText(/Risk Level/i)).toBeVisible()
    await expect(page.getByText(/Chains Screened/i)).toBeVisible()

    // Chain results visible
    await expect(page.getByText(/Chain-Specific Results/i)).toBeVisible()
    await expect(page.getByText(/ethereum/i)).toBeVisible()
    await expect(page.getByText(/polygon/i)).toBeVisible()

    // Export buttons
    await expect(page.getByRole('button', { name: /Export JSON/i })).toBeVisible()
    await expect(page.getByRole('button', { name: /Export CSV/i })).toBeVisible()
    await expect(page.getByRole('button', { name: /Export PDF/i })).toBeVisible()
  })

  test('jurisdiction filter and batch modal open', async ({ page }) => {
    await stubUniversalScreening(API, page)
    await page.goto(`${FRONTEND}/en/universal-screening`)

    await page.getByPlaceholder('0x... or bc1... or any wallet address').fill('0xabc')
    await page.getByRole('button', { name: /Screen/i }).click()

    // Jurisdiction select exists
    const select = page.locator('select')
    await expect(select).toBeVisible()

    // Batch modal opens
    await page.getByRole('button', { name: /Batch/i }).click()
    await expect(page.getByText(/Batch Universal Screening/i)).toBeVisible()
  })

  test('monitor panel toggles', async ({ page }) => {
    await stubUniversalScreening(API, page)
    await page.goto(`${FRONTEND}/en/universal-screening`)

    await page.getByPlaceholder('0x... or bc1... or any wallet address').fill('0xabc')
    await page.getByRole('button', { name: /Screen/i }).click()

    const monitorBtn = page.getByRole('button', { name: /Monitor/i })
    await expect(monitorBtn).toBeVisible()
    await monitorBtn.click()

    await expect(page.getByText(/Live Monitor/i)).toBeVisible()
  })
})

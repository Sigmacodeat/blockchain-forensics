import { test, expect } from '@playwright/test'

// Helper: mock subgraph response
function mockSubgraph(address: string) {
  return {
    nodes: [
      { id: address, address, chain: 'evm', taint_received: 0.42, risk_level: 'MEDIUM', labels: ['test'], tx_count: 1, balance: 0 },
      { id: '0xneighbor', address: '0xneighbor', chain: 'evm', taint_received: 0.2, risk_level: 'LOW', labels: [], tx_count: 1, balance: 0 },
    ],
    edges: [
      { source: address, target: '0xneighbor', tx_hash: '0xtx1', value: 1.23, timestamp: '2025-01-01T00:00:00Z', type: 'transaction' },
    ],
  }
}

// Helper: mock path response
function mockPath(from: string, to: string) {
  return {
    path: [from, to],
    edges: [],
  }
}

// ⚠️  REQUIRES BACKEND API
test.describe.skip('Investigator Deep-Link Actions (BACKEND REQUIRED)', () => {
  test('action=expand triggers neighbor expansion and shows breadcrumb', async ({ page }) => {
    // Mock initial subgraph
    await page.route('**/api/v1/graph/subgraph**', route => {
      const url = new URL(route.request().url())
      const addr = url.searchParams.get('address') || '0xseed'
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(mockSubgraph(addr)) })
    })

    // Go to investigator with expand action
    await page.goto('/en/investigator?address=0xabc123456789&action=expand')

    // Wait for breadcrumb to appear with the address
    const crumb = page.getByRole('button', { name: /breadcrumb 1/i })
    await expect(crumb).toBeVisible()
    await expect(crumb).toHaveAttribute('aria-label', /0xabc123456789/i)
  })

  test('action=path shows Clear Path button when highlighted', async ({ page }) => {
    // Mock subgraph (called at least once)
    await page.route('**/api/v1/graph/subgraph**', route => {
      const url = new URL(route.request().url())
      const addr = url.searchParams.get('address') || '0xseed'
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(mockSubgraph(addr)) })
    })

    // Mock path endpoint
    await page.route('**/api/v1/graph/cross-chain/path**', route => {
      const url = new URL(route.request().url())
      const from = url.searchParams.get('source') || '0xfrom'
      const to = url.searchParams.get('target') || '0xto'
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(mockPath(from, to)) })
    })

    await page.goto('/en/investigator?address=0xaaaa11112222&action=path&target=0xbbbb33334444')

    // Clear Path button appears when highlightedPath is set
    const clearBtn = page.getByRole('button', { name: /Clear Path/i })
    await expect(clearBtn).toBeVisible()
    await clearBtn.click()
    // After clearing, the button should disappear
    await expect(clearBtn).toBeHidden({ timeout: 2000 })
  })
})

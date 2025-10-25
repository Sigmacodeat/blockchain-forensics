import { defineConfig } from 'vitest/config'
import { fileURLToPath } from 'url'
import { dirname, resolve } from 'path'

const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)

export default defineConfig({
  resolve: {
    alias: {
      '@': resolve(__dirname, './src'),
    },
  },
  test: {
    environment: 'jsdom',
    setupFiles: ['./tests/setup.ts'],
    globals: true,
    css: true,
    minWorkers: 1,
    exclude: [
      'node_modules/**',
      'dist/**',
      'playwright.config.ts',
      'tests/**/{consent,health,metrics,navigation}/**',
      'tests/e2e/**',
      // Exclude Playwright specs under the standalone e2e folder
      'e2e/**',
      'e2e/tests/**',
      'tests/chat-widget.spec.ts',
      'tests/investigator-deeplink.spec.ts',
      'tests/ai-agent-stream.spec.*',
    ],
    testTimeout: 10000,
  },
})

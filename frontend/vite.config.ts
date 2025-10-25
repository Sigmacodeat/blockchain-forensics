import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { sentryVitePlugin } from '@sentry/vite-plugin'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    react(),
    // Sentry plugin (safe even without DSN; only active on build when auth envs are present)
    sentryVitePlugin({
      org: process.env.SENTRY_ORG,
      project: process.env.SENTRY_PROJECT,
      authToken: process.env.SENTRY_AUTH_TOKEN,
      sourcemaps: { assets: './dist/**' },
      release: { name: process.env.SENTRY_RELEASE },
    }),
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    strictPort: true, // WICHTIG: Fail wenn Port 3000 belegt ist
    host: '0.0.0.0',
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    sourcemap: true,
    target: 'es2020',
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true,
      },
    },
    rollupOptions: {
      output: {
        manualChunks: {
          // Core React
          react: [
            'react',
            'react-dom',
            'react-router-dom',
          ],
          // UI Framework
          ui: [
            '@radix-ui/react-dialog',
            '@radix-ui/react-select',
            '@radix-ui/react-tabs',
            '@radix-ui/react-tooltip',
            'lucide-react',
            'framer-motion',
          ],
          // Charts
          charts_recharts: [
            'recharts',
          ],
          charts_d3: [
            'd3',
          ],
          // Graph Visualization
          graph_cytoscape: [
            'cytoscape',
          ],
          graph_force: [
            'react-force-graph-2d',
          ],
          // Code Editor
          editor: [
            'monaco-editor',
            '@monaco-editor/react',
          ],
          // Data Fetching
          query: [
            '@tanstack/react-query',
          ],
          // Monitoring
          sentry: [
            '@sentry/react',
          ],
          // i18n
          i18n: [
            'i18next',
            'react-i18next',
            'i18next-browser-languagedetector',
          ],
        },
        // Optimize chunk size
        chunkFileNames: (chunkInfo) => {
          // Separate vendor chunks by size
          if (chunkInfo.name.includes('node_modules')) {
            return 'assets/vendor/[name]-[hash].js';
          }
          return 'assets/[name]-[hash].js';
        },
        entryFileNames: 'assets/[name]-[hash].js',
        assetFileNames: 'assets/[name]-[hash][extname]',
      },
    },
    // Increase chunk size warning limit
    chunkSizeWarningLimit: 1000,
    reportCompressedSize: false, // Faster builds
  },
  // Optimize dependencies
  optimizeDeps: {
    include: [
      'react',
      'react-dom',
      'react-router-dom',
      '@tanstack/react-query',
    ],
  },
})

/**
 * Global Window Type Extensions
 * Erweitert das Window-Interface um zusätzliche Properties
 */

interface AnalyticsTrack {
  (event: string, properties?: Record<string, any>): void
}

interface Analytics {
  track: AnalyticsTrack
  identify?: (userId: string, traits?: Record<string, any>) => void
  page?: (name?: string, properties?: Record<string, any>) => void
  group?: (groupId: string, traits?: Record<string, any>) => void
}

declare global {
  interface Window {
    analytics?: Analytics
    ethereum?: any // MetaMask
    tronWeb?: any // TronLink
  }
}

export {}

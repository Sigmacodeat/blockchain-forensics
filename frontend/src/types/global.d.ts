/**
 * Global TypeScript Declarations
 * Erweitert globale Interfaces wie Window für Drittanbieter-Libraries
 */

// Segment Analytics Interface
interface SegmentAnalytics {
  track: (event: string, properties?: Record<string, any>) => void
  page: (name?: string, properties?: Record<string, any>) => void
  identify: (userId: string, traits?: Record<string, any>) => void
  reset: () => void
}

// Window Interface Extension
declare global {
  interface Window {
    // Segment Analytics (optional, da nicht immer geladen)
    analytics?: SegmentAnalytics
    
    // Ethereum Provider (MetaMask etc.)
    ethereum?: {
      isMetaMask?: boolean
      request: (args: { method: string; params?: any[] }) => Promise<any>
      on?: (event: string, callback: (...args: any[]) => void) => void
      removeListener?: (event: string, callback: (...args: any[]) => void) => void
    }
    
    // Tron Provider (TronLink)
    tronWeb?: {
      ready?: boolean
      defaultAddress?: {
        base58?: string
        hex?: string
      }
      trx?: {
        sign: (transaction: any) => Promise<any>
        sendRawTransaction: (signedTransaction: any) => Promise<any>
        getBalance: (address: string) => Promise<number>
      }
      transactionBuilder?: {
        sendTrx: (to: string, amount: number, from: string) => Promise<any>
      }
    }
  }
}

export {}

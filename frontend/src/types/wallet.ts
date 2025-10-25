
export interface Wallet {
  id: string
  chain: string
  address: string
  publicKey: string
  balance?: WalletBalance
  createdAt: number
  riskScore?: number
  riskFactors?: string[]
}

export interface WalletBalance {
  balance: string
  risk_score?: number
  risk_factors?: string[]
  last_updated: number
}

export interface Transaction {
  hash: string
  status: 'pending' | 'confirmed' | 'failed'
  analysis?: TransactionAnalysis
  timestamp: number
  from?: string
  to?: string
  value?: string
  gasPrice?: string
  gasUsed?: string
}

export interface TransactionAnalysis {
  risk_score: number
  risk_factors: string[]
  entity_types: string[]
  money_flow: 'inflow' | 'outflow' | 'internal'
  flagged_addresses: string[]
  recommendations: string[]
}

export interface HardwareWalletDevice {
  type: 'ledger' | 'trezor'
  model: string
  connected: boolean
  firmware_version: string
  supported_chains: string[]
}

export interface CreateWalletRequest {
  chain: string
  mnemonic?: string
}

export interface SignTransactionRequest {
  chain: string
  tx_data: {
    to: string
    value: string
    gasPrice?: string
    gasLimit?: number
    data?: string
  }
  private_key: string
}

export interface BroadcastTransactionRequest {
  chain: string
  signed_tx: string
}

export interface WalletHistoryRequest {
  wallet_id: string
  limit?: number
  offset?: number
}

export interface WalletAnalytics {
  total_balance: string
  risk_distribution: {
    low: number
    medium: number
    high: number
  }
  transaction_patterns: {
    inflows: number
    outflows: number
    internal: number
  }
  flagged_transactions: number
  recommendations: string[]
}

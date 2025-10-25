import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'

// Use relative API prefix to leverage Vite proxy and avoid CORS
const API_PREFIX = '/api'
const ENV_API_KEY = (import.meta as any).env?.VITE_API_KEY as string | undefined
const getHeaders = () => {
  // Align with useCases.ts: prefer env VITE_API_KEY, then localStorage 'api_key', then 'X-API-Key'
  const key =
    ENV_API_KEY ||
    (typeof localStorage !== 'undefined'
      ? localStorage.getItem('api_key') || localStorage.getItem('X-API-Key') || ''
      : '')
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  if (key) headers['X-API-Key'] = key
  return headers
}

export type BridgeLink = {
  from_address: string
  to_address: string
  chain_from: string
  chain_to: string
  bridge_name: string
  tx_hash: string
  timestamp: number | string
  value?: number
}

export type BridgeLinksResponse = {
  total_links: number
  links: BridgeLink[]
}

export type BridgeStats = {
  total_bridge_transactions: number
  unique_addresses: number
  top_bridges: Array<{ bridge_name: string; chain_from: string; chain_to: string; transaction_count: number }>
  chain_distribution: Record<string, number>
}

export type SupportedBridge = {
  bridge_name: string
  chain: string
  contract_count: number
  pattern_type: string
  metadata: {
    counterpart_chains: string[]
    method_selectors: string[]
    address: string
  }
}

export type SupportedBridgesResponse = {
  total_bridges: number
  supported_chains: string[]
  bridges: SupportedBridge[]
}

export function useBridgeLinks(params: { address?: string; chain_from?: string; chain_to?: string; limit?: number }) {
  const qs = useMemo(() => {
    const p = new URLSearchParams()
    if (params.address) p.set('address', params.address)
    if (params.chain_from) p.set('chain_from', params.chain_from)
    if (params.chain_to) p.set('chain_to', params.chain_to)
    p.set('limit', String(params.limit ?? 100))
    return p.toString()
  }, [params.address, params.chain_from, params.chain_to, params.limit])

  return useQuery<BridgeLinksResponse>({
    queryKey: ['bridge','links', qs],
    queryFn: async () => {
      const res = await fetch(`${API_PREFIX}/v1/bridge/links?${qs}`, { headers: getHeaders() })
      if (!res.ok) throw new Error(`Failed to fetch bridge links: ${res.status}`)
      return res.json()
    }
  })
}

export function useBridgeStats() {
  return useQuery<BridgeStats>({
    queryKey: ['bridge','statistics'],
    queryFn: async () => {
      const res = await fetch(`${API_PREFIX}/v1/bridge/statistics`, { headers: getHeaders() })
      if (!res.ok) throw new Error(`Failed to fetch stats: ${res.status}`)
      return res.json()
    }
  })
}

export function useSupportedBridges(chain?: string) {
  const qs = chain ? `?chain=${encodeURIComponent(chain)}` : ''
  return useQuery<SupportedBridgesResponse>({
    queryKey: ['bridge','supported', chain ?? 'all'],
    queryFn: async () => {
      const res = await fetch(`${API_PREFIX}/v1/bridge/supported-bridges${qs}`, { headers: getHeaders() })
      if (!res.ok) throw new Error(`Failed to fetch supported bridges: ${res.status}`)
      return res.json()
    }
  })
}

export function useAddressBridgeHistory(address: string | undefined, limit = 100) {
  return useQuery<{ address: string; total_bridge_transactions: number; bridges: any[]}>({
    queryKey: ['bridge','address', address, limit],
    enabled: !!address,
    queryFn: async () => {
      const res = await fetch(`${API_PREFIX}/v1/bridge/address/${encodeURIComponent(address!)}/bridges?limit=${limit}`, { headers: getHeaders() })
      if (!res.ok) throw new Error(`Failed to fetch address history: ${res.status}`)
      return res.json()
    }
  })
}

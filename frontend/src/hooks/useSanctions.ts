import { useQuery } from '@tanstack/react-query'

const API_BASE = '/api/v1/intel/sanctions'

export interface SanctionsScreenRequest {
  address?: string
  name?: string
  ens?: string
  lists?: ('ofac' | 'un' | 'eu' | 'uk')[]
  fuzzy_threshold?: number
}

export interface SanctionsAliasHit {
  alias: string
  kind: 'name' | 'aka' | 'ens' | 'address'
  confidence: number
  source: string
}

export interface SanctionsScreenResponse {
  matched: boolean
  entity_id?: string
  canonical_name?: string
  lists: string[]
  alias_hits: SanctionsAliasHit[]
  explain?: string
}

export interface SanctionsStats {
  sources: string[]
  versions: Record<string, string>
  counts: Record<string, number>
}

/**
 * Hook für Sanctions-Screening einer Adresse oder Entität
 */
export const useSanctionsScreen = (params: SanctionsScreenRequest) => {
  return useQuery({
    queryKey: ['sanctions', 'screen', params],
    queryFn: async (): Promise<SanctionsScreenResponse> => {
      const response = await fetch(`${API_BASE}/screen`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(params),
      })

      if (!response.ok) {
        throw new Error(`Sanctions screening failed: ${response.statusText}`)
      }

      return response.json()
    },
    enabled: !!(params.address || params.name || params.ens),
    staleTime: 5 * 60 * 1000, // 5 Minuten Cache
  })
}

/**
 * Hook für Sanctions-Statistiken
 */
export const useSanctionsStats = () => {
  return useQuery({
    queryKey: ['sanctions', 'stats'],
    queryFn: async (): Promise<SanctionsStats> => {
      const response = await fetch(`${API_BASE}/stats`)

      if (!response.ok) {
        throw new Error(`Sanctions stats failed: ${response.statusText}`)
      }

      return response.json()
    },
    staleTime: 10 * 60 * 1000, // 10 Minuten Cache
  })
}

/**
 * Hook für Batch-Screening
 */
export const useSanctionsBatchScreen = (items: SanctionsScreenRequest[]) => {
  return useQuery({
    queryKey: ['sanctions', 'batch', items],
    queryFn: async (): Promise<SanctionsScreenResponse[]> => {
      const response = await fetch(`${API_BASE}/screen/batch`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ items }),
      })

      if (!response.ok) {
        throw new Error(`Sanctions batch screening failed: ${response.statusText}`)
      }

      return response.json()
    },
    enabled: items.length > 0,
    staleTime: 5 * 60 * 1000,
  })
}

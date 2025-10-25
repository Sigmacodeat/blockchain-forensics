import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Case, Entity, EvidenceLink, CaseExport, CaseChecksum, CaseVerify, AttachmentMeta } from '@/types/case'

// API base URL
const API_BASE = '/api/v1/forensics'

// Helper to get API key from env or localStorage
const getApiKey = () => {
  return import.meta.env.VITE_API_KEY || localStorage.getItem('api_key') || ''
}

// Helper for API headers
const getHeaders = () => {
  const apiKey = getApiKey()
  return {
    'Content-Type': 'application/json',
    ...(apiKey && { 'X-API-Key': apiKey }),
  }
}

// Generic API fetch wrapper
const apiRequest = async (url: string, options: RequestInit = {}) => {
  const response = await fetch(url, {
    headers: getHeaders(),
    ...options,
  })

  if (!response.ok) {
    throw new Error(`API Error: ${response.status} ${response.statusText}`)
  }

  return response.json()
}

// Case Management Hooks
export const useCases = () => {
  return useQuery({
    queryKey: ['cases'],
    queryFn: () => apiRequest(`${API_BASE}/cases`),
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}

export const useCase = (caseId: string) => {
  return useQuery({
    queryKey: ['cases', caseId],
    queryFn: () => apiRequest(`${API_BASE}/cases/${caseId}`),
    enabled: !!caseId,
  })
}

export const useCreateCase = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: Omit<Case, 'case_id' | 'created_at' | 'status'>) =>
      apiRequest(`${API_BASE}/cases/create`, {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cases'] })
    },
  })
}

export const useAddEntity = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ caseId, entity }: { caseId: string; entity: Omit<Entity, 'case_id'> }) =>
      apiRequest(`${API_BASE}/cases/${caseId}/entities/add`, {
        method: 'POST',
        body: JSON.stringify(entity),
      }),
    onSuccess: (_, { caseId }) => {
      queryClient.invalidateQueries({ queryKey: ['cases', caseId] })
    },
  })
}

export const useLinkEvidence = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ caseId, evidence }: { caseId: string; evidence: Omit<EvidenceLink, 'case_id' | 'timestamp'> }) =>
      apiRequest(`${API_BASE}/cases/${caseId}/evidence/link`, {
        method: 'POST',
        body: JSON.stringify(evidence),
      }),
    onSuccess: (_, { caseId }) => {
      queryClient.invalidateQueries({ queryKey: ['cases', caseId] })
    },
  })
}

export const useCaseExport = (caseId: string) => {
  return useQuery({
    queryKey: ['cases', caseId, 'export'],
    queryFn: () => apiRequest(`${API_BASE}/cases/${caseId}/export`),
    enabled: !!caseId,
  })
}

export const useCaseExportCsv = (caseId: string) => {
  return useQuery({
    queryKey: ['cases', caseId, 'export-csv'],
    queryFn: () => apiRequest(`${API_BASE}/cases/${caseId}/export.csv`),
    enabled: !!caseId,
  })
}

export const useCaseChecksum = (caseId: string) => {
  return useQuery({
    queryKey: ['cases', caseId, 'checksum'],
    queryFn: () => apiRequest(`${API_BASE}/cases/${caseId}/checksum`),
    enabled: !!caseId,
  })
}

export const useVerifyCase = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ caseId, checksum, signature }: { caseId: string; checksum?: string; signature?: string }) =>
      apiRequest(`${API_BASE}/cases/${caseId}/verify`, {
        method: 'POST',
        body: JSON.stringify({ checksum_sha256: checksum, signature_hmac_sha256: signature }),
      }),
    onSuccess: (_, { caseId }) => {
      queryClient.invalidateQueries({ queryKey: ['cases', caseId] })
    },
  })
}

export const useExportCase = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ caseId, format }: { caseId: string; format: 'csv' | 'pdf' }) =>
      apiRequest(`${API_BASE}/cases/${caseId}/export.${format}`),
    onSuccess: (_, { caseId }) => {
      queryClient.invalidateQueries({ queryKey: ['cases', caseId] })
    },
  })
}

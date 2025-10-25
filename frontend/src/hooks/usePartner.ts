import { useCallback } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'

const PARTNER_BASE = '/api/v1/partner'
const ADMIN_BASE = '/api/v1/partner/admin'

export interface PartnerAccount {
  id: string
  user_id: string
  name: string | null
  referral_code: string
  commission_rate: number
  recurring_rate: number
  cookie_duration_days: number
  min_payout_usd: number
  is_active: boolean
  created_at: string
}

export interface PartnerAccountResponse {
  account: PartnerAccount
  stats: Record<string, number>
}

export interface PartnerCommission {
  id: string
  partner_id: string
  referred_user_id?: string | null
  payment_id?: number | null
  order_id?: string | null
  plan_name?: string | null
  amount_usd: number
  commission_rate: number
  commission_usd: number
  status: string
  event_time: string
  notes?: string | null
}

export interface PartnerReferral {
  id: string
  partner_id: string
  referred_user_id: string
  user_email?: string | null
  source?: string | null
  tracking_id?: string | null
  first_touch_at: string
  last_touch_at: string
  created_at: string
}

export interface PartnerListResponse<T> {
  data: T[]
  total: number
}

export interface PartnerPayout {
  id: string
  partner_id: string
  amount_usd: number
  status: 'requested' | 'approved' | 'paid' | 'canceled'
  requested_at: string
  paid_at?: string | null
  tx_ref?: string | null
  details?: Record<string, unknown> | null
  partner_user_id?: string | null
  updated_at?: string | null
}

export const usePartnerAccount = () => {
  return useQuery<PartnerAccountResponse>({
    queryKey: ['partner', 'account'],
    queryFn: async () => {
      const { data } = await api.get<PartnerAccountResponse>(`${PARTNER_BASE}/account`)
      return {
        account: {
          ...data.account,
          commission_rate: Number(data.account.commission_rate),
          recurring_rate: Number(data.account.recurring_rate),
          min_payout_usd: Number(data.account.min_payout_usd)
        },
        stats: data.stats ?? {}
      }
    }
  })
}

export const usePartnerCommissions = (status?: string, limit = 50, offset = 0) => {
  return useQuery<PartnerListResponse<PartnerCommission>>({
    queryKey: ['partner', 'commissions', { status, limit, offset }],
    queryFn: async () => {
      const params: Record<string, string | number | undefined> = { limit, offset }
      if (status) params.status = status
      const { data } = await api.get<PartnerListResponse<PartnerCommission>>(`${PARTNER_BASE}/commissions`, {
        params
      })
      const normalized = (data.data ?? []).map((item) => ({
        ...item,
        amount_usd: Number(item.amount_usd),
        commission_rate: Number(item.commission_rate),
        commission_usd: Number(item.commission_usd)
      }))
      return { data: normalized, total: data.total ?? normalized.length }
    }
  })
}

export const usePartnerReferrals = (limit = 50, offset = 0) => {
  return useQuery<PartnerListResponse<PartnerReferral>>({
    queryKey: ['partner', 'referrals', { limit, offset }],
    queryFn: async () => {
      const { data } = await api.get<PartnerListResponse<PartnerReferral>>(`${PARTNER_BASE}/referrals`, {
        params: { limit, offset }
      })
      return { data: data.data ?? [], total: data.total ?? 0 }
    }
  })
}

export const useRequestPartnerPayout = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (amountUsd: number) => {
      const { data } = await api.post(`${PARTNER_BASE}/payouts/request`, { amount_usd: amountUsd })
      return data
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['partner', 'account'] })
      void queryClient.invalidateQueries({ queryKey: ['partner', 'commissions'] })
    }
  })
}

export const useExportPartnerCommissions = () => {
  return useMutation({
    mutationFn: async (params: { status?: string }) => {
      const { data } = await api.get(`${PARTNER_BASE}/commissions/export`, {
        params,
        responseType: 'blob'
      })
      return data as Blob
    }
  })
}

export const useAdminPayouts = (status?: string, limit = 50, offset = 0) => {
  return useQuery<{ data: PartnerPayout[] }>({
    queryKey: ['partner', 'admin', 'payouts', { status, limit, offset }],
    queryFn: async () => {
      const params: Record<string, string | number | undefined> = { limit, offset }
      if (status) params.status = status
      const { data } = await api.get<{ data: PartnerPayout[] }>(`${ADMIN_BASE}/payouts`, { params })
      return { data: data.data ?? [] }
    }
  })
}

export const useApprovePartnerPayout = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (payoutId: string) => {
      const { data } = await api.put(`${ADMIN_BASE}/payouts/${payoutId}/approve`)
      return data
    },
    onSuccess: (_data, payoutId) => {
      void queryClient.invalidateQueries({ queryKey: ['partner', 'admin', 'payouts'] })
      void queryClient.invalidateQueries({ queryKey: ['partner', 'account'] })
      return payoutId
    }
  })
}

interface PayPartnerPayoutInput {
  payoutId: string
  txRef?: string
}

export const usePayPartnerPayout = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ payoutId, txRef }: PayPartnerPayoutInput) => {
      const { data } = await api.put(`${ADMIN_BASE}/payouts/${payoutId}/pay`, { tx_ref: txRef })
      return data
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['partner', 'admin', 'payouts'] })
      return true
    }
  })
}

export const usePartnerStats = () => {
  const { data } = usePartnerAccount()
  return data?.stats ?? {}
}

export const useTriggerPartnerExport = () => {
  const exportMutation = useExportPartnerCommissions()
  return useCallback(
    async (params: { status?: string; filename?: string } = {}) => {
      const blob = await exportMutation.mutateAsync({ status: params.status })
      const filename = params.filename ?? `partner-commissions-${new Date().toISOString().slice(0, 10)}.csv`
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = filename
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
    },
    [exportMutation]
  )
}

export interface PlanQuotas {
  chains: number | string
  seats: number | string
  credits_monthly: number | string
  traces_monthly?: number | string
  addresses: number | string
  cases: number | string
  alerts: number | string
  api_rate?: 'very_low' | 'low' | 'medium' | 'high' | 'very_high' | 'custom'
  queue_priority?: 'medium' | 'high' | 'dedicated' | 'custom'
}

export interface PlanSLA {
  type: 'community' | 'email' | 'priority' | 'contract'
  response_hours: number | null
  support?: '8x5_to_24x7'
  cs_manager?: boolean
}

export interface Plan {
  id: string
  name: string
  monthly_price_usd?: number
  yearly_price_usd?: number
  pricing?: 'custom'
  quotas: PlanQuotas
  features: Record<string, boolean | string>
  sla: PlanSLA
}

export interface PricingConfig {
  currency: 'USD'
  annual_discount_percent: number
  overage: { price_per_1000_credits_usd: number; monthly_cap_enabled: boolean }
  addons: Record<string, number>
  plans: Plan[]
}

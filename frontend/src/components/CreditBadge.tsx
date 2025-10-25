import React, { useEffect, useMemo, useState } from 'react'
import plans from '@/config/plans.json'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function CreditBadge() {
  const [tenantPlan, setTenantPlan] = useState<string>('')
  const [remaining, setRemaining] = useState<number | null>(null)
  const [loading, setLoading] = useState(false)
  const planConfig = plans as any
  const total = useMemo(() => {
    try {
      const p = (planConfig.plans || []).find((x:any)=>x.id===tenantPlan)
      const v = p?.quotas?.credits_monthly
      return typeof v === 'number' ? v : null
    } catch { return null }
  }, [planConfig, tenantPlan])
  const pct = useMemo(() => {
    if (remaining===null || total===null) return null
    return Math.max(0, Math.min(100, Math.round((remaining/total)*100)))
  }, [remaining, total])

  // Helper to get auth token
  const getAuthHeaders = (): Record<string, string> => {
    const token = localStorage.getItem('access_token');
    if (token) {
      return { 'Authorization': `Bearer ${token}` };
    }
    return {};
  };

  useEffect(() => {
    let ignore = false
    async function loadPlan() {
      try {
        const r = await fetch(`${API_BASE_URL}/api/v1/billing/tenant/plan`, {
          headers: getAuthHeaders(),
          credentials: 'include'
        })
        if (!r.ok) throw new Error('failed')
        const j = await r.json()
        if (!ignore) setTenantPlan(j.plan_id || '')
      } catch { if (!ignore) setTenantPlan('') }
    }
    loadPlan()
    return () => { ignore = true }
  }, [])

  useEffect(() => {
    let ignore = false
    async function load() {
      try {
        setLoading(true)
        const res = await fetch(`${API_BASE_URL}/api/v1/billing/usage/remaining`, {
          headers: getAuthHeaders(),
          credentials: 'include'
        })
        if (!res.ok) throw new Error('failed')
        const r = await res.json()
        if (!ignore) setRemaining(r.unlimited ? null : r.remaining)
      } catch {
        if (!ignore) setRemaining(null)
      } finally {
        if (!ignore) setLoading(false)
      }
    }
    load()
    const id = setInterval(load, 15000) // refresh periodically
    return () => { ignore = true; clearInterval(id) }
  }, [tenantPlan])

  return (
    <div className={`px-3 py-1 rounded-full text-xs border ${
      pct!==null && pct<=10 ? 'bg-red-50 text-red-700 border-red-200' : 'bg-gray-50 text-gray-700 border-gray-200'
    }`}>
      {loading ? 'Credits…' : remaining === null ? 'Credits: ∞' : (
        pct===null ? `Credits: ${remaining}` : `Credits: ${remaining} (${pct}%)`
      )}
    </div>
  )
}

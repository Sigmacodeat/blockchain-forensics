import React, { useEffect, useState } from 'react'
import api from '@/lib/api'

interface OrgMeta {
  id: string
  name: string
  owner_id?: string
  created_at?: string
}

export default function OrgSelector() {
  const [orgs, setOrgs] = useState<OrgMeta[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [orgId, setOrgId] = useState<string>(() => {
    try { return localStorage.getItem('org_id') || '' } catch { return '' }
  })

  useEffect(() => {
    let mounted = true
    const load = async () => {
      setLoading(true)
      setError(null)
      try {
        const res = await api.get('/api/v1/orgs')
        if (!mounted) return
        const list = Array.isArray(res.data?.organizations) ? res.data.organizations as OrgMeta[] : []
        setOrgs(list)
        // Auto-select first org if none set
        if (!orgId && list.length > 0) {
          setOrgId(list[0].id)
          try { localStorage.setItem('org_id', list[0].id) } catch {}
        }
      } catch (e: any) {
        if (!mounted) return
        setError(typeof e?.message === 'string' ? e.message : 'Fehler beim Laden der Organisationen')
      } finally {
        if (mounted) setLoading(false)
      }
    }
    load()
    return () => { mounted = false }
  }, [])

  const onChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const val = e.target.value
    setOrgId(val)
    try { localStorage.setItem('org_id', val) } catch {}
  }

  return (
    <div className="flex items-center gap-2">
      <label htmlFor="org-select" className="sr-only">Organisation</label>
      <select
        id="org-select"
        value={orgId}
        onChange={onChange}
        disabled={loading}
        className="text-sm px-2 py-1 rounded-md border border-border bg-background hover:bg-muted focus:outline-none focus:ring-2 focus:ring-primary/40 min-w-[10rem]"
        aria-label="Organisation wählen"
        title={orgId ? `Aktive Org: ${orgs.find(o => o.id === orgId)?.name || orgId}` : 'Organisation wählen'}
      >
        {orgs.length === 0 && <option value="">Keine Organisationen</option>}
        {orgs.map((o) => (
          <option key={o.id} value={o.id}>{o.name}</option>
        ))}
      </select>
    </div>
  )
}

import { useEffect, useMemo, useState } from 'react'
import api from '@/lib/api'
import LoadingSpinner from '@/components/ui/LoadingSpinner'
import ErrorMessage from '@/components/ui/error-message'

interface OrgMeta {
  id: string
  name: string
  owner_id: string
  created_at: string
}

export default function OrgsPage() {
  const [orgs, setOrgs] = useState<OrgMeta[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [name, setName] = useState('')
  const [selectedOrg, setSelectedOrg] = useState<OrgMeta | null>(null)
  const [members, setMembers] = useState<string[]>([])
  const [addUserId, setAddUserId] = useState('')
  const [opBusy, setOpBusy] = useState(false)

  const canCreate = useMemo(() => name.trim().length >= 3 && name.trim().length <= 64, [name])

  const loadOrgs = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await api.get<{ organizations: OrgMeta[] }>('/api/v1/orgs')
      setOrgs(res.data.organizations || [])
    } catch (e: any) {
      setError(e?.response?.data?.detail || e?.message || 'Failed to load orgs')
    } finally {
      setLoading(false)
    }
  }

  const loadMembers = async (org: OrgMeta) => {
    setOpBusy(true)
    setError(null)
    try {
      const res = await api.get<{ members: string[] }>(`/api/v1/orgs/${org.id}/members`)
      setMembers(res.data.members || [])
    } catch (e: any) {
      setError(e?.response?.data?.detail || e?.message || 'Failed to load members')
    } finally {
      setOpBusy(false)
    }
  }

  useEffect(() => { loadOrgs() }, [])

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-2xl font-bold mb-4">Organisationen</h1>
      {loading && <LoadingSpinner />}
      {error && <ErrorMessage message={error} />}

      {/* Create Org */}
      <div className="card p-4 mb-6">
        <h2 className="font-semibold mb-2">Neue Organisation</h2>
        <div className="flex gap-2">
          <input
            className="input flex-1"
            placeholder="Name (3-64 Zeichen)"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
          <button
            className="btn-primary disabled:opacity-50"
            disabled={!canCreate || opBusy}
            onClick={async () => {
              setOpBusy(true)
              setError(null)
              try {
                await api.post('/api/v1/orgs', { name: name.trim() })
                setName('')
                await loadOrgs()
              } catch (e: any) {
                setError(e?.response?.data?.detail || e?.message || 'Fehler beim Erstellen')
              } finally {
                setOpBusy(false)
              }
            }}
          >
            Erstellen
          </button>
        </div>
      </div>

      {/* Orgs List */}
      <div className="card p-4">
        <h2 className="font-semibold mb-3">Meine Organisationen</h2>
        {orgs.length === 0 ? (
          <p className="text-sm text-muted-foreground">Keine Organisationen vorhanden.</p>
        ) : (
          <ul className="divide-y">
            {orgs.map((org) => (
              <li key={org.id} className="py-3 flex items-center justify-between gap-2">
                <div>
                  <div className="font-medium">{org.name}</div>
                  <div className="text-xs text-muted-foreground">ID: {org.id}</div>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    className="btn-secondary"
                    onClick={async () => { setSelectedOrg(org); await loadMembers(org) }}
                  >
                    Mitglieder
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Members Panel */}
      {selectedOrg && (
        <div className="card p-4 mt-6">
          <div className="flex items-center justify-between mb-2">
            <h2 className="font-semibold">Mitglieder – {selectedOrg.name}</h2>
            <button className="text-sm text-muted-foreground hover:underline" onClick={() => { setSelectedOrg(null); setMembers([]) }}>Schließen</button>
          </div>
          {opBusy ? (
            <LoadingSpinner />
          ) : (
            <>
              <ul className="mb-3 divide-y">
                {members.length === 0 ? (
                  <li className="py-2 text-sm text-muted-foreground">Keine Mitglieder</li>
                ) : members.map((m) => (
                  <li key={m} className="py-2 flex items-center justify-between">
                    <span className="text-sm">{m}</span>
                    <button
                      className="text-xs text-danger-700 hover:underline disabled:opacity-50"
                      disabled={opBusy}
                      onClick={async () => {
                        setOpBusy(true)
                        setError(null)
                        try {
                          await api.delete(`/api/v1/orgs/${selectedOrg.id}/members/${encodeURIComponent(m)}`)
                          await loadMembers(selectedOrg)
                        } catch (e: any) {
                          setError(e?.response?.data?.detail || e?.message || 'Fehler beim Entfernen')
                        } finally {
                          setOpBusy(false)
                        }
                      }}
                    >
                      Entfernen
                    </button>
                  </li>
                ))}
              </ul>
              <div className="flex gap-2">
                <input
                  className="input flex-1"
                  placeholder="User ID hinzufügen (nur Owner)"
                  value={addUserId}
                  onChange={(e) => setAddUserId(e.target.value)}
                />
                <button
                  className="btn-primary disabled:opacity-50"
                  disabled={!addUserId.trim() || opBusy}
                  onClick={async () => {
                    setOpBusy(true)
                    setError(null)
                    try {
                      await api.post(`/api/v1/orgs/${selectedOrg.id}/members`, { user_id: addUserId.trim() })
                      setAddUserId('')
                      await loadMembers(selectedOrg)
                    } catch (e: any) {
                      setError(e?.response?.data?.detail || e?.message || 'Fehler beim Hinzufügen')
                    } finally {
                      setOpBusy(false)
                    }
                  }}
                >
                  Hinzufügen
                </button>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  )
}

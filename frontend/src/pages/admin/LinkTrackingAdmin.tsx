/**
 * Link-Tracking Admin-Dashboard
 * Erstelle & Verwalte Social-Media-Tracking-Links
 * Mit Intelligence-Grade Analytics
 */

import { useState, useEffect } from 'react'
import { Link2, Plus, Eye, Copy, Download, TrendingUp, Globe, Users, Map } from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

interface TrackedLink {
  tracking_id: string
  short_url: string
  target_url: string
  source_platform: string
  source_username: string | null
  campaign: string | null
  click_count: number
  created_at: string
}

interface Analytics {
  stats: {
    total_clicks: number
    unique_countries: number
    unique_cities: number
  }
  geographic: {
    countries: Array<{ name: string; clicks: number }>
    cities: Array<{ name: string; clicks: number }>
  }
  social_media: {
    platforms: Array<{ name: string; clicks: number }>
    usernames_detected: string[]
  }
  devices: Record<string, number>
}

export default function LinkTrackingAdmin() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [links, setLinks] = useState<TrackedLink[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [selectedLink, setSelectedLink] = useState<string | null>(null)
  const [analytics, setAnalytics] = useState<Analytics | null>(null)

  // Form state
  const [targetUrl, setTargetUrl] = useState('')
  const [sourcePlatform, setSourcePlatform] = useState('twitter')
  const [sourceUsername, setSourceUsername] = useState('')
  const [campaign, setCampaign] = useState('')

  useEffect(() => {
    if (!user || user.role !== 'admin') {
      navigate('/dashboard')
      return
    }
    fetchLinks()
  }, [user])

  const fetchLinks = async () => {
    try {
      const token = localStorage.getItem('token')
      const res = await fetch(`${API_URL}/api/v1/links/admin/all`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      const data = await res.json()
      setLinks(data)
      setLoading(false)
    } catch (error) {
      console.error('Failed to fetch links:', error)
      setLoading(false)
    }
  }

  const createLink = async () => {
    try {
      const token = localStorage.getItem('token')
      const res = await fetch(`${API_URL}/api/v1/links/create`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          target_url: targetUrl,
          source_platform: sourcePlatform,
          source_username: sourceUsername || null,
          campaign: campaign || null
        })
      })

      if (res.ok) {
        const data = await res.json()
        toast.success('Link created! 🎉')
        setShowCreateModal(false)
        fetchLinks()
        
        // Copy to clipboard
        navigator.clipboard.writeText(data.short_url)
        toast.success('Short URL copied to clipboard!')
      } else {
        toast.error('Failed to create link')
      }
    } catch (error) {
      console.error('Failed to create link:', error)
      toast.error('Failed to create link')
    }
  }

  const viewAnalytics = async (trackingId: string) => {
    try {
      const token = localStorage.getItem('token')
      const res = await fetch(`${API_URL}/api/v1/links/${trackingId}/analytics`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      const data = await res.json()
      setAnalytics(data)
      setSelectedLink(trackingId)
    } catch (error) {
      console.error('Failed to fetch analytics:', error)
    }
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
    toast.success('Copied to clipboard!')
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6" role="main" aria-label="Link Tracking Dashboard">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Link Tracking</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Erstelle Social-Media-Links mit Intelligence-Grade Analytics
          </p>
        </div>
        
        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          aria-label="Create new tracking link"
        >
          <Plus className="h-5 w-5" />
          Neuer Link
        </button>
      </div>

      {/* Links Table */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700">
        <div className="overflow-x-auto">
          <table className="w-full" role="table" aria-label="Tracking links list">
            <thead>
              <tr className="border-b border-gray-200 dark:border-gray-700">
                <th className="text-left py-4 px-6 text-sm font-medium text-gray-700 dark:text-gray-300" scope="col">Short URL</th>
                <th className="text-left py-4 px-6 text-sm font-medium text-gray-700 dark:text-gray-300" scope="col">Platform</th>
                <th className="text-left py-4 px-6 text-sm font-medium text-gray-700 dark:text-gray-300" scope="col">Username</th>
                <th className="text-left py-4 px-6 text-sm font-medium text-gray-700 dark:text-gray-300" scope="col">Campaign</th>
                <th className="text-left py-4 px-6 text-sm font-medium text-gray-700 dark:text-gray-300" scope="col">Clicks</th>
                <th className="text-left py-4 px-6 text-sm font-medium text-gray-700 dark:text-gray-300" scope="col">Actions</th>
              </tr>
            </thead>
            <tbody>
              {links.map((link) => (
                <tr key={link.tracking_id} className="border-b border-gray-100 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700/50">
                  <td className="py-4 px-6">
                    <div className="flex items-center gap-2">
                      <code className="text-sm text-blue-600 dark:text-blue-400">{link.short_url}</code>
                      <button
                        onClick={() => copyToClipboard(link.short_url)}
                        className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                        aria-label={`Copy ${link.short_url} to clipboard`}
                      >
                        <Copy className="h-4 w-4" />
                      </button>
                    </div>
                  </td>
                  <td className="py-4 px-6">
                    <span className="px-2 py-1 bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 rounded text-sm">
                      {link.source_platform}
                    </span>
                  </td>
                  <td className="py-4 px-6 text-sm text-gray-700 dark:text-gray-300">
                    {link.source_username || '-'}
                  </td>
                  <td className="py-4 px-6 text-sm text-gray-700 dark:text-gray-300">
                    {link.campaign || '-'}
                  </td>
                  <td className="py-4 px-6">
                    <span className="text-lg font-bold text-gray-900 dark:text-white">{link.click_count}</span>
                  </td>
                  <td className="py-4 px-6">
                    <button
                      onClick={() => viewAnalytics(link.tracking_id)}
                      className="flex items-center gap-1 text-blue-600 hover:text-blue-700 dark:text-blue-400"
                      aria-label={`View analytics for ${link.short_url}`}
                    >
                      <Eye className="h-4 w-4" />
                      Analytics
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Analytics Panel */}
      {selectedLink && analytics && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6" role="region" aria-label="Link analytics">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-6">Analytics</h2>
          
          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4">
              <div className="flex items-center gap-3">
                <TrendingUp className="h-8 w-8 text-blue-600" />
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Total Clicks</p>
                  <p className="text-2xl font-bold text-gray-900 dark:text-white">{analytics.stats.total_clicks}</p>
                </div>
              </div>
            </div>
            
            <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-4">
              <div className="flex items-center gap-3">
                <Globe className="h-8 w-8 text-green-600" />
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Countries</p>
                  <p className="text-2xl font-bold text-gray-900 dark:text-white">{analytics.stats.unique_countries}</p>
                </div>
              </div>
            </div>
            
            <div className="bg-purple-50 dark:bg-purple-900/20 rounded-lg p-4">
              <div className="flex items-center gap-3">
                <Map className="h-8 w-8 text-purple-600" />
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Cities</p>
                  <p className="text-2xl font-bold text-gray-900 dark:text-white">{analytics.stats.unique_cities}</p>
                </div>
              </div>
            </div>
          </div>

          {/* Geographic Distribution */}
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">Top Countries</h3>
            <div className="space-y-2">
              {analytics.geographic.countries.slice(0, 5).map((country) => (
                <div key={country.name} className="flex items-center justify-between">
                  <span className="text-sm text-gray-700 dark:text-gray-300">{country.name}</span>
                  <div className="flex items-center gap-3">
                    <div className="w-32 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                      <div
                        className="bg-blue-600 h-2 rounded-full"
                        style={{ width: `${(country.clicks / analytics.stats.total_clicks) * 100}%` }}
                      />
                    </div>
                    <span className="text-sm font-bold text-gray-900 dark:text-white w-12 text-right">{country.clicks}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Social Media Platforms */}
          <div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">Detected Platforms</h3>
            <div className="flex flex-wrap gap-2">
              {analytics.social_media.platforms.map((platform) => (
                <div key={platform.name} className="px-3 py-1 bg-gray-100 dark:bg-gray-700 rounded-full">
                  <span className="text-sm text-gray-700 dark:text-gray-300">{platform.name}: {platform.clicks}</span>
                </div>
              ))}
            </div>
            
            {analytics.social_media.usernames_detected.length > 0 && (
              <div className="mt-3">
                <p className="text-sm text-gray-600 dark:text-gray-400">Detected Usernames:</p>
                <div className="flex flex-wrap gap-2 mt-2">
                  {analytics.social_media.usernames_detected.map((username) => (
                    <span key={username} className="px-2 py-1 bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 rounded text-sm">
                      @{username}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Create Link Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" role="dialog" aria-modal="true" aria-labelledby="create-link-title">
          <div className="bg-white dark:bg-gray-800 rounded-xl p-6 max-w-md w-full mx-4">
            <h2 id="create-link-title" className="text-2xl font-bold text-gray-900 dark:text-white mb-6">Neuer Tracking-Link</h2>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Target URL *
                </label>
                <input
                  type="url"
                  value={targetUrl}
                  onChange={(e) => setTargetUrl(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white"
                  placeholder="https://yoursite.com/pricing"
                  required
                  aria-required="true"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Platform *
                </label>
                <select
                  value={sourcePlatform}
                  onChange={(e) => setSourcePlatform(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white"
                  required
                  aria-required="true"
                >
                  <option value="twitter">Twitter/X</option>
                  <option value="linkedin">LinkedIn</option>
                  <option value="instagram">Instagram</option>
                  <option value="facebook">Facebook</option>
                  <option value="tiktok">TikTok</option>
                  <option value="reddit">Reddit</option>
                  <option value="youtube">YouTube</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Username (optional)
                </label>
                <input
                  type="text"
                  value={sourceUsername}
                  onChange={(e) => setSourceUsername(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white"
                  placeholder="john_doe"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Campaign (optional)
                </label>
                <input
                  type="text"
                  value={campaign}
                  onChange={(e) => setCampaign(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white"
                  placeholder="summer_2025"
                />
              </div>
            </div>
            
            <div className="flex gap-3 mt-6">
              <button
                onClick={() => setShowCreateModal(false)}
                className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700"
              >
                Cancel
              </button>
              <button
                onClick={createLink}
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                disabled={!targetUrl}
              >
                Create Link
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

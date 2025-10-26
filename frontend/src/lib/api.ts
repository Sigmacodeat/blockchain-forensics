import axios from 'axios'

const API_BASE: string | undefined = import.meta.env.VITE_API_URL
const baseURL = API_BASE || (typeof window !== 'undefined' ? window.location.origin : 'http://localhost:8000')

const api = axios.create({
  baseURL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    // Add org header if selected
    try {
      const orgId = localStorage.getItem('org_id')
      if (orgId) {
        // Prefer explicit Org header; backend bleibt abwärtskompatibel
        (config.headers as any)['X-Org-Id'] = orgId
      }
    } catch {}
    return config
  },
  (error) => Promise.reject(error)
)

// Note: Response/refresh handling lives in setupAuthInterceptors()

export { api }
export default api

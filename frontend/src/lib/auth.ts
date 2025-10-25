/**
 * Authentication Utilities & API Client
 */

import api from './api'
import { toast } from './toast'

export interface User {
  id: string
  email: string
  username: string
  role: UserRole
  plan?: 'community' | 'starter' | 'pro' | 'business' | 'plus' | 'enterprise'
  features?: string[]
  organization?: string
  created_at: string
  is_active: boolean
}

export enum UserRole {
  ADMIN = 'admin',
  ANALYST = 'analyst',
  AUDITOR = 'auditor',
  VIEWER = 'viewer',
  PARTNER = "PARTNER"
}

export interface LoginCredentials {
  email: string
  password: string
}

export interface RegisterData {
  email: string
  username: string
  password: string
  organization?: string
  organization_type?: string
  organization_name?: string
  wants_institutional_discount?: boolean
}

export interface AuthTokens {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface AuthResponse {
  user: User
  tokens: AuthTokens
}

// Storage Keys
const ACCESS_TOKEN_KEY = 'access_token'
const REFRESH_TOKEN_KEY = 'refresh_token'
const USER_KEY = 'user'

/**
 * Auth Service
 */
export const authService = {
  _refreshTimer: undefined as number | undefined,

  _clearRefreshTimer(): void {
    if (this._refreshTimer !== undefined) {
      window.clearTimeout(this._refreshTimer)
      this._refreshTimer = undefined
    }
  },

  _decodeJwt(token: string): { exp?: number } {
    try {
      const payload = token.split('.')[1]
      const b64 = payload.replace(/-/g, '+').replace(/_/g, '/')
      const json = atob(b64.padEnd(Math.ceil(b64.length / 4) * 4, '='))
      return JSON.parse(json)
    } catch {
      return {}
    }
  },

  _scheduleProactiveRefresh(): void {
    this._clearRefreshTimer()
    const token = this.getAccessToken()
    if (!token) return
    const { exp } = this._decodeJwt(token)
    if (!exp) return
    const nowSec = Math.floor(Date.now() / 1000)
    // Refresh 60s before expiry (minimum 10s)
    const secondsUntilRefresh = Math.max(exp - nowSec - 60, 10)
    this._refreshTimer = window.setTimeout(async () => {
      try {
        await this.refreshToken()
      } catch {
        // on failure, clear auth and redirect to login
        this.clearAuth()
        window.location.href = '/login'
      }
    }, secondsUntilRefresh * 1000)
  },

  initSession(): void {
    // Setup cross-tab sync for logout/login
    window.addEventListener('storage', (e) => {
      if (e.key === ACCESS_TOKEN_KEY || e.key === REFRESH_TOKEN_KEY || e.key === USER_KEY) {
        // If tokens removed in another tab -> redirect to login
        if (!localStorage.getItem(ACCESS_TOKEN_KEY)) {
          this._clearRefreshTimer()
          if (window.location.pathname !== '/login') {
            window.location.href = '/login'
          }
        }
      }
    })
    // Schedule proactive refresh if already authenticated
    if (this.isAuthenticated()) {
      this._scheduleProactiveRefresh()
    }
  },
  // Login
  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    const response = await api.post<AuthResponse>('/api/v1/auth/login', credentials)
    this.setTokens(response.data.tokens)
    this.setUser(response.data.user)
    this._scheduleProactiveRefresh()
    toast.success(`Willkommen zurück, ${response.data.user.username}!`)
    return response.data
  },

  // Register
  async register(data: RegisterData): Promise<AuthResponse> {
    const response = await api.post<AuthResponse>('/api/v1/auth/register', data)
    this.setTokens(response.data.tokens)
    this.setUser(response.data.user)
    this._scheduleProactiveRefresh()
    toast.success(`Account erstellt! Willkommen, ${response.data.user.username}!`)
    return response.data
  },

  // Logout
  async logout(): Promise<void> {
    try {
      await api.post('/api/v1/auth/logout')
      toast.info('Erfolgreich abgemeldet')
    } catch (error) {
      console.error('Logout error:', error)
    } finally {
      this.clearAuth()
      this._clearRefreshTimer()
    }
  },

  // Get current user
  async getCurrentUser(): Promise<User> {
    const response = await api.get<User>('/api/v1/auth/me')
    this.setUser(response.data)
    // Ensure timer is running when fetching user after reload
    if (this.isAuthenticated()) this._scheduleProactiveRefresh()
    return response.data
  },

  // Refresh token
  async refreshToken(): Promise<AuthTokens> {
    const refreshToken = this.getRefreshToken()
    if (!refreshToken) {
      throw new Error('No refresh token available')
    }

    const response = await api.post<AuthTokens>('/api/v1/auth/refresh', {
      refresh_token: refreshToken
    })
    
    this.setTokens(response.data)
    this._scheduleProactiveRefresh()
    return response.data
  },

  // Token Management
  setTokens(tokens: AuthTokens): void {
    localStorage.setItem(ACCESS_TOKEN_KEY, tokens.access_token)
    localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh_token)
  },

  getAccessToken(): string | null {
    return localStorage.getItem(ACCESS_TOKEN_KEY)
  },

  getRefreshToken(): string | null {
    return localStorage.getItem(REFRESH_TOKEN_KEY)
  },

  clearTokens(): void {
    localStorage.removeItem(ACCESS_TOKEN_KEY)
    localStorage.removeItem(REFRESH_TOKEN_KEY)
  },

  // User Management
  setUser(user: User): void {
    // Fallback: Nutzer ohne Plan werden als 'community' behandelt
    const normalized: User = {
      ...user,
      plan: (user.plan ?? 'community') as User['plan'],
    }
    localStorage.setItem(USER_KEY, JSON.stringify(normalized))
  },

  getUser(): User | null {
    const userStr = localStorage.getItem(USER_KEY)
    return userStr ? JSON.parse(userStr) : null
  },

  clearUser(): void {
    localStorage.removeItem(USER_KEY)
  },

  clearAuth(): void {
    this.clearTokens()
    this.clearUser()
  },

  // Check if authenticated
  isAuthenticated(): boolean {
    return !!this.getAccessToken()
  },

  // Check user role
  hasRole(role: UserRole): boolean {
    const user = this.getUser()
    return user?.role === role
  },

  hasAnyRole(roles: UserRole[]): boolean {
    const user = this.getUser()
    return user ? roles.includes(user.role) : false
  },

  // Permission checks
  canAccessAdmin(): boolean {
    return this.hasRole(UserRole.ADMIN)
  },

  canCreateTrace(): boolean {
    return this.hasAnyRole([UserRole.ADMIN, UserRole.ANALYST])
  },

  canViewReports(): boolean {
    return this.hasAnyRole([UserRole.ADMIN, UserRole.ANALYST, UserRole.AUDITOR])
  },

  canExportData(): boolean {
    return this.hasAnyRole([UserRole.ADMIN, UserRole.ANALYST, UserRole.AUDITOR])
  }
}

/**
 * Setup axios interceptors for auth
 */
export function setupAuthInterceptors() {
  // Request interceptor - add token to headers
  api.interceptors.request.use(
    (config) => {
      const token = authService.getAccessToken()
      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      }
      return config
    },
    (error) => Promise.reject(error)
  )

  // Response interceptor - handle 401 and refresh token
  api.interceptors.response.use(
    (response) => response,
    async (error) => {
      const originalRequest = error.config

      // If 401 and not already retried
      if (error.response?.status === 401 && !originalRequest._retry) {
        originalRequest._retry = true

        try {
          // Try to refresh token
          const tokens = await authService.refreshToken()
          
          // Retry original request with new token
          originalRequest.headers.Authorization = `Bearer ${tokens.access_token}`
          return api(originalRequest)
        } catch (refreshError) {
          // Refresh failed, logout user
          authService.clearAuth()
          window.location.href = '/login'
          return Promise.reject(refreshError)
        }
      }

      return Promise.reject(error)
    }
  )
}

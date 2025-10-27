import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { CheckCircle, AlertCircle, Loader2, Gift, Sparkles } from 'lucide-react'
import api from '@/lib/api'
import { analyticsTracker } from '@/services/analytics-tracker'

// API-Aufrufe laufen über die zentrale api-Instanz

// Tier-Preise für Revenue-Tracking
const TIER_PRICES = {
  chatbot: { 1: 59, 2: 119, 3: 199 },
  firewall: { 1: 79, 2: 149, 3: 249 },
  inspector: { 1: 69, 2: 139, 3: 229 },
  commander: { 1: 49, 2: 99, 3: 179 }
} as const

// Product-Info-Mapping (aus AppSumo-Strategie)
const PRODUCT_INFO = {
  chatbot: {
    name: 'AI ChatBot Pro',
    icon: '💬',
    color: 'purple',
    gradient: 'from-purple-600 to-blue-600',
    description: 'Voice-enabled AI chatbot with crypto payments'
  },
  firewall: {
    name: 'Web3 Wallet Guardian',
    icon: '🛡️',
    color: 'green',
    gradient: 'from-green-600 to-emerald-600',
    description: '15 ML-models for real-time scam detection'
  },
  inspector: {
    name: 'Crypto Transaction Inspector',
    icon: '🔍',
    color: 'blue',
    gradient: 'from-blue-600 to-cyan-600',
    description: 'Wallet scanner with risk scoring'
  },
  commander: {
    name: 'AI Dashboard Commander',
    icon: '🎯',
    color: 'orange',
    gradient: 'from-orange-600 to-amber-600',
    description: 'Natural language control for dashboards'
  }
} as const

type Step = 'code' | 'account' | 'success'

export default function AppSumoRedemption() {
  const navigate = useNavigate()
  const [step, setStep] = useState<Step>('code')
  const [code, setCode] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [firstName, setFirstName] = useState('')
  const [lastName, setLastName] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [codeInfo, setCodeInfo] = useState<any>(null)

  // Track Landing mit UTM-Parametern
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search)
    const utm_source = urlParams.get('utm_source')
    const utm_campaign = urlParams.get('utm_campaign')
    const utm_medium = urlParams.get('utm_medium')
    const utm_term = urlParams.get('utm_term')
    const utm_content = urlParams.get('utm_content')
    
    analyticsTracker.trackEvent('appsumo_landing', {
      utm_source,
      utm_campaign,
      utm_medium,
      utm_term,
      utm_content,
      referrer: document.referrer,
      page: 'redemption',
      timestamp: new Date().toISOString()
    })
  }, [])

  // Step 1: Validate Code
  const handleValidateCode = async () => {
    setLoading(true)
    setError(null)
    // Format-Validierung vor API-Aufruf
    const CODE_MIN_LEN = 10
    const isFormatOk = code && code.length >= CODE_MIN_LEN && code.includes('-')
    if (!isFormatOk) {
      setError('Invalid code')
      setLoading(false)
      return
    }
    
    // Track: Code-Eingabe gestartet
    analyticsTracker.trackEvent('appsumo_code_validation_started', {
      code_length: code.length,
      timestamp: new Date().toISOString()
    })
    
    try {
      const res = await api.post('/api/v1/appsumo/validate-code', null, { params: { code: code.toUpperCase() } })
      setCodeInfo(res.data)
      setStep('account')
      
      // Track: Code erfolgreich validiert
      analyticsTracker.trackEvent('appsumo_code_validated', {
        product: res.data.product,
        tier: res.data.tier,
        code_prefix: code.substring(0, 4),
        features_count: Object.keys(res.data.features || {}).length,
        timestamp: new Date().toISOString()
      })
      
      // Track: Funnel-Step
      analyticsTracker.trackEvent('funnel_step_3_code_valid', {
        product: res.data.product,
        tier: res.data.tier
      })
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Invalid code')
      
      // Track: Validation fehlgeschlagen
      analyticsTracker.trackEvent('appsumo_code_validation_failed', {
        code_prefix: code.substring(0, 4),
        error: err.response?.data?.detail || 'Invalid code',
        timestamp: new Date().toISOString()
      })
    } finally {
      setLoading(false)
    }
  }

  // Step 2: Redeem Code + Create Account
  const handleRedeem = async () => {
    setLoading(true)
    setError(null)
    
    const product = codeInfo?.product
    const tier = codeInfo?.tier
    const revenue = product && tier ? TIER_PRICES[product as keyof typeof TIER_PRICES]?.[tier as 1 | 2 | 3] : 0
    
    // Track: Redemption gestartet
    analyticsTracker.trackEvent('appsumo_redemption_started', {
      product,
      tier,
      revenue_usd: revenue,
      has_name: !!(firstName && lastName),
      timestamp: new Date().toISOString()
    })
    
    // Track: Funnel-Step
    analyticsTracker.trackEvent('funnel_step_5_submit', {
      product,
      tier
    })
    
    try {
      const res = await api.post('/api/v1/appsumo/redeem', {
        code: code.toUpperCase(),
        email,
        password,
        first_name: firstName,
        last_name: lastName
      })
      
      // Store JWT token
      if (res.data.access_token) {
        localStorage.setItem('token', res.data.access_token)
      }
      
      // Set User-ID für zukünftiges Tracking
      if (res.data.user?.id) {
        analyticsTracker.setUserId(res.data.user.id)
      }
      
      setStep('success')
      
      // Track: Erfolgreiches Redemption (KRITISCH für Revenue!)
      analyticsTracker.trackEvent('appsumo_code_redeemed', {
        product: res.data.product,
        tier: res.data.tier,
        revenue_usd: revenue,
        user_id: res.data.user?.id,
        email: res.data.user?.email,
        source: 'appsumo',
        timestamp: new Date().toISOString()
      })
      
      // Track: Revenue-Event (für separate Revenue-Analytics)
      analyticsTracker.trackEvent('revenue', {
        value: revenue,
        currency: 'USD',
        product: res.data.product,
        tier: res.data.tier,
        source: 'appsumo',
        transaction_id: code.toUpperCase(),
        user_id: res.data.user?.id,
        timestamp: new Date().toISOString()
      })
      
      // Track: User-Erstellung
      analyticsTracker.trackEvent('user_created', {
        user_id: res.data.user?.id,
        email: res.data.user?.email,
        source: 'appsumo',
        product: res.data.product,
        tier: res.data.tier,
        timestamp: new Date().toISOString()
      })
      
      // Track: Funnel-Completion
      analyticsTracker.trackEvent('funnel_step_6_success', {
        product: res.data.product,
        tier: res.data.tier,
        revenue_usd: revenue
      })
      
      // Redirect nach 2 Sekunden
      setTimeout(() => {
        navigate('/dashboard')
      }, 2000)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Redemption failed')
      
      // Track: Redemption fehlgeschlagen
      analyticsTracker.trackEvent('appsumo_redemption_failed', {
        product,
        tier,
        error: err.response?.data?.detail || 'Redemption failed',
        timestamp: new Date().toISOString()
      })
    } finally {
      setLoading(false)
    }
  }

  const currentProduct = codeInfo?.product ? PRODUCT_INFO[codeInfo.product as keyof typeof PRODUCT_INFO] : null

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="max-w-md w-full"
      >
        {/* Header */}
        <div className="text-center mb-8">
          <Gift className="w-16 h-16 mx-auto mb-4 text-purple-400" />
          <h1 className="text-3xl font-bold text-white mb-2">
            Redeem Your AppSumo Deal
          </h1>
          <p className="text-slate-300">
            Activate your lifetime access in 2 easy steps
          </p>
        </div>

        {/* Card */}
        <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-8 border border-white/20">
          {error && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="mb-6 p-4 bg-red-500/20 border border-red-500 rounded-lg flex items-start gap-3"
            >
              <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
              <p className="text-red-200 text-sm">{error}</p>
            </motion.div>
          )}

          {/* Step 1: Code Input */}
          {step === 'code' && (
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-slate-200 mb-2">
                  AppSumo Code
                </label>
                <input
                  type="text"
                  value={code}
                  onChange={(e) => setCode(e.target.value.toUpperCase())}
                  placeholder="CHAT-ABC123-XYZ789"
                  className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500 font-mono"
                  disabled={loading}
                  maxLength={18}
                />
                <p className="mt-2 text-xs text-slate-400">
                  Find your code in your AppSumo purchase confirmation email
                </p>
              </div>

              <button
                onClick={handleValidateCode}
                disabled={loading || !code}
                className="w-full py-3 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg font-medium hover:from-purple-700 hover:to-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 transition-all"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Validating...
                  </>
                ) : (
                  <>
                    <Sparkles className="w-5 h-5" />
                    Validate Code
                  </>
                )}
              </button>
            </div>
          )}

          {/* Step 2: Account Creation */}
          {step === 'account' && codeInfo && currentProduct && (
            <div className="space-y-6">
              {/* Product Info */}
              <div className={`p-4 bg-gradient-to-r ${currentProduct.gradient} bg-opacity-20 rounded-lg border border-white/10`}>
                <div className="flex items-center gap-3 mb-2">
                  <span className="text-4xl">{currentProduct.icon}</span>
                  <div>
                    <h3 className="font-semibold text-white text-lg">
                      {currentProduct.name}
                    </h3>
                    <p className="text-sm text-slate-200">
                      Tier {codeInfo.tier} - Lifetime Access
                    </p>
                  </div>
                </div>
                <p className="text-sm text-slate-300 mt-2">
                  {currentProduct.description}
                </p>
              </div>

              {/* Account Form */}
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label htmlFor="first-name" className="block text-sm font-medium text-slate-200 mb-2">
                      First Name
                    </label>
                    <input
                      id="first-name"
                      type="text"
                      value={firstName}
                      onChange={(e) => setFirstName(e.target.value)}
                      className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                      placeholder="John"
                    />
                  </div>
                  <div>
                    <label htmlFor="last-name" className="block text-sm font-medium text-slate-200 mb-2">
                      Last Name
                    </label>
                    <input
                      id="last-name"
                      type="text"
                      value={lastName}
                      onChange={(e) => setLastName(e.target.value)}
                      className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                      placeholder="Doe"
                    />
                  </div>
                </div>

                <div>
                  <label htmlFor="email" className="block text-sm font-medium text-slate-200 mb-2">
                    Email
                  </label>
                  <input
                    id="email"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                    placeholder="john@example.com"
                  />
                </div>

                <div>
                  <label htmlFor="password" className="block text-sm font-medium text-slate-200 mb-2">
                    Password
                  </label>
                  <input
                    id="password"
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                    placeholder="••••••••"
                  />
                  <p className="mt-1 text-xs text-slate-400">
                    Minimum 8 characters
                  </p>
                </div>
              </div>

              <button
                onClick={handleRedeem}
                disabled={loading || !email || !password || password.length < 8}
                aria-label="Create Account"
                className={`w-full py-3 bg-gradient-to-r ${currentProduct.gradient} text-white rounded-lg font-medium hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 transition-all`}
              >
                {loading ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Creating Account...
                  </>
                ) : (
                  <>
                    Activate My Lifetime Deal
                    <span className="sr-only">Create Account</span>
                  </>
                )}
              </button>

              <button
                onClick={() => setStep('code')}
                disabled={loading}
                className="w-full py-2 text-slate-300 hover:text-white text-sm transition-colors"
              >
                ← Back to code
              </button>
            </div>
          )}

          {/* Step 3: Success */}
          {step === 'success' && (
            <div className="text-center space-y-6">
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ type: 'spring', duration: 0.5 }}
              >
                <CheckCircle className="w-20 h-20 mx-auto text-green-400" />
              </motion.div>

              <div>
                <h2 className="text-2xl font-bold text-white mb-2">
                  Welcome Aboard! 🎉
                </h2>
                <p className="text-slate-300">
                  Your account has been activated successfully.
                </p>
              </div>

              <div className="p-4 bg-white/5 rounded-lg border border-white/10">
                <p className="text-sm text-slate-300">
                  Redirecting to your dashboard...
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <p className="text-center text-sm text-slate-400 mt-6">
          Need help?{' '}
          <a href="/support" className="text-purple-400 hover:underline">
            Contact Support
          </a>
        </p>
      </motion.div>
    </div>
  )
}

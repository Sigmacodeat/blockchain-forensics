import React from 'react'
import { Button } from '@/components/ui/button'
import { Loader2 } from 'lucide-react'
import i18n from '@/i18n/config-optimized'

interface GoogleLoginButtonProps {
  className?: string
  text?: string
  disabled?: boolean
}

export default function GoogleLoginButton({ className, text = 'Mit Google anmelden', disabled }: GoogleLoginButtonProps) {
  const [redirecting, setRedirecting] = React.useState(false)

  const handleGoogleLogin = () => {
    if (redirecting || disabled) return
    setRedirecting(true)
    const base = import.meta.env.VITE_API_URL || 'http://localhost:8000'
    const lang = i18n.language || 'en'
    const redirectUri = `${window.location.origin}/${lang}/login`
    const url = `${base}/api/v1/auth/oauth/google?redirect_uri=${encodeURIComponent(redirectUri)}`
    window.location.href = url
  }

  return (
    <Button
      type="button"
      variant="outline"
      className={className}
      aria-busy={redirecting}
      disabled={redirecting || !!disabled}
      onClick={handleGoogleLogin}
    >
      {redirecting ? (
        <>
          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          Weiter zu Google…
        </>
      ) : (
        <>
          <span className="mr-2 inline-block" aria-hidden>
            <svg width="18" height="18" viewBox="0 0 533.5 544.3" xmlns="http://www.w3.org/2000/svg">
              <path d="M533.5 278.4c0-18.6-1.7-36.4-4.9-53.6H272.1v101.4h146.9c-6.3 34.2-25 63.1-53.3 82.5v68h86.2c50.5-46.5 81.6-115.1 81.6-198.3z" fill="#4285F4"/>
              <path d="M272.1 544.3c73.8 0 135.6-24.4 180.8-66.1l-86.2-68c-24 16.1-54.7 25.7-94.6 25.7-72.8 0-134.5-49.2-156.6-115.4H26.6v72.5c45 89.2 137.6 151.3 245.5 151.3z" fill="#34A853"/>
              <path d="M115.5 320.5c-10.7-31.9-10.7-66.3 0-98.2V149.8H26.6c-43.5 86.9-43.5 189.6 0 276.5l88.9-66z" fill="#FBBC05"/>
              <path d="M272.1 107.7c39.9 0 75.7 13.7 103.9 40.6l78.1-78.1C407.6 26.7 345.8 0 272.1 0 164.2 0 71.6 62.2 26.6 151.4l88.9 72.5c22.1-66.1 83.8-116.2 156.6-116.2z" fill="#EA4335"/>
            </svg>
          </span>
          {text}
        </>
      )}
    </Button>
  )
}

import React, { createContext, useContext, useMemo } from 'react'

export type FeatureFlags = {
  AGENT: boolean
  INVESTIGATOR: boolean
  CORRELATION: boolean
  COVERAGE: boolean
  WALLET_TEST: boolean
  TOURS: boolean
  ADDRESS_ANALYSIS: boolean
}

const defaultFlags: FeatureFlags = {
  AGENT: false,
  INVESTIGATOR: false,
  CORRELATION: false,
  COVERAGE: false,
  WALLET_TEST: false,
  TOURS: false,
  ADDRESS_ANALYSIS: false,
}

const FeatureFlagsContext = createContext<FeatureFlags>(defaultFlags)

export function FeatureFlagsProvider({ children }: { children: React.ReactNode }) {
  const flags = useMemo<FeatureFlags>(() => ({
    AGENT: String(import.meta.env.VITE_FEATURE_AGENT || '').toLowerCase() === 'true',
    INVESTIGATOR: String(import.meta.env.VITE_FEATURE_INVESTIGATOR || '').toLowerCase() === 'true',
    CORRELATION: String(import.meta.env.VITE_FEATURE_CORRELATION || '').toLowerCase() === 'true',
    COVERAGE: String(import.meta.env.VITE_FEATURE_COVERAGE || '').toLowerCase() === 'true',
    WALLET_TEST: String(import.meta.env.VITE_FEATURE_WALLET_TEST || '').toLowerCase() === 'true',
    TOURS: String(import.meta.env.VITE_FEATURE_TOURS || '').toLowerCase() === 'true',
    ADDRESS_ANALYSIS: String(import.meta.env.VITE_FEATURE_ADDRESS_ANALYSIS || '').toLowerCase() === 'true',
  }), [])

  return (
    <FeatureFlagsContext.Provider value={flags}>{children}</FeatureFlagsContext.Provider>
  )
}

export function useFeatures() {
  return useContext(FeatureFlagsContext)
}

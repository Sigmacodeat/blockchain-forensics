import React from 'react'
import { useFeatures } from '@/contexts/FeatureFlagsContext'
import ComingSoon, { ComingSoonProps } from './ComingSoon'

export interface FeatureGateProps extends Partial<ComingSoonProps> {
  feature: keyof import('@/contexts/FeatureFlagsContext').FeatureFlags
  children: React.ReactNode
  // Wenn true, rendert gar nichts statt ComingSoon
  hideIfDisabled?: boolean
}

export default function FeatureGate({ feature, children, hideIfDisabled = false, ...props }: FeatureGateProps) {
  const flags = useFeatures()
  const enabled = !!flags[feature]

  if (enabled) return <>{children}</>
  if (hideIfDisabled) return null
  return <ComingSoon {...props} />
}

import { useState, useEffect, useCallback } from 'react'
import { Achievement, ACHIEVEMENTS } from '@/lib/achievements'
import { useToast } from '@/contexts/ToastContext'

interface UserProgress {
  traces: number
  cases: number
  alerts: number
  maxHops: number
  chains: Set<string>
  mixersFound: number
  sanctionsHits: number
  exchangeLinks: number
  casesShared: number
  intelShared: number
  reportsExported: number
  unlockedAchievements: string[]
  totalPoints: number
}

const STORAGE_KEY = 'blockchain-forensics-achievements'

export const useAchievements = () => {
  const { showToast } = useToast()
  
  const [progress, setProgress] = useState<UserProgress>(() => {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved) {
      try {
        const parsed = JSON.parse(saved)
        return {
          ...parsed,
          chains: new Set(parsed.chains || [])
        }
      } catch (e) {
        console.error('Failed to parse achievements:', e)
      }
    }
    
    return {
      traces: 0,
      cases: 0,
      alerts: 0,
      maxHops: 0,
      chains: new Set<string>(),
      mixersFound: 0,
      sanctionsHits: 0,
      exchangeLinks: 0,
      casesShared: 0,
      intelShared: 0,
      reportsExported: 0,
      unlockedAchievements: [],
      totalPoints: 0,
    }
  })

  // Save to localStorage whenever progress changes
  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({
      ...progress,
      chains: Array.from(progress.chains)
    }))
  }, [progress])

  const checkAchievements = useCallback((newProgress: UserProgress) => {
    const newlyUnlocked: Achievement[] = []

    ACHIEVEMENTS.forEach(achievement => {
      // Skip if already unlocked
      if (newProgress.unlockedAchievements.includes(achievement.id)) {
        return
      }

      let shouldUnlock = false

      switch (achievement.id) {
        case 'first_trace':
          shouldUnlock = newProgress.traces >= 1
          break
        case 'trace_master':
          shouldUnlock = newProgress.traces >= 10
          break
        case 'trace_legend':
          shouldUnlock = newProgress.traces >= 100
          break
        case 'deep_dive':
          shouldUnlock = newProgress.maxHops >= 10
          break
        case 'first_case':
          shouldUnlock = newProgress.cases >= 1
          break
        case 'case_detective':
          shouldUnlock = newProgress.cases >= 10
          break
        case 'case_closed':
          shouldUnlock = newProgress.reportsExported >= 1
          break
        case 'first_alert':
          shouldUnlock = newProgress.alerts >= 1
          break
        case 'alert_handler':
          shouldUnlock = newProgress.alerts >= 50
          break
        case 'mixer_hunter':
          shouldUnlock = newProgress.mixersFound >= 1
          break
        case 'sanctions_hit':
          shouldUnlock = newProgress.sanctionsHits >= 1
          break
        case 'exchange_link':
          shouldUnlock = newProgress.exchangeLinks >= 1
          break
        case 'cross_chain':
          shouldUnlock = newProgress.chains.size >= 3
          break
        case 'team_player':
          shouldUnlock = newProgress.casesShared >= 1
          break
        case 'intel_contributor':
          shouldUnlock = newProgress.intelShared >= 1
          break
        case 'legendary_analyst':
          shouldUnlock = newProgress.totalPoints >= 1000
          break
      }

      if (shouldUnlock) {
        newlyUnlocked.push(achievement)
      }
    })

    // Show toasts for newly unlocked achievements
    newlyUnlocked.forEach(achievement => {
      setTimeout(() => {
        showToast({
          type: 'success',
          title: `🎉 Achievement Unlocked!`,
          message: `${achievement.icon} ${achievement.title} (+${achievement.points} Punkte)`,
          duration: 8000,
        })
      }, 300)
    })

    return newlyUnlocked
  }, [showToast])

  const updateProgress = useCallback((updates: Partial<Omit<UserProgress, 'unlockedAchievements' | 'totalPoints' | 'chains'>>, chainId?: string) => {
    setProgress(prev => {
      const newChains = chainId ? new Set([...prev.chains, chainId]) : prev.chains
      
      const newProgress = {
        ...prev,
        ...updates,
        chains: newChains,
      }

      // Check for new achievements
      const newlyUnlocked = checkAchievements(newProgress)
      
      if (newlyUnlocked.length > 0) {
        const newPoints = newlyUnlocked.reduce((sum, ach) => sum + ach.points, 0)
        return {
          ...newProgress,
          unlockedAchievements: [
            ...newProgress.unlockedAchievements,
            ...newlyUnlocked.map(a => a.id)
          ],
          totalPoints: newProgress.totalPoints + newPoints,
        }
      }

      return newProgress
    })
  }, [checkAchievements])

  // Helper functions for common actions
  const recordTrace = useCallback((hops: number, chain: string) => {
    updateProgress({
      traces: progress.traces + 1,
      maxHops: Math.max(progress.maxHops, hops),
    }, chain)
  }, [progress, updateProgress])

  const recordCase = useCallback(() => {
    updateProgress({ cases: progress.cases + 1 })
  }, [progress, updateProgress])

  const recordAlert = useCallback(() => {
    updateProgress({ alerts: progress.alerts + 1 })
  }, [progress, updateProgress])

  const recordMixer = useCallback(() => {
    updateProgress({ mixersFound: progress.mixersFound + 1 })
  }, [progress, updateProgress])

  const recordSanction = useCallback(() => {
    updateProgress({ sanctionsHits: progress.sanctionsHits + 1 })
  }, [progress, updateProgress])

  const recordExchangeLink = useCallback(() => {
    updateProgress({ exchangeLinks: progress.exchangeLinks + 1 })
  }, [progress, updateProgress])

  const recordCaseShared = useCallback(() => {
    updateProgress({ casesShared: progress.casesShared + 1 })
  }, [progress, updateProgress])

  const recordIntelShared = useCallback(() => {
    updateProgress({ intelShared: progress.intelShared + 1 })
  }, [progress, updateProgress])

  const recordReportExported = useCallback(() => {
    updateProgress({ reportsExported: progress.reportsExported + 1 })
  }, [progress, updateProgress])

  const getUnlockedAchievements = useCallback(() => {
    return ACHIEVEMENTS.filter(ach => progress.unlockedAchievements.includes(ach.id))
  }, [progress])

  const getLockedAchievements = useCallback(() => {
    return ACHIEVEMENTS.filter(ach => !progress.unlockedAchievements.includes(ach.id))
  }, [progress])

  const getProgressForAchievement = useCallback((achievementId: string) => {
    switch (achievementId) {
      case 'first_trace':
      case 'trace_master':
      case 'trace_legend':
        return { current: progress.traces, required: ACHIEVEMENTS.find(a => a.id === achievementId)?.requirement || 0 }
      case 'first_case':
      case 'case_detective':
        return { current: progress.cases, required: ACHIEVEMENTS.find(a => a.id === achievementId)?.requirement || 0 }
      case 'alert_handler':
        return { current: progress.alerts, required: 50 }
      case 'cross_chain':
        return { current: progress.chains.size, required: 3 }
      default:
        return { current: 0, required: 1 }
    }
  }, [progress])

  return {
    progress,
    recordTrace,
    recordCase,
    recordAlert,
    recordMixer,
    recordSanction,
    recordExchangeLink,
    recordCaseShared,
    recordIntelShared,
    recordReportExported,
    getUnlockedAchievements,
    getLockedAchievements,
    getProgressForAchievement,
  }
}

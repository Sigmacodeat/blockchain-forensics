import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { useAuth } from './AuthContext';
import type { PlanId } from '@/lib/features';

interface OnboardingContextType {
  /** Ob die Tour gerade läuft */
  isRunning: boolean;
  /** Startet die Onboarding-Tour */
  startTour: () => void;
  /** Stoppt die Onboarding-Tour */
  stopTour: () => void;
  /** Ob der User die Tour für diesen Plan schon gesehen hat */
  hasSeenTour: boolean;
  /** Markiert die Tour als gesehen */
  markTourAsSeen: () => void;
  /** Reset die Tour (für Testing/Admin) */
  resetTour: () => void;
  /** Aktuelle Tour ID (plan-basiert) */
  currentTourId: string;
}

const OnboardingContext = createContext<OnboardingContextType | undefined>(undefined);

interface OnboardingProviderProps {
  children: React.ReactNode;
}

export function OnboardingProvider({ children }: OnboardingProviderProps) {
  const { user } = useAuth();
  const [isRunning, setIsRunning] = useState(false);
  const [hasSeenTour, setHasSeenTour] = useState(false);
  
  // Generiere Tour ID basierend auf User-Plan
  const currentTourId = `onboarding-${user?.plan || 'community'}-v1`;
  
  // Lade Tour-Status aus localStorage
  useEffect(() => {
    if (user) {
      const storageKey = `${currentTourId}-${user.id}`;
      const seen = localStorage.getItem(storageKey) === 'true';
      setHasSeenTour(seen);
    }
  }, [user, currentTourId]);
  
  const startTour = useCallback(() => {
    setIsRunning(true);
  }, []);
  
  const stopTour = useCallback(() => {
    setIsRunning(false);
  }, []);
  
  const markTourAsSeen = useCallback(() => {
    if (user) {
      const storageKey = `${currentTourId}-${user.id}`;
      localStorage.setItem(storageKey, 'true');
      setHasSeenTour(true);
      setIsRunning(false);
    }
  }, [user, currentTourId]);
  
  const resetTour = useCallback(() => {
    if (user) {
      const storageKey = `${currentTourId}-${user.id}`;
      localStorage.removeItem(storageKey);
      setHasSeenTour(false);
    }
  }, [user, currentTourId]);
  
  return (
    <OnboardingContext.Provider
      value={{
        isRunning,
        startTour,
        stopTour,
        hasSeenTour,
        markTourAsSeen,
        resetTour,
        currentTourId,
      }}
    >
      {children}
    </OnboardingContext.Provider>
  );
}

export function useOnboarding() {
  const context = useContext(OnboardingContext);
  if (context === undefined) {
    throw new Error('useOnboarding must be used within an OnboardingProvider');
  }
  return context;
}

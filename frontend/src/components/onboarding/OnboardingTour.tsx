import React, { useEffect, useState, useCallback } from 'react';
import Joyride, { CallBackProps, STATUS, EVENTS, ACTIONS } from 'react-joyride';
import { useOnboarding } from '@/contexts/OnboardingContext';
import { useAuth } from '@/contexts/AuthContext';
import { getTourStepsForPlan, tourStyles } from '@/config/onboarding-tours';
import { useTranslation } from 'react-i18next';
import { useToast } from '@/contexts/ToastContext';
import { useAchievements } from '@/hooks/useAchievements';
import TourCompletionCelebration from './TourCompletionCelebration';
import { Sparkles } from 'lucide-react';
import { trackTourStart, trackTourComplete, trackTourSkip, trackStepView } from '@/lib/onboarding-analytics';
import type { PlanId } from '@/lib/features';

interface OnboardingTourProps {
  /** Ob die Tour automatisch beim ersten Besuch starten soll */
  autoStart?: boolean;
  /** Verzögerung in ms vor dem automatischen Start */
  autoStartDelay?: number;
}

export function OnboardingTour({ autoStart = true, autoStartDelay = 1000 }: OnboardingTourProps) {
  const { t } = useTranslation();
  const { user } = useAuth();
  const { showToast } = useToast();
  const { recordTrace } = useAchievements();
  const [showCelebration, setShowCelebration] = useState(false);
  const {
    isRunning,
    startTour,
    stopTour,
    hasSeenTour,
    markTourAsSeen,
  } = useOnboarding();

  // Hole die passenden Steps für den User-Plan
  const steps = getTourStepsForPlan(user?.plan as any);

  // Auto-Start beim ersten Besuch
  useEffect(() => {
    if (autoStart && !hasSeenTour && user && !isRunning) {
      const timer = setTimeout(() => {
        startTour();
        // Track tour start
        trackTourStart(
          `onboarding-${user.plan || 'community'}-v1`,
          (user.plan || 'community') as PlanId,
          user.id
        );
      }, autoStartDelay);

      return () => clearTimeout(timer);
    }
  }, [autoStart, autoStartDelay, hasSeenTour, user, isRunning, startTour]);

  // Callback Handler für Tour-Events
  const handleJoyrideCallback = useCallback((data: CallBackProps) => {
    const { status, type, action, index, lifecycle } = data;

    if (!user) return;

    const tourId = `onboarding-${user.plan || 'community'}-v1`;
    const plan = (user.plan || 'community') as PlanId;

    // Track step views
    if (type === EVENTS.STEP_AFTER && lifecycle === 'complete') {
      trackStepView(tourId, plan, index + 1, steps.length, user.id);
    }

    // Tour wurde erfolgreich abgeschlossen
    if (status === STATUS.FINISHED) {
      markTourAsSeen();
      // Track completion
      trackTourComplete(tourId, plan, user.id, steps.length);
      // Zeige Celebration-Modal
      setShowCelebration(true);
      // Track Achievement (wird automatisch durch useAchievements behandelt)
    }

    // Tour wurde übersprungen
    if (status === STATUS.SKIPPED) {
      markTourAsSeen();
      // Track skip with current step
      trackTourSkip(tourId, plan, user.id, index, steps.length);
      showToast({
        type: 'info',
        title: 'Tour übersprungen',
        message: 'Du kannst die Tour jederzeit später starten',
      });
    }

    // User hat die Tour abgebrochen
    if (action === ACTIONS.CLOSE) {
      stopTour();
      // Track as skip
      trackTourSkip(tourId, plan, user.id, index, steps.length);
    }

    // Logging für Debug (optional)
    if (process.env.NODE_ENV === 'development') {
      console.log('[OnboardingTour]', { status, type, action, index });
    }
  }, [user, steps.length, markTourAsSeen, setShowCelebration, showToast, stopTour]);

  // Lokalisierte Labels
  const locale = {
    back: t('onboarding.back', 'Zurück'),
    close: t('onboarding.close', 'Schließen'),
    last: t('onboarding.finish', 'Fertig'),
    next: t('onboarding.next', 'Weiter'),
    open: t('onboarding.open', 'Dialog öffnen'),
    skip: t('onboarding.skip', 'Tour überspringen'),
  };

  if (!user || steps.length === 0) {
    return null;
  }

  return (
    <>
      <Joyride
        steps={steps}
        run={isRunning}
        continuous
        showProgress
        showSkipButton
        scrollToFirstStep
        disableScrolling={false}
        callback={handleJoyrideCallback}
        styles={tourStyles}
        locale={locale}
        floaterProps={{
          disableAnimation: false,
          styles: {
            arrow: {
              length: 8,
              spread: 16,
            },
          },
        }}
      />

      {/* Tour Completion Celebration */}
      {showCelebration && (
        <TourCompletionCelebration onClose={() => setShowCelebration(false)} />
      )}
    </>
  );
}

/**
 * Floating Button zum manuellen Starten der Tour
 * (optional, wenn User Tour wiederholen möchte)
 */
export function OnboardingTrigger() {
  const { startTour, hasSeenTour } = useOnboarding();
  const { t } = useTranslation();

  // Zeige Button nur wenn Tour schon gesehen wurde
  if (!hasSeenTour) {
    return null;
  }

  return (
    <button
      onClick={startTour}
      className="fixed bottom-6 right-6 z-50 flex items-center gap-2 px-4 py-3 bg-primary-600 hover:bg-primary-700 text-white rounded-full shadow-lg hover:shadow-xl transition-all duration-200 group"
      title={t('onboarding.restart', 'Tour wiederholen')}
      aria-label={t('onboarding.restart', 'Tour wiederholen')}
    >
      <Sparkles className="w-5 h-5 animate-pulse" />
      <span className="hidden sm:inline font-medium">
        {t('onboarding.restart_short', 'Tour wiederholen')}
      </span>
    </button>
  );
}

/**
 * Banner für neue User die noch keine Tour gesehen haben
 * Alternative zum Auto-Start
 */
export function OnboardingBanner() {
  const { startTour, hasSeenTour, markTourAsSeen } = useOnboarding();
  const { user } = useAuth();
  const { t } = useTranslation();
  const [dismissed, setDismissed] = React.useState(false);

  if (!user || hasSeenTour || dismissed) {
    return null;
  }

  const handleDismiss = () => {
    setDismissed(true);
    // Optional: Nicht als "gesehen" markieren, nur Banner verstecken
  };

  const handleStartTour = () => {
    setDismissed(true);
    startTour();
    // Track manual tour start
    if (user) {
      trackTourStart(
        `onboarding-${user.plan || 'community'}-v1`,
        (user.plan || 'community') as any,
        user.id
      );
    }
  };

  return (
    <div className="bg-gradient-to-r from-primary-50 to-blue-50 dark:from-primary-900/20 dark:to-blue-900/20 border-b border-primary-200 dark:border-primary-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="flex-shrink-0">
              <Sparkles className="w-6 h-6 text-primary-600 dark:text-primary-400 animate-pulse" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-gray-900 dark:text-white">
                {t('onboarding.welcome_title', 'Willkommen bei Blockchain Forensics!')}
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-300">
                {t(
                  'onboarding.welcome_message',
                  'Möchtest du eine kurze Tour durch das Dashboard machen?'
                )}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleDismiss}
              className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white transition-colors"
            >
              {t('onboarding.maybe_later', 'Später')}
            </button>
            <button
              onClick={handleStartTour}
              className="px-4 py-2 text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 rounded-lg transition-colors shadow-sm"
            >
              {t('onboarding.start_tour', 'Tour starten')}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

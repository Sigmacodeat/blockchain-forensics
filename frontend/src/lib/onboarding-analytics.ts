/**
 * Onboarding Analytics - Track Tour Completion & User Engagement
 * 
 * Tracks:
 * - Tour starts
 * - Tour completions
 * - Tour skips
 * - Step navigation
 * - Completion rate per plan
 * 
 * Integrates with existing analytics system
 */

import { track } from './analytics';
import type { PlanId } from './features';

export interface OnboardingAnalyticsEvent {
  event_type: 'tour_start' | 'tour_complete' | 'tour_skip' | 'step_view' | 'step_back' | 'step_next';
  tour_id: string;
  plan: PlanId;
  user_id?: string;
  step_number?: number;
  total_steps?: number;
  timestamp: string;
  completion_percentage?: number;
}

export interface TourCompletionStats {
  total_starts: number;
  total_completions: number;
  total_skips: number;
  completion_rate: number;
  average_steps_completed: number;
  by_plan: Record<PlanId, {
    starts: number;
    completions: number;
    skips: number;
    completion_rate: number;
  }>;
}

/**
 * Track tour start
 */
export function trackTourStart(tourId: string, plan: PlanId, userId?: string) {
  const event: OnboardingAnalyticsEvent = {
    event_type: 'tour_start',
    tour_id: tourId,
    plan,
    user_id: userId,
    timestamp: new Date().toISOString(),
  };

  // Use existing analytics infrastructure
  track('onboarding_tour_start', {
    tour_id: tourId,
    plan,
    user_id: userId,
  });

  // Store in localStorage for local analytics
  storeLocalEvent(event);

  console.log('[Onboarding Analytics] Tour started:', { tourId, plan });
}

/**
 * Track tour completion
 */
export function trackTourComplete(tourId: string, plan: PlanId, userId?: string, totalSteps?: number) {
  const event: OnboardingAnalyticsEvent = {
    event_type: 'tour_complete',
    tour_id: tourId,
    plan,
    user_id: userId,
    total_steps: totalSteps,
    completion_percentage: 100,
    timestamp: new Date().toISOString(),
  };

  track('onboarding_tour_complete', {
    tour_id: tourId,
    plan,
    user_id: userId,
    total_steps: totalSteps,
  });

  storeLocalEvent(event);

  console.log('[Onboarding Analytics] Tour completed:', { tourId, plan, totalSteps });
}

/**
 * Track tour skip
 */
export function trackTourSkip(
  tourId: string,
  plan: PlanId,
  userId?: string,
  stepNumber?: number,
  totalSteps?: number
) {
  const completionPercentage = stepNumber && totalSteps
    ? Math.round((stepNumber / totalSteps) * 100)
    : 0;

  const event: OnboardingAnalyticsEvent = {
    event_type: 'tour_skip',
    tour_id: tourId,
    plan,
    user_id: userId,
    step_number: stepNumber,
    total_steps: totalSteps,
    completion_percentage: completionPercentage,
    timestamp: new Date().toISOString(),
  };

  track('onboarding_tour_skip', {
    tour_id: tourId,
    plan,
    user_id: userId,
    step_number: stepNumber,
    total_steps: totalSteps,
    completion_percentage: completionPercentage,
  });

  storeLocalEvent(event);

  console.log('[Onboarding Analytics] Tour skipped:', {
    tourId,
    plan,
    stepNumber,
    completionPercentage: `${completionPercentage}%`,
  });
}

/**
 * Track step navigation
 */
export function trackStepView(
  tourId: string,
  plan: PlanId,
  stepNumber: number,
  totalSteps: number,
  userId?: string
) {
  const event: OnboardingAnalyticsEvent = {
    event_type: 'step_view',
    tour_id: tourId,
    plan,
    user_id: userId,
    step_number: stepNumber,
    total_steps: totalSteps,
    completion_percentage: Math.round((stepNumber / totalSteps) * 100),
    timestamp: new Date().toISOString(),
  };

  track('onboarding_step_view', {
    tour_id: tourId,
    plan,
    step_number: stepNumber,
    total_steps: totalSteps,
  });

  storeLocalEvent(event);
}

/**
 * Get completion stats from localStorage
 */
export function getCompletionStats(): TourCompletionStats {
  try {
    const eventsJson = localStorage.getItem('onboarding_analytics_events');
    if (!eventsJson) {
      return getEmptyStats();
    }

    const events: OnboardingAnalyticsEvent[] = JSON.parse(eventsJson);

    // Calculate overall stats
    const starts = events.filter((e) => e.event_type === 'tour_start').length;
    const completions = events.filter((e) => e.event_type === 'tour_complete').length;
    const skips = events.filter((e) => e.event_type === 'tour_skip').length;

    // Calculate by plan
    const byPlan: Record<string, { starts: number; completions: number; skips: number; completion_rate: number }> = {};
    
    const plans = new Set(events.map((e) => e.plan));
    for (const plan of plans) {
      const planEvents = events.filter((e) => e.plan === plan);
      const planStarts = planEvents.filter((e) => e.event_type === 'tour_start').length;
      const planCompletions = planEvents.filter((e) => e.event_type === 'tour_complete').length;
      const planSkips = planEvents.filter((e) => e.event_type === 'tour_skip').length;

      byPlan[plan] = {
        starts: planStarts,
        completions: planCompletions,
        skips: planSkips,
        completion_rate: planStarts > 0 ? (planCompletions / planStarts) * 100 : 0,
      };
    }

    // Calculate average steps completed
    const skipEvents = events.filter((e) => e.event_type === 'tour_skip');
    const averageStepsCompleted = skipEvents.length > 0
      ? skipEvents.reduce((sum, e) => sum + (e.step_number || 0), 0) / skipEvents.length
      : 0;

    return {
      total_starts: starts,
      total_completions: completions,
      total_skips: skips,
      completion_rate: starts > 0 ? (completions / starts) * 100 : 0,
      average_steps_completed: averageStepsCompleted,
      by_plan: byPlan as Record<PlanId, any>,
    };
  } catch (error) {
    console.error('[Onboarding Analytics] Failed to get stats:', error);
    return getEmptyStats();
  }
}

/**
 * Clear analytics data (for testing/reset)
 */
export function clearAnalyticsData() {
  localStorage.removeItem('onboarding_analytics_events');
  console.log('[Onboarding Analytics] Analytics data cleared');
}

/**
 * Export analytics data (for admin dashboard)
 */
export function exportAnalyticsData(): OnboardingAnalyticsEvent[] {
  try {
    const eventsJson = localStorage.getItem('onboarding_analytics_events');
    return eventsJson ? JSON.parse(eventsJson) : [];
  } catch (error) {
    console.error('[Onboarding Analytics] Failed to export data:', error);
    return [];
  }
}

// Private helper functions

function storeLocalEvent(event: OnboardingAnalyticsEvent) {
  try {
    const existing = localStorage.getItem('onboarding_analytics_events');
    const events: OnboardingAnalyticsEvent[] = existing ? JSON.parse(existing) : [];
    
    events.push(event);
    
    // Keep only last 1000 events (prevent localStorage overflow)
    if (events.length > 1000) {
      events.shift();
    }
    
    localStorage.setItem('onboarding_analytics_events', JSON.stringify(events));
  } catch (error) {
    console.error('[Onboarding Analytics] Failed to store event:', error);
  }
}

function getEmptyStats(): TourCompletionStats {
  return {
    total_starts: 0,
    total_completions: 0,
    total_skips: 0,
    completion_rate: 0,
    average_steps_completed: 0,
    by_plan: {} as Record<PlanId, any>,
  };
}

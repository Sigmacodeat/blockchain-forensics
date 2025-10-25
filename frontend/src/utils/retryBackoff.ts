/**
 * Retry Backoff Utility
 * 
 * Handles HTTP 429 Rate Limiting with Retry-After Header
 */

export interface RetryBackoffState {
  isLimited: boolean;
  retryAfter: number | null; // seconds
  retryAt: Date | null;
  remainingSeconds: number;
}

export class RetryBackoffManager {
  private retryAt: Date | null = null;
  private intervalId: NodeJS.Timeout | null = null;
  private callbacks: Set<(state: RetryBackoffState) => void> = new Set();

  /**
   * Set rate limit from Retry-After header (in seconds)
   */
  setRateLimit(retryAfterSeconds: number) {
    this.retryAt = new Date(Date.now() + retryAfterSeconds * 1000);
    this.startCountdown();
    this.notify();
  }

  /**
   * Check if currently rate limited
   */
  isRateLimited(): boolean {
    if (!this.retryAt) return false;
    const now = new Date();
    if (now >= this.retryAt) {
      this.clear();
      return false;
    }
    return true;
  }

  /**
   * Get remaining seconds until retry allowed
   */
  getRemainingSeconds(): number {
    if (!this.retryAt) return 0;
    const now = new Date();
    const diff = this.retryAt.getTime() - now.getTime();
    return Math.max(0, Math.ceil(diff / 1000));
  }

  /**
   * Get current state
   */
  getState(): RetryBackoffState {
    const remaining = this.getRemainingSeconds();
    return {
      isLimited: this.isRateLimited(),
      retryAfter: remaining > 0 ? remaining : null,
      retryAt: this.retryAt,
      remainingSeconds: remaining,
    };
  }

  /**
   * Subscribe to state changes
   */
  subscribe(callback: (state: RetryBackoffState) => void): () => void {
    this.callbacks.add(callback);
    // Immediately notify with current state
    callback(this.getState());
    
    return () => {
      this.callbacks.delete(callback);
    };
  }

  /**
   * Clear rate limit
   */
  clear() {
    this.retryAt = null;
    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = null;
    }
    this.notify();
  }

  private startCountdown() {
    if (this.intervalId) {
      clearInterval(this.intervalId);
    }
    
    this.intervalId = setInterval(() => {
      if (!this.isRateLimited()) {
        this.clear();
      } else {
        this.notify();
      }
    }, 1000);
  }

  private notify() {
    const state = this.getState();
    this.callbacks.forEach(cb => cb(state));
  }

  /**
   * Handle fetch response - automatically detect 429
   */
  static async handleResponse(response: Response): Promise<Response> {
    if (response.status === 429) {
      const retryAfter = response.headers.get('Retry-After');
      if (retryAfter) {
        const seconds = parseInt(retryAfter, 10);
        if (!isNaN(seconds)) {
          throw new RateLimitError(seconds);
        }
      }
      throw new RateLimitError(60); // Default to 60s
    }
    return response;
  }
}

/**
 * Rate Limit Error
 */
export class RateLimitError extends Error {
  constructor(public retryAfter: number) {
    super(`Rate limited. Retry after ${retryAfter} seconds.`);
    this.name = 'RateLimitError';
  }
}

/**
 * Global singleton instance
 */
export const globalBackoffManager = new RetryBackoffManager();

/**
 * React Hook for retry backoff
 */
import { useState, useEffect } from 'react';

export function useRetryBackoff(manager: RetryBackoffManager = globalBackoffManager) {
  const [state, setState] = useState<RetryBackoffState>(manager.getState());

  useEffect(() => {
    const unsubscribe = manager.subscribe(setState);
    return unsubscribe;
  }, [manager]);

  return state;
}

/**
 * Format remaining time for display
 */
export function formatRetryTime(seconds: number): string {
  if (seconds < 60) {
    return `${seconds}s`;
  }
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}m ${secs}s`;
}

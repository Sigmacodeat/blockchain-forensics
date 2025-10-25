import { renderHook, waitFor } from '@testing-library/react';
import { useRiskStream } from '../useRiskStream';
import { describe, it, expect, beforeEach, vi } from 'vitest';

// Mock EventSource
type EventHandler = (event: Event | MessageEvent) => void;

class MockEventSource {
  url: string;
  listeners: Record<string, EventHandler[]> = {};
  onopen: EventHandler | null = null;
  onerror: EventHandler | null = null;
  readyState = 0;

  constructor(url: string) {
    this.url = url;
    // Expose latest instance for tests
    (global as any).__es = this;
    setTimeout(() => {
      this.readyState = 1;
      if (this.onopen) this.onopen({} as Event);
    }, 0);
  }

  addEventListener(event: string, handler: EventHandler) {
    if (!this.listeners[event]) this.listeners[event] = [];
    this.listeners[event].push(handler);
  }

  removeEventListener(event: string, handler: EventHandler) {
    if (this.listeners[event]) {
      this.listeners[event] = this.listeners[event].filter((h) => h !== handler);
    }
  }

  close() {
    this.readyState = 2;
  }

  // Helper to simulate events
  _emit(event: string, data: any) {
    if (this.listeners[event]) {
      this.listeners[event].forEach((handler) =>
        handler({ data: JSON.stringify(data) } as MessageEvent)
      );
    }
  }
}

// Replace global EventSource
(global as any).EventSource = MockEventSource;

describe('useRiskStream', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should initialize with default state', () => {
    const { result } = renderHook(() =>
      useRiskStream('ethereum', '0xabc', { autoStart: false })
    );

    expect(result.current.connected).toBe(false);
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBeNull();
    expect(result.current.score).toBeNull();
  });

  it('should connect and emit ready event', async () => {
    const { result } = renderHook(() =>
      useRiskStream('ethereum', '0xabc', { autoStart: true })
    );

    // Wait a bit for async operations
    await waitFor(() => {
      expect(result.current.connected).toBe(false);
    });

    // Simulate ready event
    const es = (global as any).__es as MockEventSource | undefined;
    if (es) {
      es._emit('risk.ready', { ok: true });
    }

    await waitFor(() => {
      expect(result.current.connected).toBe(true);
    });
  });

  it('should handle risk.result event', async () => {
    const { result } = renderHook(() =>
      useRiskStream('ethereum', '0xabc', { autoStart: true })
    );

    const mockResult = {
      type: 'risk.result',
      payload: {
        chain: 'ethereum',
        address: '0xabc',
        score: 0.75,
        categories: ['mixer'],
        reasons: ['High risk'],
        factors: { taint: 0.8 },
      }
    };

    // Simulate result event
    const es = (global as any).__es as MockEventSource | undefined;
    if (es) {
      es._emit('risk.result', mockResult);
    }

    await waitFor(() => {
      expect(result.current.score).toBe(0.75);
      expect(result.current.categories).toEqual(['mixer']);
      expect(result.current.loading).toBe(false);
    });
  });

  it('should handle risk.error event', async () => {
    const { result } = renderHook(() =>
      useRiskStream('ethereum', 'invalid', { autoStart: true })
    );

    // Simulate error event
    const es = (global as any).__es as MockEventSource | undefined;
    if (es) {
      es._emit('risk.error', { detail: 'invalid_address' });
    }

    await waitFor(() => {
      expect(result.current.error).toBe('invalid_address');
      expect(result.current.loading).toBe(false);
    });
  });

  it('should cleanup on unmount', () => {
    const { unmount } = renderHook(() =>
      useRiskStream('ethereum', '0xabc', { autoStart: true })
    );

    const es = (global as any).__es as MockEventSource;
    const closeSpy = vi.spyOn(es, 'close');

    unmount();

    expect(closeSpy).toHaveBeenCalled();
  });

  it('should handle typing event', async () => {
    const { result } = renderHook(() =>
      useRiskStream('ethereum', '0xabc', { autoStart: true })
    );

    const es = (global as any).__es as MockEventSource | undefined;
    if (es) {
      es._emit('risk.typing', { ok: true });
    }

    await waitFor(() => {
      expect(result.current.loading).toBe(true);
    });
  });
});
